import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import folium
import asyncio
from pyppeteer import launch
import os
import math
from geographiclib.geodesic import Geodesic

class AutopilotController:

    def buildFrame(self, frame, MQTTClient, showPositionsWindow, flightPlanDesignerWindow):
        # Build autopilot control label frame ----------------------
        self.frame = frame
        self.client = MQTTClient
        self.showPositionsWindow = showPositionsWindow
        self.flightPlanDesignerWindow = flightPlanDesignerWindow
        self.autopilotControlFrame = tk.LabelFrame(frame, text="Autopilot control", padx=5, pady=5)
        #autopilotControlFrame.pack(padx=20, side=tk.LEFT);

        # Arm/disarm frame ----------------------
        self.armDisarmFrame = tk.Frame(self.autopilotControlFrame)
        self.armDisarmFrame.pack(padx=20)
        self.armed = False
        self.armDisarmButton = tk.Button(self.armDisarmFrame, text="Arm drone", bg='red', fg="white", width=90, command=self.armDisarmButtonClicked)
        self.armDisarmButton.grid(column=0, row=0, pady=5)

        # bottomFrame frame ----------------------
        self.bottomFrame = tk.Frame(self.autopilotControlFrame)
        self.bottomFrame.pack(padx=20)

        # Autopilot get frame ----------------------
        self.autopilotGet = tk.Frame(self.bottomFrame)
        self.autopilotGet.pack(side=tk.LEFT, padx=20)

        self.v = tk.StringVar()
        tk.Radiobutton(self.autopilotGet, text="Altitude", variable=self.v, value=1).grid(column=0, row=0, columnspan=5,
                                                                                        sticky=tk.W)
        tk.Radiobutton(self.autopilotGet, text="Heading", variable=self.v, value=2).grid(column=0, row=1, columnspan=5,
                                                                                       sticky=tk.W)
        tk.Radiobutton(self.autopilotGet, text="Ground Speed", variable=self.v, value=3).grid(column=0, row=2,
                                                                                            columnspan=5, sticky=tk.W)
        self.v.set(1)

        self.autopilotGetButton = tk.Button(self.autopilotGet, text="Get", bg='red', fg="white", width=10, height=5,
                                       command=self.autopilotGetButtonClicked)
        self.autopilotGetButton.grid(column=5, row=0, columnspan=2, rowspan=3, padx=10)

        self.lbl = tk.Label(self.autopilotGet, text=" ", width=10, borderwidth=2, relief="sunken")
        self.lbl.grid(column=7, row=1, columnspan=2)

        # Autopilot set frame ----------------------
        self.autopilotSet = tk.Frame(self.bottomFrame)
        self.autopilotSet.pack(padx=20)

        self.takeOffButton = tk.Button(self.autopilotSet, text="Take Off", bg='red', fg="white", width=10,
                                  command=self.takeOffButtonClicked)
        self.takeOffButton.grid(column=0, row=1, columnspan=2, sticky=tk.W)

        self.to = tk.Label(self.autopilotSet, text="to")
        self.to.grid(column=2, row=1)
        self.metersEntry = tk.Entry(self.autopilotSet, width=10)
        self.metersEntry.grid(column=3, row=1, columnspan=2)
        self.meters = tk.Label(self.autopilotSet, text="meters")
        self.meters.grid(column=5, row=1)

        self.lat = tk.Label(self.autopilotSet, text="lat")
        self.lat.grid(column=2, row=2, columnspan=2, padx=5)

        self.lon = tk.Label(self.autopilotSet, text="lon")
        self.lon.grid(column=4, row=2, columnspan=2, padx=5)


        self.getPositionButton = tk.Button(self.autopilotSet, text="Get Position", bg='red', fg="white", width=10,
                                      command=self.getPositionButtonClicked)
        self.getPositionButton.grid(column=0, row=3, pady=5, sticky=tk.W)

        self.latLbl = tk.Label(self.autopilotSet, text=" ", width=10, borderwidth=2, relief="sunken")
        self.latLbl.grid(column=2, row=3, columnspan=2, padx=5)

        self.lonLbl = tk.Label(self.autopilotSet, text=" ", width=10, borderwidth=2, relief="sunken")
        self.lonLbl.grid(column=4, row=3, columnspan=2, padx=5)

        self.goToButton = tk.Button(self.autopilotSet, text="Go To", bg='red', fg="white", width=10, command=self.goToButtonClicked)
        self.goToButton.grid(column=0, row=4, pady=5, sticky=tk.W)

        self.goTolatEntry = tk.Entry(self.autopilotSet, width=10)
        self.goTolatEntry.grid(column=2, row=4, columnspan=2, padx=5)

        self.goTolonEntry = tk.Entry(self.autopilotSet, width=10)
        self.goTolonEntry.grid(column=4, row=4, columnspan=2, padx=5)

        self.returnToLaunchButton = tk.Button(self.autopilotSet, text="Return To Launch", bg='red', fg="white", width=40,
                                         command=self.returnToLaunchButtonClicked)
        self.returnToLaunchButton.grid(column=0, row=5, pady=5, columnspan=6, sticky=tk.W)

        # /////////////////Get stored data/////////////////////////////

        self.showRecordedPositionsButton = tk.Button(self.autopilotSet, text="Show recorded positions", bg='red', fg="white",
                                                width=40, command=self.showPositionsWindow.openWindowToShowRecordedPositions)
        self.showRecordedPositionsButton.grid(column=0, row=6, pady=5, columnspan=6, sticky=tk.W)

        # /////////////////Create and execute flight plan /////////////////////////////




        '''self.showFlightPlanCreationButton = tk.Button(self.autopilotSet, text="Flight plan creation and execution", bg='red',
                                                 fg="white", width=40, command=self.flightPlanDesignerWindow.openWindowToCreateFlightPlan)'''
        self.showFlightPlanCreationButton = tk.Button(self.autopilotSet, text="Flight plan creation and execution",
                                                      bg='red',
                                                      fg="white", width=40,
                                                      command=self.openSelectionWindow)
        self.showFlightPlanCreationButton.grid(column=0, row=7, pady=5, columnspan=6, sticky=tk.W)

        return self.autopilotControlFrame


    def armDisarmButtonClicked(self):

            if not self.armed:
                self.armDisarmButton['text'] = "Disarm drone"
                self.armDisarmButton['bg'] = "green"
                self.armed = True
                self.client.publish("autopilotControllerCommand/armDrone")

            else:
                self.armDisarmButton['text'] = "Arm drone"
                self.armDisarmButton['bg'] = "red"
                self.armed = False
                self.client.publish("autopilotControllerCommand/disarmDrone")

    def autopilotGetButtonClicked(self):
        if self.v.get() == "1":
            self.client.publish("autopilotControllerCommand/getDroneAltitude")
        elif self.v.get() == "2":
            self.client.publish("autopilotControllerCommand/getDroneHeading")
        else:
            self.client.publish("autopilotControllerCommand/getDroneGroundSpeed")

    def takeOffButtonClicked(self):
        self.client.publish("autopilotControllerCommand/takeOff", self.metersEntry.get())

    def getPositionButtonClicked(self):
        self.client.publish("autopilotControllerCommand/getDronePosition")

    def goToButtonClicked(self):
        position = str(self.goTolatEntry.get()) + '*' + str(self.goTolonEntry.get())
        print ('go to position ', position)
        self.client.publish("autopilotControllerCommand/goToPosition", position)

    def returnToLaunchButtonClicked(self):
        self.client.publish("autopilotControllerCommand/returnToLaunch")

    def putAnswer (self, answer):
        self.lbl['text'] = answer[:5]
    def putPosition (self, position):
        self.latLbl['text'] = position[0]
        self.lonLbl['text'] = position[1]


    async def convert(self):
        browser = await launch(headless=True)
        page = await browser.newPage()
        path = 'file://' + os.path.realpath('map.html')
        await page.goto(path)
        await page.screenshot({'path': 'map.png', 'fullPage': True})
        await browser.close()

    def click (self, e):
        print ('AAA?')
        if self.firstPoint:
            self.firstPoint = False
            self.A = e
        else:
            self.B = e
            pixels = math.sqrt((self.A.x - self.B.x) ** 2 + (self.A.y - self.B.y) ** 2)
            self.ppm = pixels / 71.67
            messagebox.showinfo(message=str (self.ppm), title="Calibration done")

    def closeCalibrateWindow(self):
        self.calibrateWindow.destroy()


    def openCalibrateWindow (self):
        self.calibrateWindow = tk.Toplevel(self.frame)
        self.calibrateWindow.title("Calibrate window")
        self.calibrateWindow.geometry("1000x1000")
        self.canvas = tk.Canvas(self.calibrateWindow, width=1100, height=700)
        self.canvas.grid(row=0, column=0, padx=(100, 0))

        zoon_level = 18

        token = "pk.eyJ1IjoibWlndWVsdmFsZXJvIiwiYSI6ImNsMjk3MGk0MDBnaGEzdG1tbGFjbWRmM2MifQ.JZZ6tJwPN28fo3ldg37liA"  # your mapbox token
        tileurl = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(token)

        my_map = folium.Map(
            location=[41.275946, 1.987475], max_zoom=zoon_level, zoom_start=zoon_level, tiles=tileurl,
            attr='Mapbox', control_scale=True)

        folium.Marker(
            location=[41.275946, 1.987475],
            popup="Timberline Lodge",
            icon=folium.Icon(color="green")
        ).add_to(my_map)

        folium.Marker(
            location=[41.275751, 1.986663],
            popup="Timberline Lodge",
            icon=folium.Icon(color="green")
        ).add_to(my_map)

        my_map.save("map.html")

        asyncio.get_event_loop().run_until_complete(self.convert())

        # subprocess.run(["python", "convert.py", 'map.html', 'map.png'])
        img = PhotoImage(file='map.png')

        img = img.zoom(15)  # with 250, I ended up running out of memory
        img = img.subsample(12)  # mechanically, here it is adjusted to 32 instead of 320

        # I do no know why but the next sentences is necessary
        self.frame.img = img
        self.image = self.canvas.create_image((0, 0), image=img, anchor="nw")
        instructionsText = "Click exactly in both marked positions"


        instructionsTextId = self.canvas.create_text(300, 400, text=instructionsText,
                                                          font=("Courier", 10, 'bold'))


        bbox = self.canvas.bbox(instructionsTextId)
        instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
        self.canvas.tag_raise(instructionsTextId, instructionsBackground)
        self.firstPoint = True
        self.canvas.bind("<ButtonPress-1>", self.click)

        close = tk.Button(self.calibrateWindow, text="close", bg='red', fg="white", width=100,
                          command=self.closeCalibrateWindow)
        close.grid(row=1, column=0, pady=30)


    def openSelectionWindow(self):
        self.newWindow = tk.Toplevel(self.frame)
        self.newWindow.title("Selection window")
        self.newWindow.geometry("1000x500")
        self.label = tk.Label(self.newWindow, text="Select the method to build the flight plan", width=50,  font=("Colibri", 25))
        self.label.grid (column = 0, row = 0, columnspan = 4, pady = 30)

        self.calibrateButtonBorder = tk.Frame(self.newWindow, highlightbackground="black",
                                 highlightthickness=2, bd=0)


        calibrateButton = tk.Button(self.calibrateButtonBorder, text="Calibrate distances", fg="black", width=100, height = 3,
                                 command=self.openCalibrateWindow).pack()
        self.calibrateButtonBorder.grid(row=1, column=0,  columnspan = 4, pady = 20)

        canvas1 = tk.Canvas(self.newWindow, width=200, height=200)
        canvas1.grid(row=2, column=0,  padx= 40,sticky="W")
        self.photoPoints = ImageTk.PhotoImage(Image.open("points.png").resize ((200,200)))
        canvas1.create_image(0,0, image=self.photoPoints, anchor="nw")
        pointsButton = tk.Button(self.newWindow, text="Fix waypoints by hand", bg='#375E97', fg="white", width=25,
                                    command=self.selectPoints)
        pointsButton.grid(row = 3, column=0, padx=50, sticky="W")


        canvas2 = tk.Canvas(self.newWindow, width=200, height=200)
        canvas2.grid(row=2, column=1, sticky="W")
        self.photoScan = ImageTk.PhotoImage(Image.open("parallelogram.png").resize((200, 200)))
        canvas2.create_image(0,0, image=self.photoScan, anchor="nw")
        scanButton = tk.Button(self.newWindow, text="Scan a parallelogram", bg='#FB6542', fg="black", width=25,
                                 command=self.selectScan)
        scanButton.grid(row=3, column=1, padx=10, sticky="W")



        canvas3 = tk.Canvas(self.newWindow, width=200, height=200)
        canvas3.grid(row=2, column=2, sticky="W")
        self.photoSpiral = ImageTk.PhotoImage(Image.open("spiral.png").resize((200, 200)))
        canvas3.create_image(0,0, image=self.photoSpiral,  anchor="nw")
        spiral = tk.Button(self.newWindow, text="Scan in spiral", bg='#FFBB00', fg="white", width=25,
                                 command=self.selectSpiral)
        spiral.grid(row = 3, column=2,padx=10, sticky="W")

        canvas4 = tk.Canvas(self.newWindow, width=200, height=200)
        canvas4.grid(row=2, column=3, sticky="W")
        self.photoLoad = ImageTk.PhotoImage(Image.open("load.png").resize((200, 200)))
        canvas4.create_image(0, 0, image=self.photoLoad,  anchor="nw")
        load = tk.Button(self.newWindow, text="Load flight plan", bg='#3F681C', fg="white", width=25,
                           command=self.loadFlightPlan)
        load.grid(row = 3, column=3,padx=10, sticky="W")

        close = tk.Button(self.newWindow, text="close", bg='#B7BBB6', fg="white", width=100,
                           command=self.close)
        close.grid(row = 4, column=0, columnspan = 4, pady = 30)

    def selectPoints (self):
        self.flightPlanDesignerWindow.putMode (1)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectScan(self):
        self.flightPlanDesignerWindow.putMode(2,  self.ppm)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectSpiral(self):
        self.flightPlanDesignerWindow.putMode(3,  self.ppm)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def loadFlightPlan(self):
        self.flightPlanDesignerWindow.putMode(0,  self.ppm)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def close(self):
        self.newWindow.destroy()


