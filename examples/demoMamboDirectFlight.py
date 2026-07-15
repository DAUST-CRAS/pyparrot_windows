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

    print("Flying direct: going forward (positive pitch)")
    mambo.fly_direct(roll=0, pitch=10, yaw=0, vertical_movement=0, duration=1)

    print("Showing turning (in place) using turn_degrees")
    mambo.turn_degrees(90)
    mambo.smart_sleep(2)
    mambo.turn_degrees(-90)
    mambo.smart_sleep(2)

    print("Flying direct: yaw")
    mambo.fly_direct(roll=0, pitch=0, yaw=50, vertical_movement=0, duration=1)

    print("Flying direct: going backwards (negative pitch)")
    mambo.fly_direct(roll=0, pitch=-10, yaw=0, vertical_movement=0, duration=0.5)

    print("Flying direct: roll")
    mambo.fly_direct(roll=10, pitch=0, yaw=0, vertical_movement=0, duration=1)

    print("Flying direct: going up")
    mambo.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=50, duration=1)

    print("Flying direct: going around in a circle (yes you can mix roll, pitch, yaw in one command!)")
    mambo.fly_direct(roll=15, pitch=0, yaw=50, vertical_movement=0, duration=2)

    print("landing")
    mambo.safe_land(5)
    mambo.smart_sleep(5)

    print("disconnect")
    mambo.disconnect()
