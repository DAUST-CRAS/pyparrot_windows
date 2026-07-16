# Programming the Parrot Mambo — Camp Tutorial

Welcome, pilot! In this tutorial you will learn to control a real drone with
Python code. No remote control, no phone app — **your program is the pilot.**

Before starting, complete the [Installation Guide](INSTALL_GUIDE.md):
Python installed, library installed, and your drone's address found with
`find_mambo`.

---

# Unit 1 — Getting to Know Your Mambo

## Lesson 1.1 — Introduction

Drones are used everywhere today: filming, delivery, agriculture,
search-and-rescue, inspection of bridges and wind turbines. What all these
have in common is **autonomy** — the drone follows a program, not just a
joystick. That is exactly what you'll build this week: programs that fly.

**Get to know your Mambo.** Find these parts on your drone:

- **4 propellers** — two spin clockwise, two counter-clockwise (that's how
  it steers!)
- **Propeller guards** — always attached indoors
- **Battery** — clips in underneath; the drone's "eyes" light up when powered
- **Eyes (LEDs)** — also show status: steady = ready, blinking = problem or
  low battery
- **Accessory port** (on top) — this is where the **claw** (grab and drop
  objects) or the **cannon** (fires small plastic balls) clips in. We'll
  program both in Unit 3!

Each drone has a name like `Mambo_627406` and a unique Bluetooth address
like `D0:3A:8A:89:E6:21` — check the sticker on your drone.

## Lesson 1.2 — Before You Fly (Safety)

A pilot's first job is safety. These rules are **not optional**:

1. **Propeller guards on**, always, indoors.
2. **Clear a 3×3 meter space.** Nobody inside it while flying.
3. **Two people per flight**: one pilot (runs the code), one spotter
   (watches the drone and calls out problems).
4. **Never grab a flying drone.** If something goes wrong, hands off:
   every program we write lands the drone automatically, and even if the
   program crashes, the Mambo lands itself a few seconds after losing its
   Bluetooth link.
5. **Fly low first.** No big `vertical_movement` values until Unit 2 is
   mastered.
6. **Respect the battery.** Below ~20% the drone behaves strangely — swap
   batteries, don't push it.
7. Tie back long hair; keep fingers away from propellers when carrying a
   powered drone.

**Spotter's emergency procedure:** shout "LAND!", pilot presses
`Ctrl+C` in PowerShell — our programs catch this and land immediately.

## Lesson 1.3 — Python Is Your Controller

Other drones come with a physical remote controller. Yours doesn't need
one: Python is your controller. Every flight program has the same skeleton —
learn it once and you'll reuse it all week.

Create a file `my_first_flight.py`:

```python
from pyparrot.Minidrone import Mambo

# YOUR drone's address (from find_mambo — check the sticker!)
mamboAddr = "D0:3A:8A:89:E6:21"

mambo = Mambo(mamboAddr, use_wifi=False)

print("trying to connect")
success = mambo.connect(num_retries=3)
print("connected: %s" % success)

if success:
    try:
        # let the drone wake up and send us its status
        mambo.smart_sleep(2)
        mambo.ask_for_state_update()
        mambo.smart_sleep(2)

        print("taking off!")
        mambo.safe_takeoff(5)

        # ============================
        #  YOUR FLIGHT CODE GOES HERE
        # ============================
        mambo.smart_sleep(3)   # for now: just hover for 3 seconds

    except KeyboardInterrupt:
        print("Emergency stop requested!")

    finally:
        print("landing")
        mambo.safe_land(5)
        mambo.smart_sleep(2)
        print("disconnect")
        mambo.disconnect()
```

Run it (drone on the floor, space clear, spotter ready):

```
python my_first_flight.py
```

**Understanding the skeleton:**

- `connect(num_retries=3)` — opens the Bluetooth link, tries 3 times
- `smart_sleep(seconds)` — the drone's version of waiting. **Always use
  this, never `time.sleep()`** — smart_sleep keeps listening to the drone
  while waiting.
- `safe_takeoff(5)` / `safe_land(5)` — take off / land, waiting up to 5
  seconds for the drone to confirm it happened
- `try / except KeyboardInterrupt / finally` — the safety net: whatever
  happens (your code crashes, or someone presses Ctrl+C), the `finally`
  block **always** runs and lands the drone. Every program you write this
  week must keep this structure.

## Lesson 1.4 — Troubleshooting

Things go wrong for every programmer — debugging is a pilot skill too.

