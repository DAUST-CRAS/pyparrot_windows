"""
Demo the trick flying for the python interface

Author: Amy McGovern
"""

from pyparrot.Minidrone import Mambo

# Replace with your drone's address (run: python bleConnection.py to scan)
mamboAddr = "D0:3A:8A:89:E6:21"
mambo = Mambo(mamboAddr, use_wifi=False)

print("trying to connect")
success = mambo.connect(num_retries=3)
print("connected: %s" % success)

if (success):
    # get the state information
    print("sleeping")
    mambo.smart_sleep(2)
    mambo.ask_for_state_update()
    mambo.smart_sleep(2)

    print("taking off!")
    mambo.safe_takeoff(5)

    if (mambo.sensors.flying_state != "emergency"):
        print("flying state is %s" % mambo.sensors.flying_state)
        print("Flying direct: going up")
        mambo.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=20, duration=1)

        print("flip left")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="left")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("flip right")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="right")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("flip front")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="front")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("flip back")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="back")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("landing")
        print("flying state is %s" % mambo.sensors.flying_state)
        mambo.safe_land(5)
        mambo.smart_sleep(5)

    print("disconnect")
    mambo.disconnect()
