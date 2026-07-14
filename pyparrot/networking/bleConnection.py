"""
bleConnection.py  (Windows/Mac/Linux compatible version -- FIXED)

Drop-in replacement for pyparrot's pyparrot/networking/bleConnection.py,
built on bleak instead of bluepy.

FIXES in this version (vs. the previous bleak port):

  FIX 1 (the landing bug): in bleak >= 0.19, notification callbacks receive
         a BleakGATTCharacteristic OBJECT as `sender`, not a UUID string.
         str(sender) looks like:
             "9a66fb0e-...-cb8e (Handle: 187): Unknown"
         which never matched the UUID keys in uuid_to_channel, so EVERY
         notification hit the "unknown channel" branch. Result: no ACKs, no
         sensor updates, flying_state never changed, and safe_land() had
         nothing to key off of. We now read sender.uuid.

  FIX 2: _safe_ble_write() used to loop FOREVER on write failure, which
         could hang the landing loop with the drone still in the air. It is
         now bounded and returns True/False.

  FIX 3: _reconnect() re-authenticates the handshake but never re-subscribed
         to the four receive characteristics, so after any mid-flight
         reconnect you'd lose ACKs/sensors even with FIX 1. It now re-runs
         start_notify() on all receive channels.

  FIX 4 (the deadlock exposed by FIX 1): bleak runs notification callbacks
         on its event-loop thread. pyparrot reacts to ACK_DRONE_DATA by
         writing an ack packet back to the drone; a blocking BLE write from
         the loop thread deadlocks the loop and every write times out with
         an empty "()" error. Notifications are now queued and dispatched
         into pyparrot from a dedicated worker thread, and
         _BleakEventLoopThread.run() refuses (loudly) to be called from the
         loop thread so this class of bug can't silently return.

INSTALL:
    pip install bleak

USAGE: same as before -- copy over pyparrot/networking/bleConnection.py.
"""

import asyncio
import queue
import struct
import threading
import time
from datetime import datetime

from bleak import BleakClient, BleakScanner
from pyparrot.utils.colorPrint import color_print
from pyparrot.commandsandsensors.DroneSensorParser import get_data_format_and_size


class _BleakEventLoopThread:
    """
    Runs a single asyncio event loop forever in a background daemon thread,
    so synchronous pyparrot code can call bleak's async API and block for
    the result, the same way it used to block on bluepy calls.
    """
    _loop = None
    _thread = None
    _lock = threading.Lock()

    @classmethod
    def get_loop(cls):
        with cls._lock:
            if cls._loop is None:
                cls._loop = asyncio.new_event_loop()
                cls._thread = threading.Thread(target=cls._loop.run_forever, daemon=True)
                cls._thread.start()
            return cls._loop

    @classmethod
    def run(cls, coro, timeout=None):
        loop = cls.get_loop()
        # FIX 4 (guard): calling future.result() FROM the event-loop thread
        # deadlocks the loop (the coroutine can never be scheduled while we
        # block). This happened when bleak notification callbacks (which run
        # on the loop thread) triggered pyparrot's ack_packet() -> BLE write.
        # Fail loudly instead of freezing for the timeout duration.
        if threading.current_thread() is cls._thread:
            raise RuntimeError(
                "BLE call attempted from the event-loop thread itself; "
                "this would deadlock. Dispatch to a worker thread instead."
            )
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout)


