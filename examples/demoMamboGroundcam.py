"""
Demo of the groundcam
Mambo takes off, takes a picture and shows a RANDOM frame, not the last one
Author: Valentin Benke, https://github.com/Vabe7
Author: Amy McGovern
"""

from pyparrot.Minidrone import Mambo

# Replace with your drone's address (run: python bleConnection.py to scan)
mamboAddr = "D0:3A:8A:89:E6:21"
mambo = Mambo(mamboAddr, use_wifi=False)

print("trying to connect to mambo now")
success = mambo.connect(num_retries=3)
print("connected: %s" % success)

if (success):
    # get the state information
    print("sleeping")
    mambo.smart_sleep(1)
    mambo.ask_for_state_update()
    mambo.smart_sleep(1)
    mambo.safe_takeoff(5)

    # take the photo
    pic_success = mambo.take_picture()

    # need to wait a bit for the photo to show up
    mambo.smart_sleep(0.5)

    picture_names = mambo.groundcam.get_groundcam_pictures_names() #get list of availible files
    print(picture_names)

    frame = mambo.groundcam.get_groundcam_picture(picture_names[0],True) #get frame which is the first in the array

    if frame is not None:
        if frame is not False:
            cv2.imshow("Groundcam", frame)
            cv2.waitKey(100)

    mambo.safe_land(5)
    mambo.disconnect()