- **Install/connection problems** (ModuleNotFoundError, drone not found,
  `Connected: False`): see the [Installation Guide troubleshooting
  table](INSTALL_GUIDE.md#troubleshooting).
- **`handshake notify failed for ...fd24/fd54`** when connecting:
  harmless, ignore it.
- **Drone connects but won't take off:** battery too low, or the drone is
  not flat — place it on level ground. The eyes blink when the battery is
  low.
- **Drone drifts on its own while hovering:** land, place it perfectly flat
  and still, then add `mambo.flat_trim()` right after `ask_for_state_update`
  — this recalibrates its sense of "level".
- **The program froze:** `Ctrl+C`. Our skeleton catches it and lands.
- **Golden debugging rule:** read the error message *bottom line first* —
  Python tells you exactly what it didn't like.

---

# Unit 2 — Flying with Code

## Lesson 2.1 — Moving: fly_direct

One command moves the drone in any direction:

```python
mambo.fly_direct(roll=0, pitch=10, yaw=0, vertical_movement=0, duration=1)
```

| Parameter | What it does | Range |
|---|---|---|
| `pitch` | forward (+) / backward (−) | −100 to 100 |
| `roll` | slide right (+) / left (−) | −100 to 100 |
| `yaw` | rotate right (+) / left (−) | −100 to 100 |
| `vertical_movement` | up (+) / down (−) | −100 to 100 |
| `duration` | how long, in seconds | |

The numbers are **percentages of maximum power** — and 100% is *very* fast.
Indoors, stay between **10 and 25**.

Drop these into the skeleton's "YOUR FLIGHT CODE" zone, one at a time:

```python
print("forward")
mambo.fly_direct(roll=0, pitch=10, yaw=0, vertical_movement=0, duration=1)
mambo.smart_sleep(1)

print("backward")
mambo.fly_direct(roll=0, pitch=-10, yaw=0, vertical_movement=0, duration=1)
mambo.smart_sleep(1)

print("slide right")
mambo.fly_direct(roll=10, pitch=0, yaw=0, vertical_movement=0, duration=1)
mambo.smart_sleep(1)

print("up")
mambo.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=30, duration=1)
mambo.smart_sleep(1)
```

**Why the `smart_sleep(1)` between moves?** It lets the drone stabilize —
without it, moves blur together and the drone wobbles.

**Experiment:** you can mix parameters in ONE command. What shape does this
fly?

```python
mambo.fly_direct(roll=15, pitch=0, yaw=50, vertical_movement=0, duration=2)
```

## Lesson 2.2 — Precise Turns: turn_degrees

`yaw` rotates by *power and time* — imprecise. For exact angles:

```python
mambo.turn_degrees(90)     # quarter turn right
mambo.smart_sleep(2)
mambo.turn_degrees(-90)    # quarter turn left
mambo.smart_sleep(2)
mambo.turn_degrees(180)    # about-face
```

## Lesson 2.3 — Challenges

Time to earn your wings. For each challenge, plan the moves on paper first —
real pilots plan before they fly.

**Challenge 1 — The Square 🟨**
Fly a square: forward, quarter turn, forward, quarter turn... back to start,
facing the way you began.
*Hint: a `for` loop makes this 4 lines instead of 16.*

```python
for side in range(4):
    mambo.fly_direct(roll=0, pitch=15, yaw=0, vertical_movement=0, duration=1)
    mambo.smart_sleep(1)
    mambo.turn_degrees(90)
    mambo.smart_sleep(2)
```

**Challenge 2 — The Elevator 🛗**
Take off, rise for 1 second, descend for 1 second, land. Smooth, no wobble.

**Challenge 3 — The Compass 🧭**
Face each of the 4 directions in turn, hovering 2 seconds at each, using
`turn_degrees`.

**Challenge 4 — Free Design ✏️**
Invent a 15-second routine: draw the path on paper, write it, fly it.
Bonus style points if it ends exactly where it started.

**Challenge 5 — The Flip 🤸 (instructor permission required)**
Fresh battery, high ceiling, extra clear space:

```python
mambo.flip(direction="front")   # also: "back", "left", "right"
mambo.smart_sleep(3)
```

---

# Unit 3 — Accessories and Sensors

## Lesson 3.1 — The Claw 🦾

Clip the claw accessory onto the top port. The claw can grab and release
light objects — the classic mission: pick up a small ball, fly it across
the room, drop it in a cup.

```python
print("open and close the claw")
mambo.open_claw()
mambo.smart_sleep(5)   # the claw needs time to move — always sleep after!

mambo.close_claw()
mambo.smart_sleep(5)
```

**Mission — Air Delivery 📦:** place an object in the open claw, close it,
take off, fly to a target 2 meters away, land, open the claw. Full points
if the object ends up inside the target zone.

## Lesson 3.2 — The Cannon 🎯

Clip on the cannon accessory (fires soft plastic balls — **never aim at
people or animals**; set up a paper target).

The cannon works even without flying:

```python
print("fire!")
mambo.fire_gun()
mambo.smart_sleep(10)   # firing takes time — sleep before the next command
```

**Mission — Target Practice:** take off, hover, turn to face the paper
target, fire, land. Teams score by hits out of 3 balls.

## Lesson 3.3 — Reading Sensors

Your drone talks back! After `ask_for_state_update()`, the `mambo.sensors`
object holds live data:

```python
print("battery: %s%%" % mambo.sensors.battery)
print("flying state: %s" % mambo.sensors.flying_state)
```

`flying_state` is one of: `landed`, `takingoff`, `hovering`, `flying`,
`landing`, `emergency`.

**Smart pilot upgrade:** make your program refuse to take off when the
battery is weak. Add this before `safe_takeoff`:

```python
if mambo.sensors.battery < 30:
    print("Battery too low to fly safely: %s%%" % mambo.sensors.battery)
else:
    mambo.safe_takeoff(5)
    # ... rest of the flight ...
```

## Lesson 3.4 — Final Project 🏆

You now have everything you need: the safety skeleton, movement commands,
precise turns, accessories, and sensors. Your final mission will be
announced by your instructors — get ready to combine it all.

---

*Happy flying! Fork of [pyparrot](https://github.com/amymcgovern/pyparrot)
by Dr. Amy McGovern — full API reference at https://pyparrot.readthedocs.io*