class MinidroneNotifyHandler:
    """
    Equivalent of the original bluepy MinidroneDelegate, adapted to bleak's
    notification callback style: callback(sender, data).

    FIX 4 (the deadlock): bleak invokes this callback ON the background
    event-loop thread. pyparrot's update_sensors() reacts to ACK_DRONE_DATA
    by sending an ack packet back to the drone -- i.e. a BLE write -- and a
    blocking BLE write from the event-loop thread deadlocks the loop (it
    waits on a coroutine that can only run on the thread that's waiting).
    That's what produced the silent 5-second "BLE write failed on attempt 1 ()"
    TimeoutErrors as soon as sensor notifications started flowing.

    So the callback itself now does the bare minimum -- copy the data and put
    it on a queue -- and a dedicated worker thread does the actual dispatch
    into pyparrot. A single ordered worker preserves packet ordering, which
    matters for the sequence-number logic in update_sensors().
    """
    def __init__(self, uuid_to_channel, minidrone, ble_connection):
        self.uuid_to_channel = uuid_to_channel
        self.minidrone = minidrone
        self.ble_connection = ble_connection
        self._queue = queue.Queue()
        self._worker = threading.Thread(target=self._process_forever, daemon=True)
        self._worker.start()

    def __call__(self, sender, data):
        # Runs on the bleak event-loop thread: do NOTHING blocking here.
        # FIX 1: bleak >= 0.19 passes a BleakGATTCharacteristic object whose
        # str() is "uuid (Handle: N): Description"; use .uuid when present.
        uuid = getattr(sender, "uuid", sender)
        self._queue.put((str(uuid).lower(), bytes(data)))

    def _process_forever(self):
        # Runs on its own thread, so BLE writes triggered from here (like
        # pyparrot's ack_packet) block safely without freezing the loop.
        while True:
            sender_key, data = self._queue.get()
            try:
                self._dispatch(sender_key, data)
            except Exception as e:
                color_print("error handling notification from %s: %r" % (sender_key, e), "ERROR")

    def _dispatch(self, sender_key, data):
        channel = self.uuid_to_channel.get(sender_key)

        if channel is None:
            color_print("unknown channel for sender %s" % sender_key, "ERROR")
            return

        (packet_type, packet_seq_num) = struct.unpack('<BB', data[0:2])
        raw_data = data[2:]

        if channel == 'ACK_DRONE_DATA':
            self.minidrone.update_sensors(packet_type, None, packet_seq_num, raw_data, ack=True)
        elif channel == 'NO_ACK_DRONE_DATA':
            self.minidrone.update_sensors(packet_type, None, packet_seq_num, raw_data, ack=False)
        elif channel == 'ACK_COMMAND_SENT':
            self.ble_connection._set_command_received('SEND_WITH_ACK', True)
        elif channel == 'ACK_HIGH_PRIORITY':
            self.ble_connection._set_command_received('SEND_HIGH_PRIORITY', True)
        else:
            color_print("unknown channel %s sending data" % channel, "ERROR")


