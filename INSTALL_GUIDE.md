# Parrot Mambo + Python on Windows — Installation Guide

*For summer camp instructors and students (ages 15+)*

This guide gets you from a brand-new Windows laptop to flying a Parrot Mambo
drone with Python over Bluetooth (BLE). It uses a modified version of
[pyparrot](https://github.com/amymcgovern/pyparrot) (by Dr. Amy McGovern,
MIT license) that replaces the Linux-only `bluepy` Bluetooth code with
[bleak](https://github.com/hbldh/bleak), which works on Windows, macOS,
and Linux.

---

## 1. What you need

| Item | Details |
|---|---|
| A Windows laptop | Windows 10 or 11, with **Bluetooth 4.0 or newer** (almost all laptops from 2015+). A cheap USB Bluetooth 4.0+ dongle also works. |
| A Parrot Mambo | Charged battery. Works with or without the FPV camera (this guide uses BLE, not WiFi). |
| Python 3 | Version 3.9 or newer. |
| This package | The modified pyparrot with Windows BLE support. |

> **Instructor tip:** label each drone and each laptop with matching numbers
> (Drone 1 ↔ Laptop 1). Each drone has a different Bluetooth address, and
> mixed-up pairs are the #1 source of "it doesn't connect!" during camp.

---

## 2. Install Python

1. Download Python from https://www.python.org/downloads/ (big yellow button).
2. Run the installer. **IMPORTANT: tick the checkbox "Add python.exe to PATH"**
   on the first screen before clicking Install. If you forget this, nothing
   else in this guide will work from the command line.
3. To verify: open **PowerShell** (press the Windows key, type `powershell`,
   press Enter) and run:

   ```
   python --version
   ```

   You should see something like `Python 3.12.x`. If you get
   `'python' is not recognized`, reinstall and tick the PATH checkbox.

---

## 3. Install the drone software

1. Download this package (green **Code** button → **Download ZIP** on the
   GitHub page) and unzip it somewhere easy, for example:

   ```
   C:\Users\<you>\Documents\pyparrot-windows
   ```

2. Open PowerShell **in that folder**: in File Explorer, open the folder,
   click the address bar, type `powershell`, and press Enter.

3. Install the required Python packages:

   ```
   pip install bleak untangle
   ```

   - `bleak` = the cross-platform Bluetooth library
   - `untangle` = XML parser pyparrot needs for drone commands

That's it — no compilers, no drivers, no admin rights needed.

---

## 4. Turn on Bluetooth and prepare the drone

1. On the laptop: **Settings → Bluetooth & devices → Bluetooth: On.**
   Do **NOT** "pair" the drone in Windows settings — the Python code
   connects directly. Pairing in Windows can actually cause problems.
2. On the drone: install a charged battery. The eyes/lights should glow.
3. **Close the Parrot FreeFlight phone app** and turn off Bluetooth on any
   phone that has connected to this drone before. A Mambo only accepts ONE
   connection at a time — if a phone grabs it first, Python cannot connect.

---

## 5. Find your drone's Bluetooth address

Every drone has a unique address that looks like `D0:3A:60:8B:E6:5A`.
You need it once per drone — write it on a sticker on the drone!

With the drone powered on, run the scanner from the package folder:

```
python find_mambo.py
```

Expected output:

```
Scanning for nearby Parrot minidrones (5 seconds)...
 found minidrone: Mambo_596940 at address D0:3A:60:8B:E6:5A
```

Copy the address exactly, including the colons.

**If nothing is found:**
- Is the drone's battery charged and clicked in? (eyes lit?)
- Is another phone/laptop already connected to it? (see step 4.3)
- Is laptop Bluetooth actually on?
- Move the drone within 1–2 meters of the laptop and scan again.
- Multiple drones in the room? They all appear at once — match the
  `Mambo_XXXXXX` name to the sticker under each drone.

> **Note:** the address printed by the scanner is the one to use, even if
> a different number is printed on the drone itself.

---

## 6. First test flight

1. Open `examples/demoMamboDirectFlight.py` in a text editor
   (Notepad, VS Code, ...).
2. Replace the address at the top with YOUR drone's address:

   ```python
   mamboAddr = "D0:3A:60:8B:E6:5A"   # <- your address here
   ```

3. Put the drone on the floor, in a clear space, propeller guards ON.
4. Run it:

   ```
   python examples/demoMamboDirectFlight.py
   ```

The drone should take off, hover, drift forward gently, and land.
Watch the console — you should see
`Flying state before takeoff: landed`. If it says `unknown`, see
Troubleshooting below.

---

## 7. Safety rules (non-negotiable for camp)

- **Propeller guards always on.** No exceptions indoors.
- Clear a 3×3 meter space. Nobody inside it during flight.
- Fly LOW first (default hover height is fine). No `vertical_movement`
  greater than 20 until students are experienced.
- One person flies, one person watches (the "spotter" calls out problems).
- **Never grab a flying drone.** If something goes wrong: the program's
  landing sequence runs automatically, and closing the program
  (Ctrl+C, then let the script finish) still lands the drone —
  the Mambo auto-lands a few seconds after losing its Bluetooth link.
- Hair tied back, fingers away from propellers when carrying a powered drone.
- Low battery = weird behavior. Swap batteries at ~20%, don't push it.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `'python' is not recognized` | Reinstall Python with "Add to PATH" ticked, then close and reopen PowerShell. |
| `ModuleNotFoundError: No module named 'bleak'` | Run `pip install bleak untangle` again in the same PowerShell where you run the scripts. |
| Scanner finds nothing | Battery in and charged? Phone app closed? Bluetooth on? Drone within 2 m? |
| `Connected: False` after 3 tries | Power-cycle the drone (remove/reinsert battery), wait 10 s, retry. Make sure no phone is connected. |
| `handshake notify failed for ...fd24 / ...fd54` | **Harmless.** These are camera/file-transfer channels Windows can't subscribe to. Flight is unaffected. |
| `unknown channel for sender ...` spam | You are running an OLD `bleConnection.py`. Make sure the fixed file from this package is in `pyparrot/networking/`. |
| `Flying state before takeoff: unknown` | Same as above — the fixed file isn't being used, or the drone needs a power-cycle. |
| Drone won't land | The script sends multiple layers of land commands; as a last resort it disconnects, and the drone auto-lands on link loss. If truly stuck, remove yourself from under it and wait — it lands when the link drops. |
| Two students' laptops fight over one drone | One connection at a time. Match sticker numbers (see instructor tip in section 1). |

---

## 9. What to try next

Once the demo works, students can edit the middle section of the script:

```python
mambo.fly_direct(roll=0, pitch=10, yaw=0, vertical_movement=0, duration=1)
```

- `pitch` = forward/backward (−100..100)
- `roll` = left/right lean (−100..100)
- `yaw` = rotate (−100..100)
- `vertical_movement` = up/down (−100..100)
- `duration` = seconds

Keep values small (±10 to ±25) indoors. `mambo.turn_degrees(90)` and
`mambo.flip(direction="front")` are fun next steps — flips need fresh
batteries and ceiling clearance!

Full API documentation: https://pyparrot.readthedocs.io

---

## Credits & license

- Original pyparrot: Dr. Amy McGovern — https://github.com/amymcgovern/pyparrot (MIT License)
- Windows/macOS BLE port: based on bleak — https://github.com/hbldh/bleak (MIT License)
- This modified version is distributed under the same MIT License.
  See the LICENSE file. No warranty: fly responsibly, test before class.
