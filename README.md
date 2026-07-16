# Installation Guide — Parrot Mambo + Python on Windows

This guide covers **setup only**: installing Python, installing the drone
library, and finding your drone's Bluetooth address. For flying, see
[tutorial.md](tutorial.md).

---

## 1. What you need

- A Windows 10/11 laptop with **Bluetooth 4.0 or newer** (almost all laptops from 2015+)
- A Parrot Mambo with a charged battery
- Python 3.9 or newer

---

## 2. Install Python

1. Download Python from https://www.python.org/downloads/
2. Run the installer. **IMPORTANT: tick "Add python.exe to PATH"** on the
   first screen before clicking Install.
3. Verify: open **PowerShell** and run:

   ```
   python --version
   ```

   You should see something like `Python 3.12.x`. If you get
   `'python' is not recognized`, reinstall and tick the PATH checkbox.

---

## 3. Install the drone library (one command)

In PowerShell:

```
python -m pip install https://github.com/DAUST-CRAS/pyparrot_windows/archive/refs/tags/v2.0.0-windows.zip
```

This installs `pyparrot` plus everything it needs (`bleak`, `untangle`,
`zeroconf`). No Git, no compilers, no admin rights.

> **THE GOLDEN RULE:** many laptops secretly have more than one Python
> (python.org, Microsoft Store, Anaconda...). If you install packages into
> one Python and run scripts with another, you get `ModuleNotFoundError`
> even though the install "worked".
>
> The rule: **use the word `python` for everything, always.**
> - Install: `python -m pip install ...`  (never plain `pip install ...`)
> - Run: `python myscript.py`  (never `py myscript.py`)

Verify:

```
python -c "import pyparrot; print('pyparrot OK')"
```

---

## 4. Prepare Bluetooth and the drone

1. Laptop: **Settings → Bluetooth & devices → Bluetooth: On.**
   Do **NOT** "pair" the drone in Windows settings — the Python code
   connects directly, and pairing can cause problems.
2. Drone: insert a charged battery (the eyes/lights should glow).
3. **Close the Parrot FreeFlight phone app** and turn off Bluetooth on any
   phone that has connected to this drone before. A Mambo accepts only ONE
   connection at a time.

---

## 5. Find your drone's Bluetooth address

Every drone has a unique address like `D0:3A:60:8B:E6:5A`. You need it once
per drone — write it on a sticker on the drone!

With the drone powered on, run (from any folder):

```
find_mambo
```

Expected output:

```
Scanning for nearby Parrot minidrones (5 seconds)...
 found minidrone: Mambo_596940 at address D0:3A:60:8B:E6:5A
```

Copy the address exactly, including the colons. Multiple drones in the room
all appear at once — match the `Mambo_XXXXXX` name to the sticker on each
drone.

You're done — continue with [tutorial.md](tutorial.md) to fly.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `'python' is not recognized` | Reinstall Python with "Add to PATH" ticked, then close and reopen PowerShell. |
| `python` opens the Microsoft Store | Windows has a fake `python` alias. Settings → Apps → Advanced app settings → App execution aliases → turn OFF the two `python` entries, then reinstall from python.org with "Add to PATH" ticked. |
| `ModuleNotFoundError` (pyparrot, bleak, zeroconf...) | The two-Pythons problem — see the Golden Rule in section 3. Reinstall with `python -m pip install ...` and run with `python`, never `py`. To compare which Python each command uses: `python -c "import sys; print(sys.executable)"` vs `py -c "import sys; print(sys.executable)"`. |
| `AttributeError: 'project' has no attribute 'myclass'` | Old/broken install. Re-run the section 3 command with `--force-reinstall` added at the end. |
| `find_mambo` finds nothing | Battery in and charged (eyes lit)? Phone app closed / phone Bluetooth off? Laptop Bluetooth on? Drone within 1–2 meters? |
| `handshake notify failed for ...fd24 / ...fd54` when connecting | **Harmless.** Camera/file-transfer channels Windows can't subscribe to. Flight is unaffected. |
| `Connected: False` after retries | Power-cycle the drone (remove/reinsert battery), wait 10 s, retry. Make sure no phone is connected. |

---

## Credits & license

Fork of [pyparrot](https://github.com/amymcgovern/pyparrot) by Dr. Amy
McGovern (MIT License), with cross-platform BLE via
[bleak](https://github.com/hbldh/bleak). Distributed under the same
[MIT License](LICENSE). No warranty — test before class.