class BLEConnection:
    """
    Same public interface as the original bluepy-based BLEConnection class,
    reimplemented on top of bleak so it runs on Windows, macOS, and Linux.
    """

    def __init__(self, address, minidrone):
        """
        :param address: BLE address for the minidrone (see scan_for_minidrones())
        :param minidrone: the Minidrone object for this drone (used for sensor callbacks)
        """
        self.address = address
        self.minidrone = minidrone
        self.client = None  # bleak.BleakClient, created in connect()

        self.service_uuids = {
            'fa00': 'ARCOMMAND_SENDING_SERVICE',
            'fb00': 'ARCOMMAND_RECEIVING_SERVICE',
            'fc00': 'PERFORMANCE_COUNTER_SERVICE',
            'fd21': 'NORMAL_BLE_FTP_SERVICE',
            'fd51': 'UPDATE_BLE_FTP',
            'fe00': 'UPDATE_RFCOMM_SERVICE',
            '1800': 'Device Info',
            '1801': 'unknown',
        }

        self.characteristic_send_uuids = {
            '0a': 'SEND_NO_ACK',
            '0b': 'SEND_WITH_ACK',
            '0c': 'SEND_HIGH_PRIORITY',
            '1e': 'ACK_COMMAND'
        }

        self.characteristic_send_counter = {
            'SEND_NO_ACK': 0,
            'SEND_WITH_ACK': 0,
            'SEND_HIGH_PRIORITY': 0,
            'ACK_COMMAND': 0,
            'RECEIVE_WITH_ACK': 0
        }

        self.characteristic_receive_uuids = {
            '0e': 'ACK_DRONE_DATA',
            '0f': 'NO_ACK_DRONE_DATA',
            '1b': 'ACK_COMMAND_SENT',
            '1c': 'ACK_HIGH_PRIORITY',
        }

        self.characteristic_ftp_uuids = {
            '22': 'NORMAL_FTP_TRANSFERRING',
            '23': 'NORMAL_FTP_GETTING',
            '24': 'NORMAL_FTP_HANDLING',
            '52': 'UPDATE_FTP_TRANSFERRING',
            '53': 'UPDATE_FTP_GETTING',
            '54': 'UPDATE_FTP_HANDLING',
        }

        self.ftp_commands = {
            "list": "LIS",
            "get": "GET"
        }

        self.services = None
        self.send_characteristics = dict()       # channel name -> characteristic uuid (str)
        self.receive_characteristics = dict()    # channel name -> characteristic uuid (str)
        self.handshake_characteristics = dict()  # short hex id -> characteristic uuid (str)
        self.ftp_characteristics = dict()

        # reverse lookup used by the notification handler
        self.uuid_to_receive_channel = dict()

        # kept so _reconnect() can re-subscribe with the same handler (FIX 3)
        self._notify_handler = None

        self.data_types = {
            'ACK': 1,
            'DATA_NO_ACK': 2,
            'LOW_LATENCY_DATA': 3,
            'DATA_WITH_ACK': 4
        }

        self.command_received = {
            'SEND_WITH_ACK': False,
            'SEND_HIGH_PRIORITY': False,
            'ACK_COMMAND': False
        }

        self.command_tuple_cache = dict()
        self.sensor_tuple_cache = dict()

        self.max_packet_retries = 3

    # ---------------------------------------------------------------
    # connection management
    # ---------------------------------------------------------------

    def connect(self, num_retries):
        """
        Connects to the drone and re-tries in case of failure the specified number of times.
        :param num_retries: number of times to retry
        :return: True if it succeeds, False otherwise
        """
        import traceback
        try_num = 1
        connected = False
        while try_num < num_retries and not connected:
            try:
                self._connect()
                connected = True
            except Exception as e:
                color_print("retrying connections (%r)" % e, "INFO")
                traceback.print_exc()
                try_num += 1
        return connected

    def _reconnect(self, num_retries):
        async def _resolve_and_connect():
            device = await BleakScanner.find_device_by_address(self.address, timeout=10.0)
            if device is None:
                raise RuntimeError("Could not find BLE device %s during scan" % self.address)
            client = BleakClient(device, address_type="random", timeout=20.0)
            await client.connect()
            return client

        try_num = 1
        success = False
        while try_num < num_retries and not success:
            try:
                color_print("trying to re-connect to the minidrone at address %s" % self.address, "WARN")
                self.client = _BleakEventLoopThread.run(_resolve_and_connect(), timeout=40)
                color_print("connected!  Asking for services and characteristics", "SUCCESS")
                success = True
            except Exception as e:
                color_print("retrying connections (%r)" % e, "WARN")
                try_num += 1

        if success:
            self._perform_handshake()

            # ----------------------------------------------------------
            # FIX 3: re-subscribe to the receive characteristics after a
            # reconnect. The old code only redid the handshake, so ACKs
            # and sensor data were silently lost after any reconnect.
            # ----------------------------------------------------------
            if self._notify_handler is not None:
                for channel_uuid in self.receive_characteristics.values():
                    try:
                        _BleakEventLoopThread.run(
                            self.client.start_notify(channel_uuid, self._notify_handler),
                            timeout=10
                        )
                    except Exception as e:
                        color_print("re-subscribe failed for %s: %s" % (channel_uuid, e), "WARN")

        return success

    def _connect(self):
        """
        Connect to the minidrone, discover services/characteristics, do the
        handshake, and subscribe to notifications. Raises on failure.
        """
        color_print("trying to connect to the minidrone at address %s" % self.address, "INFO")

        async def _resolve_and_connect():
            # Resolving the device via the scanner first (rather than
            # connecting from a bare address string) is the pattern bleak's
            # WinRT backend expects, and lets us reliably request a "random"
            # address type -- Parrot minidrones use a random static BLE
            # address (bluepy's original code connected with
            # self.drone_connection.connect(self.address, "random")). If
            # Windows assumes "public" instead, BLE connect can hang
            # indefinitely rather than failing, which is what caused the
            # earlier TimeoutError with no useful message.
            device = await BleakScanner.find_device_by_address(self.address, timeout=10.0)
            if device is None:
                raise RuntimeError(
                    "Could not find BLE device %s during scan. Make sure the "
                    "Mambo is powered on, nearby, and not already connected "
                    "to another app/device." % self.address
                )
            client = BleakClient(
                device,
                address_type="random",
                timeout=45.0,
                winrt=dict(use_cached_services=False),
            )
            await client.connect()
            return client

        self.client = _BleakEventLoopThread.run(_resolve_and_connect(), timeout=60)
        color_print("connected!  Asking for services and characteristics", "SUCCESS")

        all_services_found = False

        while not all_services_found:
            services = self.client.services

            for s in services:
                hex_str = self._get_byte_str_from_uuid(s.uuid, 3, 4)
                if hex_str not in self.service_uuids:
                    continue
                service_name = self.service_uuids[hex_str]

                if service_name == 'ARCOMMAND_RECEIVING_SERVICE':
                    for c in s.characteristics:
                        c_hex = self._get_byte_str_from_uuid(c.uuid, 4, 4)
                        if c_hex in self.characteristic_receive_uuids:
                            channel = self.characteristic_receive_uuids[c_hex]
                            self.receive_characteristics[channel] = c.uuid
                            self.uuid_to_receive_channel[c.uuid.lower()] = channel

                elif service_name == 'ARCOMMAND_SENDING_SERVICE':
                    for c in s.characteristics:
                        c_hex = self._get_byte_str_from_uuid(c.uuid, 4, 4)
                        if c_hex in self.characteristic_send_uuids:
                            self.send_characteristics[self.characteristic_send_uuids[c_hex]] = c.uuid

                elif service_name in ('UPDATE_BLE_FTP', 'NORMAL_BLE_FTP_SERVICE'):
                    for c in s.characteristics:
                        c_hex = self._get_byte_str_from_uuid(c.uuid, 4, 4)
                        if c_hex in self.characteristic_ftp_uuids:
                            self.ftp_characteristics[self.characteristic_ftp_uuids[c_hex]] = c.uuid

                # handshake characteristics: original code wrote 0x0100 to the
                # CCCD by hand. bleak's start_notify() does that write for us,
                # so here we just remember which characteristics need it.
                for c in s.characteristics:
                    full_hex = self._get_byte_str_from_uuid(c.uuid, 3, 4)
                    if full_hex in ['fb0f', 'fb0e', 'fb1b', 'fb1c', 'fd22', 'fd23',
                                     'fd24', 'fd52', 'fd53', 'fd54']:
                        self.handshake_characteristics[full_hex] = c.uuid

            all_services_found = True
            for r_id in self.characteristic_receive_uuids.values():
                if r_id not in self.receive_characteristics:
                    color_print("setting to false in receive on %s" % r_id)
                    all_services_found = False

            for s_id in self.characteristic_send_uuids.values():
                if s_id not in self.send_characteristics:
                    color_print("setting to false in send")
                    all_services_found = False

            for f_id in self.characteristic_ftp_uuids.values():
                if f_id not in self.ftp_characteristics:
                    color_print("setting to false in ftp")
                    all_services_found = False

            if len(self.handshake_characteristics.keys()) != 10:
                color_print("setting to false in len")
                all_services_found = False

        self._perform_handshake()

        # subscribe to notifications on the drone-data / ack receive channels
        self._notify_handler = MinidroneNotifyHandler(
            self.uuid_to_receive_channel, self.minidrone, self)
        for channel_uuid in self.receive_characteristics.values():
            _BleakEventLoopThread.run(
                self.client.start_notify(channel_uuid, self._notify_handler),
                timeout=10
            )

    def _perform_handshake(self):
        """
        "Magic handshake" -- subscribe (enable notifications) on every
        handshake characteristic. bleak's start_notify() writes the 0x0001
        CCCD value under the hood, which is what the original bluepy code
        did manually with writeCharacteristic(handle+2, b'\\x01\\x00').

        Note: on Windows, fd24/fd54 (FTP "handling" channels) report that
        they don't support notifications; that warning is harmless for
        flight -- those channels are only used for media/FTP transfers.
        """
        color_print("magic handshake to make the drone listen to our commands")
        for uuid in self.handshake_characteristics.values():
            if uuid in self.receive_characteristics.values():
                continue  # already subscribed above
            try:
                _BleakEventLoopThread.run(
                    self.client.start_notify(uuid, lambda sender, data: None),
                    timeout=10
                )
            except Exception as e:
                color_print("handshake notify failed for %s: %s" % (uuid, e), "WARN")

    def disconnect(self):
        """
        Disconnect the BLE connection. Always call this at the end of your
        programs to cleanly disconnect.
        """
        if self.client is not None:
            try:
                _BleakEventLoopThread.run(self.client.disconnect(), timeout=10)
            except Exception as e:
                color_print("disconnect error (ignored): %s" % e, "WARN")

    def _get_byte_str_from_uuid(self, uuid, byte_start, byte_end):
        uuid_str = format("%s" % uuid)
        idx_start = 2 * (byte_start - 1)
        idx_end = 2 * byte_end
        return uuid_str[idx_start:idx_end]

    # ---------------------------------------------------------------
    # sending commands (packet formats are unchanged from the original)
    # ---------------------------------------------------------------

    def send_turn_command(self, command_tuple, degrees):
        self.characteristic_send_counter['SEND_WITH_ACK'] = (
            self.characteristic_send_counter['SEND_WITH_ACK'] + 1) % 256
        packet = struct.pack("<BBBBHh", self.data_types['DATA_WITH_ACK'],
                              self.characteristic_send_counter['SEND_WITH_ACK'],
                              command_tuple[0], command_tuple[1], command_tuple[2],
                              degrees)
        return self.send_command_packet_ack(packet)

    def send_auto_takeoff_command(self, command_tuple):
        self.characteristic_send_counter['SEND_WITH_ACK'] = (
            self.characteristic_send_counter['SEND_WITH_ACK'] + 1) % 256
        packet = struct.pack("<BBBBHB", self.data_types['DATA_WITH_ACK'],
                              self.characteristic_send_counter['SEND_WITH_ACK'],
                              command_tuple[0], command_tuple[1], command_tuple[2],
                              1)
        return self.send_command_packet_ack(packet)

    def send_command_packet_ack(self, packet):
        try_num = 0
        self._set_command_received('SEND_WITH_ACK', False)
        while try_num < self.max_packet_retries and not self.command_received['SEND_WITH_ACK']:
            color_print("sending command packet on try %d" % try_num, 2)
            self._safe_ble_write(characteristic=self.send_characteristics['SEND_WITH_ACK'], packet=packet)
            try_num += 1
            color_print("sleeping for a notification", 2)
            self.smart_sleep(0.5)
        return self.command_received['SEND_WITH_ACK']

    def send_single_pcmd_command(self, command_tuple, roll, pitch, yaw, vertical_movement):
        self.characteristic_send_counter['SEND_NO_ACK'] = (
            self.characteristic_send_counter['SEND_NO_ACK'] + 1) % 256
        packet = struct.pack("<BBBBHBbbbbI", self.data_types['DATA_NO_ACK'],
                              self.characteristic_send_counter['SEND_NO_ACK'],
                              command_tuple[0], command_tuple[1], command_tuple[2],
                              1, int(roll), int(pitch), int(yaw), int(vertical_movement), 0)
        self._safe_ble_write(characteristic=self.send_characteristics['SEND_NO_ACK'], packet=packet)

    def send_pcmd_command(self, command_tuple, roll, pitch, yaw, vertical_movement, duration):
        start_time = time.time()
        while time.time() - start_time < duration:
            self.send_single_pcmd_command(command_tuple, roll, pitch, yaw, vertical_movement)
            self.smart_sleep(0.1)

    def send_noparam_command_packet_ack(self, command_tuple):
        self.characteristic_send_counter['SEND_WITH_ACK'] = (
            self.characteristic_send_counter['SEND_WITH_ACK'] + 1) % 256
        packet = struct.pack("<BBBBH", self.data_types['DATA_WITH_ACK'],
                              self.characteristic_send_counter['SEND_WITH_ACK'],
                              command_tuple[0], command_tuple[1], command_tuple[2])
        return self.send_command_packet_ack(packet)

    def send_enum_command_packet_ack(self, command_tuple, enum_value, usb_id=None):
        self.characteristic_send_counter['SEND_WITH_ACK'] = (
            self.characteristic_send_counter['SEND_WITH_ACK'] + 1) % 256
        if usb_id is None:
            packet = struct.pack("<BBBBBBI", self.data_types['DATA_WITH_ACK'],
                                  self.characteristic_send_counter['SEND_WITH_ACK'],
                                  command_tuple[0], command_tuple[1], command_tuple[2], 0,
                                  enum_value)
        else:
            packet = struct.pack("<BBBBHBI", self.data_types['DATA_WITH_ACK'],
                                  self.characteristic_send_counter['SEND_WITH_ACK'],
                                  command_tuple[0], command_tuple[1], command_tuple[2],
                                  usb_id, enum_value)
        return self.send_command_packet_ack(packet)

    def send_param_command_packet(self, command_tuple, param_tuple=None, param_type_tuple=0, ack=True):
        param_size_list = [0] * len(param_tuple)
        pack_char_list = [0] * len(param_tuple)

        if param_tuple is not None:
            for i, param in enumerate(param_tuple):
                pack_char_list[i], param_size_list[i] = get_data_format_and_size(param, param_type_tuple[i])

        if ack:
            ack_string = 'SEND_WITH_ACK'
            data_ack_string = 'DATA_WITH_ACK'
        else:
            ack_string = 'SEND_NO_ACK'
            data_ack_string = 'DATA_NO_ACK'

        self.characteristic_send_counter['SEND_WITH_ACK'] = (
            self.characteristic_send_counter['SEND_WITH_ACK'] + 1) % 256

        packet = struct.pack("<BBBBH", self.data_types[data_ack_string],
                              self.characteristic_send_counter[ack_string],
                              command_tuple[0], command_tuple[1], command_tuple[2])

        if param_tuple is not None:
            for i, param in enumerate(param_tuple):
                packet += struct.pack(pack_char_list[i], param)

        return self.send_command_packet_ack(packet)

    def _set_command_received(self, channel, val):
        self.command_received[channel] = val

    def _safe_ble_write(self, characteristic, packet):
        """
        FIX 2: bounded retries instead of an infinite loop. The old
        `while not success:` version could hang forever mid-landing if BLE
        writes started failing and reconnects kept failing too -- meaning
        disconnect() was never reached and the drone's link-loss auto-land
        never triggered. Now: try the write, on failure reconnect and retry,
        give up after max_packet_retries attempts and return False.
        """
        for attempt in range(self.max_packet_retries):
            try:
                _BleakEventLoopThread.run(
                    self.client.write_gatt_char(characteristic, packet, response=False),
                    timeout=5
                )
                return True
            except Exception as e:
                color_print("BLE write failed on attempt %d (%s)" % (attempt + 1, e), "WARN")
                if attempt < self.max_packet_retries - 1:
                    if not self._reconnect(3):
                        color_print("reconnect failed, giving up on this packet", "ERROR")
                        return False
        return False

    def ack_packet(self, buffer_id, packet_id):
        self.characteristic_send_counter['ACK_COMMAND'] = (
            self.characteristic_send_counter['ACK_COMMAND'] + 1) % 256
        packet = struct.pack("<BBB", self.data_types['ACK'],
                              self.characteristic_send_counter['ACK_COMMAND'],
                              packet_id)
        self._safe_ble_write(characteristic=self.send_characteristics['ACK_COMMAND'], packet=packet)

    def smart_sleep(self, timeout):
        """
        Sleeps the requested number of seconds. bleak's notification handler
        runs on the background event-loop thread the entire time regardless
        of what the main thread is doing, so a plain chunked sleep here does
        not block notification handling.
        """
        start_time = datetime.now()
        diff = 0.0
        while diff < timeout:
            time.sleep(min(0.1, max(timeout - diff, 0)))
            new_time = datetime.now()
            diff = (new_time - start_time).seconds + ((new_time - start_time).microseconds / 1000000.0)


