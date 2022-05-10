import folium
import tkinter as tk
from ttkwidgets import CheckboxTreeview
import subprocess
from tkinter import *
import json
import math
from geographiclib.geodesic import Geodesic


class FlightPlanDesignerWindow:



    def __init__(self, frame, MQTTClient, originlat, originlon):
        self.frame = frame
        self.client = MQTTClient
        self.done = False
        self.firstPoint =True
        self.wpNumber = 1
        self.geod = Geodesic.WGS84
        self.waypointsIds = []
        self.originlat = originlat
        self.originlon = originlon
        self.x = 200
        self.y = 200
        self.defaultDistance = 10  # default distance for scan and spiral (10 meters)
        self.azimuth1 = 250
        self.azimuth2 = 250
        self.posx = 300
        self.posy = 300


        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.fourthPoint = False

    def putOriginalPosition (self,originlat, originlon):
        self.originlat = originlat
        self.originlon = originlon

    def openWindowToCreateFlightPlan(self):
            self.newWindow = tk.Toplevel(self.frame)
            self.newWindow.title("Create and execute flight plan")
            self.newWindow.geometry("1400x800")

            title = tk.Label( self.newWindow, text="Create and execute flight plan")
            title.grid(row=0, column=0, columnspan=3)
            self.canvas = tk.Canvas( self.newWindow, width=800, height=600)

            # canvas.create_image(0, 0, image=img, anchor="nw")
            self.canvas.grid(row=1, column=0, columnspan=2, padx=10, pady=0)

            # table2 = ttk.Treeview(newWindow2)
            self.table = CheckboxTreeview(self.newWindow)

            self.table['column'] = ('wp', 'latitude', 'longitude')

            self.table.column("wp", anchor=tk.CENTER, width=30)
            self.table.column("latitude", anchor=tk.CENTER, width=120)
            self.table.column("longitude", anchor=tk.CENTER, width=120)


            self.table.heading("wp", text="wp", anchor=tk.CENTER)
            self.table.heading("latitude", text="Latitude", anchor=tk.CENTER)
            self.table.heading("longitude", text="Longitude", anchor=tk.CENTER)

            self.table.grid(row=1, column=2, padx=10, pady=0)

            self.clearButton = tk.Button(self.newWindow, width = 50, height = 2, text="Clear",  bg='red', fg="white", command=self.clear)
            self.clearButton.grid(row=2, column=0, rowspan = 2)

            self.sliderFrame= tk.LabelFrame(self.newWindow, text = 'Select distance in meters for scanning')
            self.sliderFrame.grid(row=2, column=1, padx=0, pady=0)
            self.label = tk.Label(self.sliderFrame, width = 60, text="create first").pack()



            runButton = tk.Button(self.newWindow, text="Run the flight plan", width=80, bg='red', fg="white",
                                  command=self.runButtonClick)
            runButton.grid(row=4, column=0, columnspan = 2)

            closeButton = tk.Button(self.newWindow, text="Close", width=80, bg='red', fg="white",
                                    command=self.closeWindowToToCreateFlightPlan)
            closeButton.grid(row=5, column=0, columnspan = 2)






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

            zoon_level = 19
            self.mpp = 0.2235
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
            subprocess.run(["python", "convert.py", 'map.html', 'map.png'])
            img = PhotoImage(file='map.png')
            # I do no know why but the next sentences is necessary
            self.frame.img = img
            self.image = self.canvas.create_image((0, 0), image=img, anchor="nw")

            instructionsText = "Click in home position \nand define the parallelogram to be scanned"
            self.instructionsTextId = self.canvas.create_text(300, 400, text=instructionsText,
                                                              font=("Courier", 10, 'bold'))
            bbox = self.canvas.bbox(self.instructionsTextId)
            self.instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
            self.canvas.tag_raise(self.instructionsTextId, self.instructionsBackground)

            self.canvas.bind("<ButtonPress-1>", self.click)
            self.canvas.bind("<ButtonPress-3>", self.returnToLaunch)
            self.canvas.bind("<Motion>", self.drag)


    def closeWindowToToCreateFlightPlan(self):
            self.newWindow.destroy()


    def runButtonClick (self):
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
        print('waypoints ')
        print(waypoints)
        waypoints_json = json.dumps(waypoints)
        self.client.publish("autopilotControllerCommand/executeFlightPlan", waypoints_json)



    def clear (self):
        self.firstPoint = True
        self.done = False

        items = self.canvas.find_all()

        for item in items:
            if item != self.image:
                self.canvas.delete(item)

        for i in self.table.get_children():
            self.table.delete(i)

        self.sliderFrame.destroy()
        self.sliderFrame = tk.LabelFrame(self.newWindow, text='Select distance in meters for scanning', width=100, height = 3)
        self.sliderFrame.grid(row=2, column=1, padx=0, pady=0)
        self.label = tk.Label(self.sliderFrame, width = 60, text="create first").pack()
        self.d = self.defaultDistance

        instructionsText = "Click in home position \nand define the parallelogram to be scanned"
        self.instructionsTextId = self.canvas.create_text(300, 400, text=instructionsText,
                                                          font=("Courier", 10, 'bold'))
        bbox = self.canvas.bbox(self.instructionsTextId)
        self.instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
        self.canvas.tag_raise(self.instructionsTextId, self.instructionsBackground)



    def click(self, e):
            if self.done:
                # if flight plan is done then the user wants to change the position of a waypoint
                # select the ids of elements of the canvas that are close to the clicked waypoint
                selected = self.canvas.find_overlapping(e.x - 10, e.y - 10, e.x + 10, e.y + 10)
                print ('selected ', selected)
                print ('waypointsID', self.waypointsIds)
                if selected:
                    # finds the ids of the selected waypoint
                    # Among the selected items there must be the id of the text of the selected waypoint
                    self.waypointToMoveIds = [wp for wp in self.waypointsIds if wp['textId'] in selected][0]
                    print ( 'waypoint selected', self.waypointToMoveIds)
                    # now we are ready to drag the waypoint
                    self.canvas.bind("<B1-Motion>", self.moveWp)

            elif self.firstPoint:
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
                self.points.append ((self.Ax, self.Ay))
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
                self.distanceY= self.canvas.create_text(e.x, e.y, text='0', font=("Courier", 15, 'bold'),
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
                self.sliderFrame = tk.LabelFrame(self.newWindow, width=60,
                                                 text='Select distance in meters for scanning')
                self.sliderFrame.grid(row=2, column=1, padx=0, pady=0)
                self.slider = tk.Scale(self.sliderFrame, from_=10, to=50, length=350,
                                       orient="horizontal",
                                       activebackground='green',
                                       tickinterval=10,
                                       resolution=10,
                                       command=self.reCreate)
                self.slider.grid(row=0, column=0, padx=0, pady=0)



    def drag(self,e):
        if self.secondPoint:
            self.points[1] = (e.x, e.y)
            self.points[2] = (e.x, e.y)
            self.canvas.delete(self.rectangle)
            self.rectangle = self.canvas.create_polygon(self.points, outline='red', fill='', width=5)
            # the user is draging the mouse to decide where to place next waypoint
            dist = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2) * self.mpp

            # show distance in the middle of the line
            self.canvas.coords(self.distanceX, self.Ax + (e.x -  self.Ax) / 2,
                                self.Ay + (e.y - self.Ay) / 2)
            self.canvas.itemconfig(self.distanceX, text=str(round(dist, 2)))
        elif self.thirdPoint:

            dist = math.sqrt((e.x - self.Bx) ** 2 + (e.y - self.By) ** 2)
            angle = math.degrees(math.atan2((self.Bx - e.x), (self.By - e.y))) * (-1)
            if angle < 0:
                angle = angle + 360

            Cx = self.Bx + dist * math.cos (math.radians(angle - 90))
            Cy = self.By + dist * math.sin (math.radians(angle - 90))

            Dx = self.Ax + dist * math.cos(math.radians(angle - 90))
            Dy = self.Ay + dist * math.sin(math.radians(angle - 90))

            self.points[2] = (Cx,Cy)
            self.points[3] = (Dx, Dy)
            self.canvas.delete (self.rectangle)
            self.rectangle = self.canvas.create_polygon(self.points, outline = 'red', fill = '', width = 5)
            # show distance in the middle of the line
            self.canvas.coords(self.distanceY, self.Bx + (e.x - self.Bx) / 2,
                               self.By + (e.y - self.By) / 2)
            self.canvas.itemconfig(self.distanceY, text=str(round(dist*self.mpp, 2)))


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

                # get lat and lon of the current position of the waypoint, that can be taken from the table
                entries = self.table.get_children()
                print ('entries')

                # finds the entry in the table corresponding to the waypoint
                entry = [en for en in entries if str(self.table.item(en)['values'][0]) == self.waypointToMoveIds['wpId']][0]

                lat = float(self.table.item(entry)['values'][1])
                lon = float(self.table.item(entry)['values'][2])

                # compute new position of the waypoint
                g = self.geod.Direct(lat, lon, azimuth, dist)
                lat = float(g['lat2'])
                lon = float(g['lon2'])

                # chage info in the table
                self.table.item(entry, values=(self.waypointToMoveIds['wpId'], lat, lon))

                # change coordinates of arriving and departing lines
                self.canvas.coords(self.waypointToMoveIds['lineInId'], lineInCoord[0], lineInCoord[1], e.x, e.y)
                self.canvas.coords(self.waypointToMoveIds['lineOutId'], e.x, e.y, lineOutCoord[2], lineOutCoord[3])


                # this is to avoid that the text with the distance appears on top of the line
                # better a little bit displaced



    def returnToLaunch(self,e):

        # right button click to finish the flight plan

        # complete the ids of the home waypoint
        self.waypointsIds[0]['lineInId'] = self.waypointsIds[-1]['lineOutId']
        self.waypointsIds[0]['distanceFromId'] = self.waypointsIds[-1]['distanceToId']


        # modify last line to return launch
        self.canvas.coords(self.waypointsIds[-1]['lineOutId'], self.previousx, self.previousy, self.originx, self.originy)

        # compute distance to home
        dist = math.sqrt((self.originx - self.previousx) ** 2 + (self.originy - self.previousy) ** 2)*self.mpp

        self.canvas.coords(self.distanceId, self.previousx + (self.originx- self.previousx) / 2 , self.previousy + (self.originy - self.previousy) / 2 )
        self.canvas.itemconfig(self.distanceId, text=str(round(dist,2)))

        # insert return to launch in the table
        self.table.insert(parent='', index='end', iid=self.wpNumber, text='take picture?',
                     values=('RL', ' ',' ' ))

        # change color of all lines
        for wp in self.waypointsIds:
            self.canvas.itemconfig(wp['lineOutId'], fill="blue")
            self.canvas.itemconfig(wp['lineOutId'], width=3)

        # ignore mouse drag from now on
        self.canvas.unbind("<Motion>")

        self.done = True

    def reCreate (self, event):
        print ('voy')

        self.d = self.slider.get()
        items = self.canvas.find_all()

        for item in items:
            if item != self.rectangle and item != self.image and item != self.distanceY and item != self.distanceX:
                self.canvas.delete (item)


        for i in self.table.get_children():
            self.table.delete(i)
        self.createScan()



    def createScan (self):

        azimuth1 = 180 - self.azimuth1
        azimuth2 = 180 - self.azimuth2
        self.posx = self.originposx
        self.posy = self.originposy
        num = math.ceil(self.x / (self.d * self.ppm));
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
        self.table.insert(parent='', index='end', iid=0, text='', values=('H', lat,lon))
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
                self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
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
                self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
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
                self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
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
                self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
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
        self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
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
            self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
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
            self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
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



