import os

import folium
import tkinter as tk
from ttkwidgets import CheckboxTreeview
import subprocess
from tkinter import *
import json
import math
from geographiclib.geodesic import Geodesic
import asyncio
from pyppeteer import launch
from tkinter.filedialog import asksaveasfile, askopenfilename
from tkinter import messagebox



from html2image import Html2Image

class WaypointsWindow:
    def __init__(self, frame):
        self.window = tk.Toplevel(frame)
        self.window.title("Waypoint window")
        self.window.geometry("600x800")
        lab = tk.Label (self.window, text = "List of waypoints", font=("Calibri",20))
        lab.grid(row=0, column=0)

        self.table = CheckboxTreeview(self.window)

        self.table['column'] = ('wp', 'latitude', 'longitude')

        self.table.column("wp", anchor=tk.CENTER, width=40)
        self.table.column("latitude", anchor=tk.CENTER, width=150)
        self.table.column("longitude", anchor=tk.CENTER, width=150)

        self.table.heading("wp", text="wp", anchor=tk.CENTER)
        self.table.heading("latitude", text="Latitude", anchor=tk.CENTER)
        self.table.heading("longitude", text="Longitude", anchor=tk.CENTER)

        self.table.grid(row=1, column=0, padx = 20)
        self.wpNumber = 1

    def removeEntries (self):

        for i in self.table.get_children():
            self.table.delete(i)
        self.wpNumber = 1

    def insertHome (self, lat, lon):
        self.table.insert(parent='', index='end', iid=0, text='', values=('H', lat, lon))

    def insertWP (self, lat, lon):
        self.table.insert(parent='', index='end', iid=self.wpNumber, text='take picture?',
                          values=(self.wpNumber, lat, lon))
        self.wpNumber = self.wpNumber + 1

    def getCoordinates (self, wpId):
        # get lat and lon of the current position of the waypoint, that can be taken from the table
        entries = self.table.get_children()

        # finds the entry in the table corresponding to the waypoint

        entry = [en for en in entries if str(self.table.item(en)['values'][0]) == str(wpId)][0]

        lat = float(self.table.item(entry)['values'][1])
        lon = float(self.table.item(entry)['values'][2])
        return lat, lon

    def changeCoordinates(self, wpId, lat, lon):
        entries = self.table.get_children()
        # finds the entry in the table corresponding to the waypoint
        entry = [en for en in entries if str(self.table.item(en)['values'][0]) == str(wpId)][0]
        self.table.item(entry, values=(wpId, lat, lon))

    def insertRTL (self):
        self.table.insert(parent='', index='end', iid=self.wpNumber, text='take picture?',
                      values=('RTL', ' ', ' '))

    def getWaypoints (self):
        waypoints = []
        checkedList = self.table.get_checked()
        entries = self.table.get_children()

        for entry in entries[:-1]:
            if entry in checkedList:
                take = True
            else:
                take = False
            waypoints.append({
                'lat': self.table.item(entry)['values'][1],
                'lon': self.table.item(entry)['values'][2],
                'takePic': take
            })
        return waypoints
    def checkLastEntry (self):
        self.table.change_state(self.table.get_children()[-1], "checked")

    def focus_force (self):
        self.window.focus_force()


