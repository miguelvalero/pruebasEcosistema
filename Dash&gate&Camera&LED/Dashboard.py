import base64
import json
import cv2 as cv
from PIL import Image as Img
from PIL import ImageTk
import paho.mqtt.client as mqtt
import tkinter as tk
import numpy as np
import ssl

#from geographiclib.geodesic import Geodesic

import sys
sys.path.insert(0, './dashboardClasses')
from LEDsControllerClass import LEDsController
from CameraControllerClass import CameraController
from AutopilotControllerClass import AutopilotController
from ShowRecordedPositionsClass import RecordedPositionsWindow
from FlightPlanDesignerClass import FlightPlanDesignerWindow


# treatment of messages received from gate through the global broker

def on_message(client, userdata, message):

    if message.topic == "cameraControllerAnswer/videoFrame":
        img = base64.b64decode(message.payload)
        # converting into numpy array from buffer
        npimg = np.frombuffer(img, dtype=np.uint8)
        # Decode to Original Frame
        img = cv.imdecode(npimg, 1)
        # show stream in a separate opencv window
        cv.imshow("Stream", img)
        cv.waitKey(1)
    if message.topic == 'cameraControllerAnswer/picture':
        img = base64.b64decode(message.payload)
        # converting into numpy array from buffer
        npimg = np.frombuffer(img, dtype=np.uint8)
        # Decode to Original Frame
        cv2image = cv.imdecode(npimg, 1)
        dim = (300, 300)
        # resize image
        cv2image = cv.resize(cv2image, dim, interpolation=cv.INTER_AREA)

        img = Img.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)

        myCameraController.putPicture(imgtk)

        '''panel.destroy()
        panel = tk.Label(takePictureFrame, borderwidth=2, relief="raised")
        panel.imgtk = imgtk
        panel.configure(image=imgtk)
        panel.grid(column=0, row=1, rowspan=5, columnspan = 2)'''

    if (message.topic == "autopilotControllerAnswer/droneAltitude"):
        answer = str(message.payload.decode("utf-8"))
        myAutopilotController.putAnswer (answer)
    if (message.topic == "autopilotControllerAnswer/droneHeading"):
        answer = str(message.payload.decode("utf-8"))
        myAutopilotController.putAnswer(answer)
    if (message.topic == "autopilotControllerAnswer/droneGroundSpeed"):
        answer = str(message.payload.decode("utf-8"))
        myAutopilotController.putAnswer(answer)
    if (message.topic == "autopilotControllerAnswer/dronePosition"):
        positionStr = str(message.payload.decode("utf-8"))
        position = positionStr.split('*')
        myAutopilotController.putPosition(position)
        myFlightPlanDesignerWindow.putOriginalPosition(position[0], position[1])
    if (message.topic == "autopilotControllerAnswer/showDronePosition"):
        positionStr = str(message.payload.decode("utf-8"))
        position = positionStr.split('*')
        myFlightPlanDesignerWindow.showPosition(position)
    if  (message.topic == "dataServiceAnswer/storedPositions"):
        # receive the positions stored by the data service
        data = message.payload.decode("utf-8")
        # converts received string to json
        dataJson = json.loads(data)
        myRecordedPositionsWindow.putStoredPositions(dataJson)


master = tk.Tk()
client = mqtt.Client('Dashboard')
client.on_message = on_message
#global_broker_address ="127.0.0.1"
global_broker_port = 1884

global_broker_address ="classpip.upc.edu"
#global_broker_port = 1884

# to be taken from the autopilot service
originlat = 41.2759
originlon = 1.9875
'''
originlat = 31.7223
originlon = 2.4961
'''



# |--DASHBOARD master frame ----------------------------------------------------------------------------------|
# |                                                                                                           |
# |  |---connection frame--------------------------------------------------------------------------------|    |
# |  |---------------------------------------------------------------------------------------------------|    |
# |                                                                                                           |
# |  |---top frame---------------------------------------------------------------------------------------|    |
# |  |                                                                                                   |    |
# |  |   |--Autopilot control label frame ----------------------------|  |--LEDs control label frame--|  |    |
# |  |   |                                                            |  |                            |  |    |
# |  |   |  |--Arm/disarm frame -----------------------------------|  |  |----------------------------|  |    |
# |  |   |  |------------------------------------------------------|  |                                  |    |
# |  |   |                                                            |                                  |    |
# |  |   |  |--bottom frame ---------------------------------------|  |                                  |    |
# |  |   |  |                                                      |  |                                  |    |
# |  |   |  |  |-Autopilot get frame--|  |-Autopilot set frame -|  |  |                                  |    |
# |  |   |  |  |----------------------|  |----------------------|  |  |                                  |    |
# |  |   |  |                                                      |  |                                  |    |
# |  |   |  |------------------------------------------------------|  |                                  |    |
# |  |   |                                                            |                                  |    |
# |  |   |------------------------------------------------------------|                                  |    |
# |  |---------------------------------------------------------------------------------------------------|    |
# |                                                                                                           |
# |  |---camera control label frame----------------------------------------------------------------------|    |
# |  |                                                                                                   |    |
# |  |   |--- Take picture frame -----------|            |--- Video stream frame -----------|            |    |
# |  |   |                                  |            |                                  |            |    |
# |  |   |----------------------------------|            |----------------------------------|            |    |
# |  |---------------------------------------------------------------------------------------------------|    |
# |                                                                                                           |
# |-----------------------------------------------------------------------------------------------------------|



# Connection frame ----------------------
connected = False
connectionFrame = tk.Frame (master)
connectionFrame.pack(fill = tk.X)

def connectionButtonClicked():
    global connected
    global client
    if not connected:
        connectionButton['text'] = "Disconnect"
        connectionButton['bg'] = "green"
        connected = True
        client.username_pw_set(username='ecosystem', password='eco1342.')
        #client.tls_set("ca.crt","client.crt", "client.key", tls_version=ssl.PROTOCOL_TLSv1_2)
        client.connect(global_broker_address,  global_broker_port)
        print ('connect')
        client.publish("connectPlatform")
        client.loop_start()
        client.subscribe("#")
        print('Connected with drone platform')

        topFrame.pack(fill=tk.X)
        cameraControlFrame.pack(padx=20, pady=20);

    else:
        print('Disconnect')
        connectionButton['text'] = "Connect with drone platform"
        connectionButton['bg'] = "red"
        connected = False
        topFrame.pack_forget()
        ledsControlFrame.pack_forget()
        cameraControlFrame.pack_forget()

connectionButton = tk.Button(connectionFrame, text="Connect with drone platform", width = 150, bg='red', fg="white", command=connectionButtonClicked)
connectionButton.grid(row = 0, column = 0, padx=60, pady=20)


# top frame -------------------------------------------
topFrame = tk.Frame (master)


# Autopilot control label frame ----------------------
myRecordedPositionsWindow = RecordedPositionsWindow (master, client)
myFlightPlanDesignerWindow = FlightPlanDesignerWindow (master, client, originlat, originlon)
myAutopilotController = AutopilotController()
autopilotControlFrame= myAutopilotController.buildFrame(topFrame, client, myRecordedPositionsWindow, myFlightPlanDesignerWindow)
autopilotControlFrame.pack(padx=20, side = tk.LEFT);

# LEDs control frame ----------------------
ledsControlFrame= LEDsController().buildFrame(topFrame, client)
ledsControlFrame.pack(padx=20, pady=20);

# Camera control label frame ----------------------
myCameraController = CameraController()
cameraControlFrame= myCameraController.buildFrame(master, client)

master.mainloop()