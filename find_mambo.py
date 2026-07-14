"""
find_mambo.py -- find your drone's Bluetooth address

Run this with your Parrot Mambo powered ON and nearby:

    python find_mambo.py

It prints something like:

    found minidrone: Mambo_596940 at address D0:3A:60:8B:E6:5A

Copy that address into your flight script (mamboAddr = "...").

If nothing shows up:
  * Is the drone battery charged and clicked in? (eyes lit?)
  * Is the Parrot phone app closed / phone Bluetooth off?
    (the drone only accepts ONE connection at a time)
  * Is Bluetooth turned on in Windows settings?
  * Try holding the drone within 1-2 meters of the laptop.
"""

import sys

try:
    from pyparrot.networking.bleConnection import scan_for_minidrones
except ImportError:
    print("Could not import pyparrot. Run this script from the folder that")
    print("contains the 'pyparrot' folder, and make sure you installed the")
    print("requirements:  pip install bleak untangle")
    sys.exit(1)

print("Scanning for nearby Parrot minidrones (5 seconds)...")
found = scan_for_minidrones(timeout=5)

if not found:
    print()
    print("No minidrones found. Check:")
    print("  1. Drone battery is in and charged (eyes lit)")
    print("  2. No phone/app is already connected to the drone")
    print("  3. Bluetooth is ON in Windows settings")
    print("  4. Drone is within 1-2 meters of this laptop")
    print("Then run this script again.")
else:
    print()
    print("Copy the address (D0:3A:...) into your flight script:")
    for name, address in found:
        print('    mamboAddr = "%s"    # %s' % (address, name))