# ---------------------------------------------------------------------
# Scanning helper: replaces bluepy's Scanner / pyparrot's findMinidrone
# script, which was also Linux/bluepy-only.
# ---------------------------------------------------------------------

def scan_for_minidrones(timeout=5, name_filter=None):
    """
    Scan for nearby BLE devices and print any that look like Parrot
    minidrones (Mambo, Swing, etc). Returns a list of (name, address) tuples.

    :param timeout: seconds to scan for
    :param name_filter: optional substring to filter device names by
                         (defaults to common Parrot minidrone name prefixes)
    :return: list of (name, address)
    """
    prefixes = ('Mambo', 'Swing', 'Travis', 'Maclan', 'RS_')

    async def _scan():
        devices = await BleakScanner.discover(timeout=timeout)
        found = []
        for d in devices:
            name = d.name or ""
            if name_filter:
                if name_filter in name:
                    found.append((name, d.address))
            elif name.startswith(prefixes):
                found.append((name, d.address))
        return found

    results = _BleakEventLoopThread.run(_scan(), timeout=timeout + 10)
    for name, address in results:
        color_print("found minidrone: %s at address %s" % (name, address), "SUCCESS")
    return results


if __name__ == "__main__":
    # quick manual test: python bleConnection.py
    print("Scanning for nearby Parrot minidrones...")
    scan_for_minidrones()
