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

    def putOriginalPosition (self,originlat, originlon):
        self.originlat = float (originlat)
        self.originlon = float (originlon)

    def openWindowToCreateFlightPlan(self):
            self.newWindow = tk.Toplevel(self.frame)
            self.newWindow.title("Create and execute flight plan")
            self.newWindow.geometry("1400x800")

            title = tk.Label( self.newWindow, text="Create and execute flight plan")
            title.grid(row=0, column=0, columnspan=2)
            self.canvas = tk.Canvas( self.newWindow, width=800, height=600)

            # canvas.create_image(0, 0, image=img, anchor="nw")
            self.canvas.grid(row=1, column=0, padx=10, pady=10)

            # table2 = ttk.Treeview(newWindow2)
            self.table = CheckboxTreeview(self.newWindow)

            self.table['column'] = ('wp', 'latitude', 'longitude')

            self.table.column("wp", anchor=tk.CENTER, width=30)
            self.table.column("latitude", anchor=tk.CENTER, width=120)
            self.table.column("longitude", anchor=tk.CENTER, width=120)


            self.table.heading("wp", text="wp", anchor=tk.CENTER)
            self.table.heading("latitude", text="Latitude", anchor=tk.CENTER)
            self.table.heading("longitude", text="Longitude", anchor=tk.CENTER)

            self.table.grid(row=1, column=1, padx=10, pady=10)

            runButton = tk.Button(self.newWindow, text="Run the flight plan", width=100, bg='red', fg="white",
                                  command=self.runButtonClick)
            runButton.grid(row=2, column=0, padx=10, pady=10)

            closeButton = tk.Button(self.newWindow, text="Close", width=30, bg='red', fg="white",
                                    command=self.closeWindowToToCreateFlightPlan)
            closeButton.grid(row=2, column=1, padx=10, pady=10)

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
            self.canvas.create_image((0, 0), image=img, anchor="nw")

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

            elif self.firstPoint:
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
                self.distanceToId = self.canvas.create_text(e.x, e.y, text='0', font=("Courier", 15, 'bold'), fill='red')

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
                self.table.insert(parent='', index='end', iid=0, text='', values=('H', self.lat, self.lon))
            else:
                # the user is fixing the next waypoint
                # create the elements (line, oval, text and distance) for the new waypoint
                self.lineId = self.canvas.create_line(e.x, e.y, e.x, e.y)
                self.ovalId = self.canvas.create_oval(e.x - 10, e.y - 10, e.x + 10, e.y + 10, fill='blue')
                self.textId = self.canvas.create_text(e.x, e.y, text=str(self.wpNumber), font=("Courier", 10, 'bold'), fill='white')
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
                dist = math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2)*self.mpp
                # compute azimuth
                azimuth = math.degrees(math.atan2((self.previousx - e.x), (self.previousy - e.y))) * (-1)
                if azimuth < 0:
                    azimuth = azimuth + 360
                # compute lat,log of new waypoint
                g = self.geod.Direct(float(self.lat), float(self.lon), azimuth, dist)
                self.lat = float(g['lat2'])
                self.lon = float(g['lon2'])

                # insert new waypoint in table

                self.table.insert(parent='', index='end', iid=self.wpNumber, text='take picture?', values=(self.wpNumber, self.lat, self.lon))
                # update previouos point
                self.previousx = e.x
                self.previousy = e.y
                self.wpNumber = self.wpNumber + 1

    def drag(self,e):

        if not self.firstPoint:
            # the user is draging the mouse to decide where to place next waypoint
            dist = math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2)*self.mpp

            # show distance in the middle of the line
            self.canvas.coords(self.waypointsIds[-1]['distanceToId'], self.previousx + (e.x - self.previousx) / 2,
                          self.previousy + (e.y - self.previousy) / 2)
            self.canvas.itemconfig(self.waypointsIds[-1]['distanceToId'], text=str(round(dist, 2)))
            # Change the coordinates of the last created line to the new coordinates
            self.canvas.coords(self.waypointsIds[-1]['lineOutId'], self.previousx, self.previousy, e.x, e.y)

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
                # finds the entry in the table corresponding to the waypoint
                entry = [en for en in entries if self.table.item(en)['values'][0] == self.waypointToMoveIds['wpId']][0]

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

                # change distances
                distFrom = math.sqrt((e.x - lineInCoord[0]) ** 2 + (e.y - lineInCoord[1]) ** 2)*self.mpp
                distTo = math.sqrt((e.x - lineOutCoord[2]) ** 2 + (e.y - lineOutCoord[3]) ** 2)*self.mpp

                # this is to avoid that the text with the distance appears on top of the line
                # better a little bit displaced

                # show distance in the middle of the line
                self.canvas.coords(self.waypointToMoveIds['distanceFromId'], lineInCoord[0] + (e.x - lineInCoord[0]) / 2,
                              lineInCoord[1] + (e.y - lineInCoord[1]) / 2)
                self.canvas.itemconfig(self.waypointToMoveIds['distanceFromId'], text=str(round(distFrom, 2)))

                self.canvas.coords(self.waypointToMoveIds['distanceToId'], lineOutCoord[2] + (e.x - lineOutCoord[2]) / 2,
                              lineOutCoord[3] + (e.y - lineOutCoord[3]) / 2)
                self.canvas.itemconfig(self.waypointToMoveIds['distanceToId'], text=str(round(distTo, 2)))

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

