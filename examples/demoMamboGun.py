"""
Demo the gun for the python interface

Author: Amy McGovern
"""

from pyparrot.Minidrone import Mambo

# Replace with your drone's address (run: python bleConnection.py to scan)
mamboAddr = "D0:3A:8A:89:E6:21"
mambo = Mambo(mamboAddr, use_wifi=False)

print("trying to connect")
success = mambo.connect(num_retries=3)
print("connected: %s" % success)

# get the state information
print ("sleeping")
mambo.smart_sleep(2)
mambo.ask_for_state_update()
mambo.smart_sleep(2)

print("shoot the gun")
mambo.fire_gun()
# sleep to ensure it does the firing
mambo.smart_sleep(10)
mambo.fire_gun()
# sleep to ensure it does the firing
mambo.smart_sleep(10)

print("disconnect")
mambo.disconnect()