class FlightPlanDesignerWindow:

    def __init__(self, frame, MQTTClient, originlat, originlon):
        self.frame = frame   # father frame
        self.client = MQTTClient
        self.originlat = originlat
        self.originlon = originlon


        self.done = False
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.fourthPoint = False

        self.wpNumber = 1
        self.geod = Geodesic.WGS84
        self.waypointsIds = []
        self.defaultDistance = 10 # default distance for parallelogram and spiral scans (10 meters)



    def putOriginalPosition (self,originlat, originlon):
        print ('original position ', self.originlat, self.originlon)
        self.originlat = originlat
        self.originlon = originlon

    def showPosition(self, position):
        print ('position ', position)
        lat = position[0]
        lon = position [1]
        if position[2] == '0':
            color = 'yellow'
        else:
            color = 'red'

        g = self.geod.Inverse(float(self.dronPositionx), float(self.dronPositiony), float(lat),float(lon))
        azimuth = 180 - float(g['azi2'])
        dist = float(g['s12'])
        print ('azimut y distance ', azimuth, dist)
        print ('ppm ', self.ppm)
        print ('dron psition pixels ', self.dronePositionPixelx, self.dronePositionPixely)
        newposx = self.dronePositionPixelx + math.trunc(dist * self.ppm * math.sin(math.radians(azimuth)))
        newposy = self.dronePositionPixely + math.trunc(dist * self.ppm * math.cos(math.radians(azimuth)))
        print ('new position ', newposx, newposy)
        self.canvas.itemconfig(self.dronePositionId, fill = color)
        self.canvas.coords(self.dronePositionId, newposx - 15, newposy - 15, newposx+ 15, newposy + 15)
        self.dronPositionx = lat
        self.dronPositiony = lon
        self.dronePositionPixelx = newposx
        self.dronePositionPixely = newposy


    def putMode (self, mode):
        self.mode = mode  # 1: points, 2: parallelogram scan, 3: spiral scan


    async def convert(self):
        browser = await launch(headless=True)
        page = await browser.newPage()
        path = 'file://' + os.path.realpath('map.html')
        await page.goto(path)
        await page.screenshot({'path': 'map.png', 'fullPage': True})
        await browser.close()

    def openWindowToCreateFlightPlan(self):
            self.newWindow = tk.Toplevel(self.frame)
            self.newWindow.title("Create and execute flight plan")
            self.newWindow.geometry("1400x800")

            title = tk.Label( self.newWindow, text="Create and execute flight plan", font=("Calibri",25))
            title.grid(row=0, column=0, columnspan=3)
            self.canvas = tk.Canvas( self.newWindow, width=1100, height=700)
            self.canvas.grid(row=1, column=0, padx=(100, 0))
            self.controlFrame = tk.LabelFrame(self.newWindow, text="Control", width=200, height=700)
            self.controlFrame.grid(row=1, column=1,padx=0)
            if self.mode == 0 or self.mode == 1:
                self.clearButton = tk.Button(self.controlFrame, height=6, width=10, text="Clear", bg='#375E97',
                                             fg="white", command=self.clear)
                self.clearButton.grid(row=0, column=0, padx=10, pady=20)
                runButton = tk.Button(self.controlFrame, height=6, width=10, text="Run", bg='#FFBB00', fg="black",
                                      command=self.runButtonClick)
                runButton.grid(row=1, column=0, padx=10, pady=20)
                saveButton = tk.Button(self.controlFrame, height=6, width=10, text="Save", bg='#FB6542', fg="white",
                                       command=self.saveButtonClick)
                saveButton.grid(row=2, column=0, padx=10, pady=20)
                closeButton = tk.Button(self.controlFrame, height=6, width=10, text="Close", bg='#B7BBB6', fg="white",
                                        command=self.closeWindowToToCreateFlightPlan)
                closeButton.grid(row=3, column=0, padx=10, pady=20)

                '''elif self.mode == 1:
                self.clearButton = tk.Button(self.controlFrame, height = 6, width = 10, text="Clear", bg='green', fg="white", command=self.clear)
                self.clearButton.grid(row=0, column=0, padx = 10, pady = 20)
                runButton = tk.Button(self.controlFrame, height = 6, width = 10, text="Run", bg='orange', fg="black",
                                      command=self.runButtonClick)
                runButton.grid(row=1, column=0, padx = 10, pady = 20)
                saveButton = tk.Button(self.controlFrame, height=6, width=10, text="Save", bg='#0059b3', fg="white",
                                      command=self.saveButtonClick)
                saveButton.grid(row=2, column=0, padx=10, pady=20)
                closeButton = tk.Button(self.controlFrame, height = 6, width = 10, text="Close", bg='red', fg="white",
                                        command=self.closeWindowToToCreateFlightPlan)
                closeButton.grid(row=3, column=0, padx = 10, pady = 20)'''
            else:
                self.sliderFrame = tk.LabelFrame(self.controlFrame, text='Select separation (meters)')
                self.sliderFrame.grid(row=0, column=0,  padx = 10, pady = 20)
                self.label = tk.Label(self.sliderFrame, text="create scan first").pack()

                self.clearButton = tk.Button(self.controlFrame,  height = 7, width = 10, text="Clear", bg='#375E97', fg="white",
                                             command=self.clear)
                self.clearButton.grid(row=1, column=0,  padx = 10, pady = 20)

                runButton = tk.Button(self.controlFrame, height = 7, width = 10, text="Run", bg='#FFBB00', fg="black",
                                  command=self.runButtonClick)
                runButton.grid(row=2, column=0,  padx = 10, pady = 20)

                saveButton = tk.Button(self.controlFrame, height=7, width=10, text="Save", bg='#FB6542', fg="white",
                                       command=self.saveButtonClick)
                saveButton.grid(row=3, column=0, padx=10, pady=20)

                closeButton = tk.Button(self.controlFrame, height = 7, width = 10, text="Close", bg='#B7BBB6', fg="white",
                                    command=self.closeWindowToToCreateFlightPlan)
                closeButton.grid(row=4, column=0,  padx = 10, pady = 20)


            self.wpWindow = WaypointsWindow (self.frame)
            '''self.table = CheckboxTreeview(self.newWindow)

            self.table['column'] = ('wp', 'latitude', 'longitude')

            self.table.column("wp", anchor=tk.CENTER, width=10)
            self.table.column("latitude", anchor=tk.CENTER, width=50)
            self.table.column("longitude", anchor=tk.CENTER, width=50)

            self.table.heading("wp", text="wp", anchor=tk.CENTER)
            self.table.heading("latitude", text="Latitude", anchor=tk.CENTER)
            self.table.heading("longitude", text="Longitude", anchor=tk.CENTER)

            self.table.grid(row=1, column=2, padx=10, pady=0)'''



            # to calibrate the distance measurement I did the following
            # In google maps I measure the a few real distances in meters between different positions
            # In the program I compute the corresponding distances in pixels
            # With this I compute an approximation to the number of meters per pixel (mpp)
            # finally, when computing the distance in pixel I must multiply by this factor
            # Of course, the factor depends on the zoom level of the map and also depends on the latitude
            # of the working area.
            # The data obtained for the latitude of Barcelona (lat = 40) are
            # Zoom level: 19, mpp = 0.2235
            # Zoom level: 20, mpp = 0.1122
            # more interesting information here: https://docs.mapbox.com/help/glossary/zoom-level/
            self.mpp = 0.2235
            zoon_level = 19
            self.ppm = 1 / self.mpp
            self.d = self.defaultDistance

            token = "pk.eyJ1IjoibWlndWVsdmFsZXJvIiwiYSI6ImNsMjk3MGk0MDBnaGEzdG1tbGFjbWRmM2MifQ.JZZ6tJwPN28fo3ldg37liA"  # your mapbox token
            tileurl = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(token)

            my_map = folium.Map(
                location=[self.originlat, self.originlon], max_zoom = zoon_level, zoom_start=zoon_level, tiles=tileurl, attr='Mapbox', control_scale=True)

            folium.Marker(
                location=[self.originlat, self.originlon],
                popup="Timberline Lodge",
                icon=folium.Icon(color="green")
            ).add_to(my_map)
            my_map.save("map.html")
            asyncio.get_event_loop().run_until_complete(self.convert())

            '''hti = Html2Image()
            hti.screenshot(
                html_file='map.html',
                save_as='map.png'
            )'''
            #subprocess.run(["python", "convert.py", 'map.html', 'map.png'])
            img = PhotoImage(file='map.png')

            #img = img.zoom(15)  # with 250, I ended up running out of memory
            #img = img.subsample(12)  # mechanically, here it is adjusted to 32 instead of 320

            # I do no know why but the next sentences is necessary
            self.frame.img = img
            self.image = self.canvas.create_image((0, 0), image=img, anchor="nw")
            if self.mode == 0:
                instructionsText = "Click in home position \nand select the file with the flight plan"
            if self.mode == 1:
                instructionsText = "Click in home position \nand fix the sequence of waypoints"
            if self.mode == 2:
                instructionsText = "Click in home position \nand define parallelogram to be scaned"
            if self.mode == 3:
                instructionsText = "Click in home position \nand decide spiral direction and length"

            self.instructionsTextId = self.canvas.create_text(300, 400, text=instructionsText,
                                                              font=("Courier", 10, 'bold'))
            bbox = self.canvas.bbox(self.instructionsTextId)
            self.instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
            self.canvas.tag_raise(self.instructionsTextId,  self.instructionsBackground)

            self.canvas.bind("<ButtonPress-1>", self.click)
            self.canvas.bind("<Motion>", self.drag)
            if self.mode == 1:
                self.canvas.bind("<ButtonPress-3>", self.returnToLaunch)



    def closeWindowToToCreateFlightPlan(self):
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.done = False
        self.newWindow.destroy()



    def runButtonClick (self):
        '''waypoints = []
        checkedList = self.table.get_checked()
        entries = self.table.get_children()

        for entry in entries[:-1]:
            if entry in checkedList:
                take = True
            else:
                take = False
            waypoints.append({
                'lat': self.table.item(entry)['values'][1],
                'lon': self.table.item(entry)['values'][2],
                'takePic': take
            })'''
        waypoints = self.wpWindow.getWaypoints()
        waypoints_json = json.dumps(waypoints)
        self.client.publish("autopilotControllerCommand/executeFlightPlan", waypoints_json)
        print ('asigno posicion original ', self.originlat, self.originlon)
        self.dronPositionx = self.originlat
        self.dronPositiony = self.originlon
        self.dronePositionPixelx = self.originx
        self.dronePositionPixely = self.originy
        self.dronePositionId = self.canvas.create_oval(self.originx - 15, self.originy - 15, self.originx + 15, self.originy + 15,
                                         fill='red')

    def clear(self):
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.done = False
        self.wpNumber = 1

        items = self.canvas.find_all()

        for item in items:
            if item != self.image:
                self.canvas.delete(item)

        self.wpWindow.removeEntries()
        '''for i in self.table.get_children():
            self.table.delete(i)'''

        if self.mode == 2 or self.mode == 3:
            self.sliderFrame.destroy()

            self.sliderFrame = tk.LabelFrame(self.controlFrame, text='Select separation (meters)')
            self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)

            self.label = tk.Label(self.sliderFrame, text="create first").pack()

        self.d = self.defaultDistance

        if self.mode == 0:
            instructionsText = "Click in home position \nand select the file with the flight plan"
        if self.mode == 1:
            instructionsText = "Click in home position \nand fix the sequence of waypoints"
        if self.mode == 2:
            instructionsText = "Click in home position \nand define parallelogram to be scaned"
        if self.mode == 3:
            instructionsText = "Click in home position \nand decide spiral direction and length"

        self.instructionsTextId = self.canvas.create_text(300, 400, text=instructionsText,
                                                          font=("Courier", 10, 'bold'))
        bbox = self.canvas.bbox(self.instructionsTextId)
        self.instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
        self.canvas.tag_raise(self.instructionsTextId, self.instructionsBackground)
        self.canvas.bind("<Motion>", self.drag)

    def saveButtonClick (self):
        waypoints = self.wpWindow.getWaypoints()
        f = asksaveasfile(mode='w', defaultextension=".json")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            messagebox.showinfo(message="Flight plan NOT saved", title="File save")
        else:
            waypoints_json = json.dumps(waypoints)
            f.write(waypoints_json)
            f.close()
            messagebox.showinfo(message="Flight plan saved", title="File save")
        self.newWindow.focus_force()

    def drawFlighPlan (self, waypoints):

        self.waypointsIds =[]
        home = waypoints[0]
        ovalId = self.canvas.create_oval(self.originx - 10, self.originy - 10, self.originx + 10, self.originy + 10, fill='blue')
        textId = self.canvas.create_text(self.originx, self.originy, text='H', font=("Courier", 10, 'bold'), fill='white')
        prev = home
        posx = self.originx
        posy = self.originy
        wpNum = 1
        self.waypointsIds.append({
            'wpId': 'H',
            'textId': textId,
            'ovalId': ovalId,
            'lineInId': 0,
            'lineOutId': 0,
            'distanceFromId': 0,
            'distanceToId': 0
        })
        self.wpWindow.insertHome(home['lat'], home['lon'])
        if (home['takePic']):
            self.wpWindow.checkLastEntry()

        for wp in waypoints [1:]:
            g = self.geod.Inverse (float(prev['lat']), float(prev['lon']), float(wp['lat']), float(wp['lon']))
            azimuth = 180 - float(g['azi2'])
            dist = float(g['s12'])

            newposx = posx + math.trunc(dist*self.ppm * math.sin(math.radians(azimuth)))
            newposy = posy + math.trunc(dist*self.ppm * math.cos(math.radians(azimuth)))
            lineId = self.canvas.create_line(posx, posy, newposx, newposy)
            distId = self.canvas.create_text(posx + (newposx - posx) / 2,
                               posy + (newposy- posy) / 2, text=str(round(dist, 2)), font=("Courier", 15, 'bold'),
                                    fill='red')
            posx = newposx
            posy = newposy
            ovalId =self.canvas.create_oval( posx - 10, posy - 10, posx + 10, posy + 10,
                                    fill='blue')
            textId = self.canvas.create_text(posx, posy, text=str(wpNum), font=("Courier", 10, 'bold'), fill='white')
            self.waypointsIds [-1]['lineOutId'] = lineId
            self.waypointsIds[-1]['distanceToId'] = distId
            self.waypointsIds.append({
                'wpId': str(wpNum),
                'textId': textId,
                'ovalId': ovalId,
                'lineInId': lineId,
                'lineOutId': 0,
                'distanceFromId': distId,
                'distanceToId': 0
            })
            self.wpWindow.insertWP(wp['lat'], wp['lon'])
            if (wp['takePic']):
                self.wpWindow.checkLastEntry()
            wpNum = wpNum + 1
            prev = wp

        lineId = self.canvas.create_line(posx, posy, self.originx, self.originy)
        g = self.geod.Inverse(float(prev['lat']), float(prev['lon']), float(home['lat']), float(home['lon']))
        dist = float(g['s12'])
        distId = self.canvas.create_text(posx + (self.originx - posx) / 2,
                                posy + (self.originy - posy) / 2, text=str(round(dist, 2)), font=("Courier", 15, 'bold'),
                                fill='red')
        self.waypointsIds[-1]['lineOutId'] = lineId
        self.waypointsIds[-1]['distanceToId'] = distId
        self.waypointsIds[0]['lineInId'] = lineId
        self.waypointsIds[0]['distanceFrom'] = distId
        self.wpWindow.insertRTL()
        self.wpWindow.focus_force()

    '''
    def loadButtonClick (self):
        fileName = askopenfilename()
        if fileName is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            messagebox.showinfo(message="NO file selected", title="File open")
        else:
            messagebox.showinfo(message="File selected", title="File open")
            file = open(fileName)
            waypoints = json.load(file)
            self.drawFlighPlan (waypoints)
        self.newWindow.focus_force()
    '''
    def click(self, e):
            if self.done:
                # if flight plan is done then the user wants to change the position of a waypoint
                # select the ids of elements of the canvas that are close to the clicked waypoint
                selected = self.canvas.find_overlapping(e.x - 10, e.y - 10, e.x + 10, e.y + 10)

                if selected:
                    # finds the ids of the selected waypoint
                    # Among the selected items there must be the id of the text of the selected waypoint
                    self.waypointToMoveIds = [wp for wp in self.waypointsIds if wp['textId'] in selected][0]
                    # now we are ready to drag the waypoint
                    self.canvas.bind("<B1-Motion>", self.moveWp)

            elif self.mode == 0:
                if self.firstPoint:
                    # origin point
                    self.originx = e.x
                    self.originy = e.y
                    self.canvas.delete(self.instructionsTextId)
                    self.canvas.delete(self.instructionsBackground)

                    fileName = askopenfilename()
                    if fileName is None:  # asksaveasfile return `None` if dialog closed with "cancel".
                        messagebox.showinfo(message="NO file selected", title="File open")
                    else:
                        messagebox.showinfo(message="File selected", title="File open")
                        file = open(fileName)
                        waypoints = json.load(file)
                        self.drawFlighPlan(waypoints)
                    self.newWindow.focus_force()
                    self.done = True
                    self.firstPoint = False

            elif self.mode == 1:

                if self.firstPoint:
                    self.canvas.delete(self.instructionsTextId)
                    self.canvas.delete(self.instructionsBackground)
                    # the user select the position for the initial waypoint
                    self.firstPoint = False
                    # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                    # previous point
                    self.previousx = e.x
                    self.previousy = e.y

                    # origin point
                    self.originx = e.x
                    self.originy = e.y

                    # Create a line starting in origin
                    self.lineOutId = self.canvas.create_line(self.originx, self.originy, e.x, e.y)
                    # Create oval and text por the origin (H) waypoint
                    self.ovalId = self.canvas.create_oval(e.x - 10, e.y - 10, e.x + 10, e.y + 10, fill='blue')
                    self.textId = self.canvas.create_text(e.x, e.y, text='H', font=("Courier", 10, 'bold'), fill='white')
                    # create a text for the distance
                    self.distanceToId = self.canvas.create_text(e.x, e.y, text='0', font=("Courier", 15, 'bold'),
                                                                fill='red')

                    # adds to the list the ids of the elements corresponding to the home waypoint
                    self.waypointsIds.append({
                        'wpId': 'H',
                        'textId': self.textId,
                        'ovalId': self.ovalId,
                        'lineInId': 0,
                        'lineOutId': self.lineOutId,
                        'distanceFromId': 0,
                        'distanceToId': self.distanceToId
                    })

                    # current lat, lon are the origin coordinates
                    self.lat = self.originlat
                    self.lon = self.originlon

                    # insert information of origin waypoint in the table
                    self.wpWindow.insertHome(self.lat, self.lon)
                    #self.table.insert(parent='', index='end', iid=0, text='', values=('H', self.lat, self.lon))
                else:
                    # the user is fixing the next waypoint
                    # create the elements (line, oval, text and distance) for the new waypoint
                    self.lineId = self.canvas.create_line(e.x, e.y, e.x, e.y)
                    self.ovalId = self.canvas.create_oval(e.x - 10, e.y - 10, e.x + 10, e.y + 10, fill='blue')
                    self.textId = self.canvas.create_text(e.x, e.y, text=str(self.wpNumber), font=("Courier", 10, 'bold'),
                                                          fill='white')
                    self.distanceId = self.canvas.create_text(e.x, e.y, text='0', font=("Courier", 15, 'bold'), fill='red')

                    # adds the ids of the new waypoint to the list
                    self.waypointsIds.append({
                        'wpId': self.wpNumber,
                        'textId': self.textId,
                        'ovalId': self.ovalId,
                        'lineInId': self.waypointsIds[-1]['lineOutId'],
                        'lineOutId': self.lineId,
                        'distanceFromId': self.waypointsIds[-1]['distanceToId'],
                        'distanceToId': self.distanceId
                    })

                    # compute distance from previous waypoint
                    dist = math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2) * self.mpp
                    # compute azimuth
                    azimuth = math.degrees(math.atan2((self.previousx - e.x), (self.previousy - e.y))) * (-1)
                    if azimuth < 0:
                        azimuth = azimuth + 360
                    # compute lat,log of new waypoint
                    g = self.geod.Direct(float(self.lat), float(self.lon), azimuth, dist)
                    self.lat = float(g['lat2'])
                    self.lon = float(g['lon2'])

                    # insert new waypoint in table
                    self.wpWindow.insertWP(self.lat, self.lon)
                    '''self.table.insert(parent='', index='end', iid=self.wpNumber, text='take picture?',
                                      values=(self.wpNumber, self.lat, self.lon))'''
                    # update previouos point
                    self.previousx = e.x
                    self.previousy = e.y
                    self.wpNumber = self.wpNumber + 1

            elif self.mode == 2:
                if self.firstPoint:
                    self.canvas.delete(self.instructionsTextId)
                    self.canvas.delete(self.instructionsBackground)
                    # the user starts defining the area (rectangle) to be scanned
                    # Four points (A, B, C and D) must be defined
                    self.originposx = e.x
                    self.originposy = e.y
                    self.firstPoint = False
                    self.secondPoint = True
                    # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                    self.points = []
                    # A point
                    self.Ax = e.x
                    self.Ay = e.y
                    self.points.append((self.Ax, self.Ay))
                    self.points.append((self.Ax, self.Ay))
                    self.points.append((self.Ax, self.Ay))
                    self.points.append((self.Ax, self.Ay))
                    self.rectangle = self.canvas.create_polygon(self.points, outline='red', fill='', width=5)
                    self.distanceX = self.canvas.create_text(e.x, e.y, text='0', font=("Courier", 15, 'bold'),
                                                             fill='red')

                elif self.secondPoint:
                    # the user is fixing point B
                    self.secondPoint = False
                    self.thirdPoint = True

                    self.Bx = e.x
                    self.By = e.y

                    self.azimuth1 = math.degrees(math.atan2((self.Ax - e.x), (self.Ay - e.y))) * (-1)
                    if self.azimuth1 < 0:
                        self.azimuth1 = self.azimuth1 + 360
                    self.x = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2)
                    self.distanceY = self.canvas.create_text(e.x, e.y, text='0', font=("Courier", 15, 'bold'),
                                                             fill='red')

                    self.wpNumber = self.wpNumber + 1
                elif self.thirdPoint:
                    # the user is fixing point C
                    self.thirdPoint = False
                    self.azimuth2 = math.degrees(math.atan2((self.Bx - e.x), (self.By - e.y))) * (-1)
                    if self.azimuth2 < 0:
                        self.azimuth2 = self.azimuth2 + 360
                    self.y = math.sqrt((e.x - self.Bx) ** 2 + (e.y - self.By) ** 2)

                    self.createScan()

                    self.sliderFrame.destroy()

                    self.sliderFrame = tk.LabelFrame(self.controlFrame, text='Select separation (meters)')
                    self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)

                    self.slider = tk.Scale(self.sliderFrame, from_=10, to=50, length=150,
                                           orient="horizontal",
                                           activebackground='green',
                                           tickinterval=10,
                                           resolution=10,
                                           command=self.reCreate)
                    self.slider.grid(row=0, column=0, padx=0, pady=0)


            else:
                if self.firstPoint:

                    self.canvas.delete(self.instructionsTextId)
                    self.canvas.delete(self.instructionsBackground)

                    # the user starts defining the area (rectangle) to be scanned
                    # Four points (A, B, C and D) must be defined

                    self.originx = e.x
                    self.originy = e.y
                    self.firstPoint = False
                    self.secondPoint = True
                    # I must remember the clicked coordinates, that in this case will be also the origin coordinates


                    # A point
                    self.Ax = e.x
                    self.Ay = e.y

                    self.line = self.canvas.create_line(self.Ax,self.Ay, e.x, e.y, fill='red', width = 3)
                    self.distance = self.canvas.create_text(e.x, e.y, text='0', font=("Courier", 15, 'bold'),
                                                                fill='red')
                elif self.secondPoint:
                    # the user is fixing point B
                    self.secondPoint = False
                    self.azimuth = math.degrees(math.atan2((self.Ax - e.x), (self.Ay - e.y))) * (-1)
                    if self.azimuth < 0:
                        self.azimuth = self.azimuth1 + 360
                    self.x = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2)

                    self.createSpiral()

                    self.sliderFrame.destroy()

                    self.sliderFrame = tk.LabelFrame(self.controlFrame, text='Select separation (meters)')
                    self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)
                    self.slider = tk.Scale(self.sliderFrame, from_=10, to=50, length=150,
                                           orient="horizontal",
                                           activebackground='green',
                                           tickinterval=10,
                                           resolution=10,
                                           command=self.reCreate)
                    self.slider.grid(row=0, column=0, padx=0, pady=0)

    def drag(self,e):

        if self.mode == 1:
            if not self.firstPoint:
                # the user is draging the mouse to decide where to place next waypoint
                dist = math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2) * self.mpp

                # show distance in the middle of the line
                self.canvas.coords(self.waypointsIds[-1]['distanceToId'], self.previousx + (e.x - self.previousx) / 2,
                                   self.previousy + (e.y - self.previousy) / 2)
                self.canvas.itemconfig(self.waypointsIds[-1]['distanceToId'], text=str(round(dist, 2)))
                # Change the coordinates of the last created line to the new coordinates
                self.canvas.coords(self.waypointsIds[-1]['lineOutId'], self.previousx, self.previousy, e.x, e.y)

        if self.mode == 2:
            if self.secondPoint:
                # the user is draging the mouse to decide the direction and lenght of the first dimension of parallelogram
                self.points[1] = (e.x, e.y)
                self.points[2] = (e.x, e.y)
                self.canvas.delete(self.rectangle)
                self.rectangle = self.canvas.create_polygon(self.points, outline='red', fill='', width=5)
                dist = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2) * self.mpp

                # show distance in the middle of the line
                self.canvas.coords(self.distanceX, self.Ax + (e.x - self.Ax) / 2,
                                   self.Ay + (e.y - self.Ay) / 2)
                self.canvas.itemconfig(self.distanceX, text=str(round(dist, 2)))
            elif self.thirdPoint:
                # the user is draging the mouse to decide the direction and lenght of the second dimension of parallelogram

                dist = math.sqrt((e.x - self.Bx) ** 2 + (e.y - self.By) ** 2)
                angle = math.degrees(math.atan2((self.Bx - e.x), (self.By - e.y))) * (-1)
                if angle < 0:
                    angle = angle + 360

                Cx = self.Bx + dist * math.cos(math.radians(angle - 90))
                Cy = self.By + dist * math.sin(math.radians(angle - 90))

                Dx = self.Ax + dist * math.cos(math.radians(angle - 90))
                Dy = self.Ay + dist * math.sin(math.radians(angle - 90))

                self.points[2] = (Cx, Cy)
                self.points[3] = (Dx, Dy)
                self.canvas.delete(self.rectangle)
                self.rectangle = self.canvas.create_polygon(self.points, outline='red', fill='', width=5)
                # show distance in the middle of the line
                self.canvas.coords(self.distanceY, self.Bx + (e.x - self.Bx) / 2,
                                   self.By + (e.y - self.By) / 2)
                self.canvas.itemconfig(self.distanceY, text=str(round(dist * self.mpp, 2)))

        if self.mode == 3:
            if self.secondPoint:
                # the user is draging the mouse to decide the direction and lenght of spiral
                self.canvas.coords(self.line, self.Ax, self.Ay, e.x, e.y)
                dist = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2)*self.mpp

                # show distance in the middle of the line
                self.canvas.coords(self.distance, self.Ax + (e.x - self.Ax) / 2,
                              self.Ay + (e.y - self.Ay) / 2)
                self.canvas.itemconfig(self.distance, text=str(round(dist, 2)))



    def moveWp(self,e):
            # the user is moving a waypoints
            # the ids of this waypoint are in waypointToMoveIds
            if not self.waypointToMoveIds['wpId'] == 'H':
                # can move any waypoint except home
                # move the oval and the text
                self.canvas.coords(self.waypointToMoveIds['ovalId'], e.x - 10, e.y - 10, e.x + 10, e.y + 10)
                self.canvas.coords(self.waypointToMoveIds['textId'], e.x, e.y)

                # get coordinates of lineIn and lineout
                lineInCoord = self.canvas.coords(self.waypointToMoveIds['lineInId'])
                lineOutCoord = self.canvas.coords(self.waypointToMoveIds['lineOutId'])

                # these are the coordinates of the waypoint
                wpCoord = (lineInCoord[2], lineInCoord[3])

                # compute distance and azimuth from the current position of the waypoint

                dist = math.sqrt((e.x - wpCoord[0]) ** 2 + (e.y - wpCoord[1]) ** 2)*self.mpp
                azimuth = math.degrees(math.atan2((wpCoord[0] - e.x), (wpCoord[1] - e.y))) * (-1)
                if azimuth < 0:
                    azimuth = azimuth + 360
                lat,lon = self.wpWindow.getCoordinates(self.waypointToMoveIds['wpId'])
                # get lat and lon of the current position of the waypoint, that can be taken from the table
                '''entries = self.table.get_children()

                # finds the entry in the table corresponding to the waypoint

                entry = [en for en in entries if str(self.table.item(en)['values'][0]) == str(self.waypointToMoveIds['wpId'])][0]

                lat = float(self.table.item(entry)['values'][1])
                lon = float(self.table.item(entry)['values'][2])'''

                # compute new position of the waypoint
                g = self.geod.Direct(lat, lon, azimuth, dist)
                lat = float(g['lat2'])
                lon = float(g['lon2'])

                # change info in the table
                self.wpWindow.changeCoordinates(self.waypointToMoveIds['wpId'], lat,lon)
                # self.table.item(entry, values=(self.waypointToMoveIds['wpId'], lat, lon))

                # change coordinates of arriving and departing lines
                self.canvas.coords(self.waypointToMoveIds['lineInId'], lineInCoord[0], lineInCoord[1], e.x, e.y)
                self.canvas.coords(self.waypointToMoveIds['lineOutId'], e.x, e.y, lineOutCoord[2], lineOutCoord[3])

                if self.mode == 0 or self.mode == 1 :
                    # change distance labels
                    distFrom = math.sqrt((e.x - lineInCoord[0]) ** 2 + (e.y - lineInCoord[1]) ** 2) * self.mpp
                    distTo = math.sqrt((e.x - lineOutCoord[2]) ** 2 + (e.y - lineOutCoord[3]) ** 2) * self.mpp

                    # show distance in the middle of the line
                    self.canvas.coords(self.waypointToMoveIds['distanceFromId'],
                                       lineInCoord[0] + (e.x - lineInCoord[0]) / 2,
                                       lineInCoord[1] + (e.y - lineInCoord[1]) / 2)
                    self.canvas.itemconfig(self.waypointToMoveIds['distanceFromId'], text=str(round(distFrom, 2)))

                    self.canvas.coords(self.waypointToMoveIds['distanceToId'],
                                       lineOutCoord[2] + (e.x - lineOutCoord[2]) / 2,
                                       lineOutCoord[3] + (e.y - lineOutCoord[3]) / 2)
                    self.canvas.itemconfig(self.waypointToMoveIds['distanceToId'], text=str(round(distTo, 2)))



    def returnToLaunch(self,e):

        # right button click to finish the flight plan (only in mode 1)

        # complete the ids of the home waypoint
        self.waypointsIds[0]['lineInId'] = self.waypointsIds[-1]['lineOutId']
        self.waypointsIds[0]['distanceFromId'] = self.waypointsIds[-1]['distanceToId']


        # modify last line to return to launch

        self.canvas.coords(self.waypointsIds[-1]['lineOutId'], self.previousx , self.previousy, self.originx, self.originy)

        # compute distance to home
        dist = math.sqrt((self.originx - self.previousx) ** 2 + (self.originy - self.previousy) ** 2)*self.mpp

        self.canvas.coords(self.distanceId, self.previousx + (self.originx- self.previousx) / 2 , self.previousy + (self.originy - self.previousy) / 2 )
        self.canvas.itemconfig(self.distanceId, text=str(round(dist,2)))

        # insert return to launch in the table
        self.wpWindow.insertRTL ()
        '''self.table.insert(parent='', index='end', iid=self.wpNumber, text='take picture?',
                     values=('RL', ' ',' ' ))'''

        # change color of all lines
        for wp in self.waypointsIds:
            self.canvas.itemconfig(wp['lineOutId'], fill="blue")
            self.canvas.itemconfig(wp['lineOutId'], width=3)

        # ignore mouse drag from now on
        self.canvas.unbind("<Motion>")

        self.done = True

    def reCreate (self, event):
        # new distance for scan has been selected
        self.d = self.slider.get()

        '''for i in self.table.get_children():
            self.table.delete(i)'''
        self.wpWindow.removeEntries()

        items = self.canvas.find_all()
        if self.mode == 2:
            for item in items:
                if item != self.rectangle and item != self.image and item != self.distanceY and item != self.distanceX:
                    self.canvas.delete(item)
            self.createScan ()

        if self.mode == 3:
            for item in items:
                if item != self.line and item != self.image and item != self.distance:
                    self.canvas.delete(item)
            self.createSpiral()


    def createScan (self):

        azimuth1 = 180 - self.azimuth1
        azimuth2 = 180 - self.azimuth2
        self.posx = self.originposx
        self.posy = self.originposy
        num = math.ceil(self.y / (self.d * self.ppm))
        waypoints = []
        self.waypointToMoveIds = []
        lat = float (self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
        textId = self.canvas.create_text(self.posx, self.posy, text='H', font=("Courier", 10, 'bold'), fill='white')
        self.waypointsIds.append({
            'wpId': 'H',
            'textId': textId,
            'ovalId': ovalId,
            'lineInId': 0,
            'lineOutId': 0
        })

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat,lon)
        cont = 1
        for i in range (num//2):
                g = self.geod.Direct(lat, lon, azimuth1, self.x*self.mpp)
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)
                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx =self.posx +  math.trunc(self.x * math.sin(math.radians(azimuth1)))
                newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))

                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy


                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text= str(cont), font=("Courier", 10, 'bold'), fill='white')
                self.waypointsIds [-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1

                g = self.geod.Direct(lat, lon, azimuth2, self.d)
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)

                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
                newposy = self.posy + math.trunc(self.d*self.ppm * math.cos(math.radians(azimuth2)))

                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy

                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'),
                                        fill='white')
                self.waypointsIds[-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1


                g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x*self.mpp)
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)

                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx = self.posx + math.trunc(self.x * math.sin(math.radians((azimuth1 + 180)%360)))
                newposy = self.posy + math.trunc(self.x * math.cos(math.radians((azimuth1 + 180)%360)))
                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy
                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'),
                                        fill='white')
                self.waypointsIds[-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1

                g = self.geod.Direct(lat, lon, azimuth2, self.d)
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)

                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
                newposy = self.posy + math.trunc(self.d *self.ppm * math.cos(math.radians(azimuth2)))
                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy
                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'), fill='white')
                self.waypointsIds[-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1

        g = self.geod.Direct(lat, lon, azimuth1, self.x*self.mpp)
        lat = float(g['lat2'])
        lon = float(g['lon2'])
        waypoints.append({
            'lat': lat,
            'lon': lon,
            'takePic': False
        })
        self.wpWindow.insertWP(lat, lon)

        #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
        newposx = self.posx + math.trunc(self.x * math.sin(math.radians(azimuth1)))
        newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))
        lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
        self.posx = newposx
        self.posy = newposy
        ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
        textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'), fill='white')
        self.waypointsIds[-1]['lineOutId'] = lineId
        self.waypointsIds.append({
            'wpId': str(cont),
            'textId': textId,
            'ovalId': ovalId,
            'lineInId': lineId,
            'lineOutId': 0
        })
        cont = cont + 1

        if num%2 != 0:
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g['lat2'])
            lon = float(g['lon2'])
            waypoints.append({
                'lat': lat,
                'lon': lon,
                'takePic': False
            })
            self.wpWindow.insertWP(lat, lon)

            #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
            newposy = self.posy + math.trunc(self.d*self.ppm * math.cos(math.radians(azimuth2)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
            textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'), fill='white')
            self.waypointsIds[-1]['lineOutId'] = lineId
            self.waypointsIds.append({
                'wpId': str(cont),
                'textId': textId,
                'ovalId': ovalId,
                'lineInId': lineId,
                'lineOutId': 0
            })
            cont = cont + 1

            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x*self.mpp)
            lat = float(g['lat2'])
            lon = float(g['lon2'])
            waypoints.append({
                'lat': lat,
                'lon': lon,
                'takePic': False
            })
            self.wpWindow.insertWP(lat, lon)

            #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(self.x * math.sin(math.radians((azimuth1 + 180) % 360)))
            newposy = self.posy + math.trunc(self.x * math.cos(math.radians((azimuth1 + 180) % 360)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
            textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'), fill='white')
            self.waypointsIds[-1]['lineOutId'] = lineId
            self.waypointsIds.append({
                'wpId': str(cont),
                'textId': textId,
                'ovalId': ovalId,
                'lineInId': lineId,
                'lineOutId': 0
            })

        self.done = True
        #waypoints_json = json.dumps(waypoints)
        #self.client.publish("autopilotControllerCommand/executeFlightPlan", waypoints_json)



    def createSpiral (self):

        azimuth = 180 - self.azimuth
        self.posx = self.originx
        self.posy = self.originy
        num = math.ceil (self.x / (self.d*self.ppm));
        waypoints = []
        self.waypointToMoveIds = []
        lat = float (self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
        textId = self.canvas.create_text(self.posx, self.posy, text='H', font=("Courier", 10, 'bold'), fill='white')
        self.waypointsIds.append({
            'wpId': 'H',
            'textId': textId,
            'ovalId': ovalId,
            'lineInId': 0,
            'lineOutId': 0
        })

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat,lon)
        #self.table.insert(parent='', index='end', iid=0, text='', values=('H', lat,lon))
        cont = 1
        for i in range (num):
                dist = (2*i+1)*self.d
                g = self.geod.Direct(lat, lon, azimuth, dist)
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)

                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx =self.posx +  math.trunc(dist*self.ppm * math.sin(math.radians(azimuth)))
                newposy = self.posy + math.trunc(dist*self.ppm * math.cos(math.radians(azimuth)))

                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy


                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text= str(cont), font=("Courier", 10, 'bold'), fill='white')
                self.waypointsIds [-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1

                g = self.geod.Direct(lat, lon, azimuth + 90, dist)
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)

                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx = self.posx + math.trunc(dist*self.ppm * math.sin(math.radians(azimuth+90)))
                newposy = self.posy + math.trunc(dist*self.ppm * math.cos(math.radians(azimuth+90)))

                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy

                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'),
                                        fill='white')
                self.waypointsIds[-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1


                g = self.geod.Direct(lat, lon, azimuth + 180, dist+self.d)
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)

                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx = self.posx + math.trunc((dist+self.d)*self.ppm * math.sin(math.radians(azimuth + 180)))
                newposy = self.posy + math.trunc((dist+self.d)*self.ppm * math.cos(math.radians(azimuth + 180)))
                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy
                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'),
                                        fill='white')
                self.waypointsIds[-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1

                g = self.geod.Direct(lat, lon, azimuth + 270,(dist+self.d))
                lat = float(g['lat2'])
                lon = float(g['lon2'])
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'takePic': False
                })
                self.wpWindow.insertWP(lat,lon)

                #self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
                newposx = self.posx + math.trunc((dist+self.d)*self.ppm * math.sin(math.radians(azimuth + 270)))
                newposy = self.posy + math.trunc((dist+self.d)*self.ppm * math.cos(math.radians(azimuth + 270)))
                lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
                self.posx = newposx
                self.posy = newposy
                ovalId = self.canvas.create_oval(self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill='blue')
                textId = self.canvas.create_text(self.posx, self.posy, text=str(cont), font=("Courier", 10, 'bold'), fill='white')
                self.waypointsIds[-1]['lineOutId'] = lineId
                self.waypointsIds.append({
                    'wpId': str(cont),
                    'textId': textId,
                    'ovalId': ovalId,
                    'lineInId': lineId,
                    'lineOutId': 0
                })
                cont = cont + 1
        self.done = True



