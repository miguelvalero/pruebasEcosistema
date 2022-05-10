import threading

import paho.mqtt.client as mqtt
import time

import dronekit
from dronekit import connect
import requests
from geographiclib.geodesic import Geodesic
import json
import math


local_broker_address =  "127.0.0.1"
local_broker_port = 1883
LEDSequenceOn = False


def arm():
    """ Arms vehicle and fly to aTargetAltitude. """
    print("Basic pre-arm checks") # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)
    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = dronekit.VehicleMode("GUIDED")
    vehicle.armed = True
    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

def takeOff(aTargetAltitude):

    vehicle.simple_takeoff(aTargetAltitude)
    while True:
        print(" Altitude: ",vehicle.location.global_relative_frame.alt)
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)

def sendPosition():
    global timer
    # get the position and send it to the data service
    lat = vehicle.location.global_frame.lat
    lon = vehicle.location.global_frame.lon
    position = str(lat) + '*' + str(lon) + '*1'
    #client.publish("dataService/storePosition", position)
    client.publish("autopilotControllerAnswer/showDronePosition", position)
    # we will repeat this in 5 seconds
    timer= threading.Timer(1, sendPosition)
    timer.start()


#timer = threading.Timer(5.0, sendPosition)

def compare_location ( previous, current):
    if previous.lat == current.lat and previous.lon == current.lon:
        return True
    else:
        return False
def executeFlightPlanOld(waypoints_json):
    global vehicle
    waypoints = json.loads(waypoints_json)
    takeOff(20)
    for wp in waypoints:
        print (wp)
        print (float(wp['lat']),float(wp['lon']) )
        point = dronekit.LocationGlobalRelative(float(wp['lat']),float(wp['lon']), 20)
        vehicle.simple_goto(point)

        time.sleep(1)
        arrived = False
        previousPosition = vehicle.location.global_frame
        time.sleep(1)
        while not arrived:
            arrived = compare_location(previousPosition, vehicle.location.global_frame)
            previousPosition = vehicle.location.global_frame
            time.sleep(1)
        if wp['takePic']:
            print ('take picture')
            client.publish("cameraControllerCommand/takePicture")


    vehicle.mode = dronekit.VehicleMode("RTL")




    '''lat = vehicle.location.global_frame.lat
    lon = vehicle.location.global_frame.lon


    geod = Geodesic.WGS84

    waypoints = []
    g = geod.Direct(lat, lon, 0, 60)
    lat = float(g['lat2'])
    lon = float(g['lon2'])
    waypoints.append ((lat,lon))

    g = geod.Direct(lat, lon, 90, 60)
    lat = float(g['lat2'])
    lon = float(g['lon2'])
    waypoints.append((lat, lon))

    g = geod.Direct(lat, lon, 180, 60)
    lat = float(g['lat2'])
    lon = float(g['lon2'])
    waypoints.append((lat, lon))

    g = geod.Direct(lat, lon, 270, 60)
    lat = float(g['lat2'])
    lon = float(g['lon2'])
    waypoints.append((lat, lon))


    for wp in waypoints:
        point = dronekit.LocationGlobalRelative (wp[0],wp[1], 20)
        vehicle.simple_goto(point)

        time.sleep(1)
        arrived = False
        previousPosition = vehicle.location.global_frame
        time.sleep(1)
        while not arrived:
            arrived = compare_location(previousPosition, vehicle.location.global_frame)
            previousPosition = vehicle.location.global_frame
            time.sleep(1)
        print ("arrived")
        print ('take picture')
        client.publish("cameraControllerCommand/takePicture",payload=None, qos=0, retain=True)'''

def distanceInMeters(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

def executeFlightPlan(waypoints_json):
    global vehicle
    global timer
    waypoints = json.loads(waypoints_json)
    wp = waypoints[0]
    originPoint = dronekit.LocationGlobalRelative(float(wp['lat']), float(wp['lon']), 20)
    lat = vehicle.location.global_frame.lat
    lon = vehicle.location.global_frame.lon
    position = wp['lat'] + '*' + wp['lon'] + '*0'
    client.publish("autopilotControllerAnswer/showDronePosition", position)
    takeOff(20)
    print ('envio posicion rojo')
    position = wp['lat'] + '*' + wp['lon'] + '*1'
    client.publish("autopilotControllerAnswer/showDronePosition", position)
    distanceThreshold = 0.25
    for wp in waypoints [1:]:
        print ('siguiente wp')
        print (wp)
        print (float(wp['lat']),float(wp['lon']) )
        destinationPoint = dronekit.LocationGlobalRelative(float(wp['lat']),float(wp['lon']), 20)
        vehicle.simple_goto(destinationPoint)

        currentLocation = vehicle.location.global_frame
        dist = distanceInMeters (destinationPoint,currentLocation)

        while dist > distanceThreshold:
            time.sleep(0.25)
            currentLocation = vehicle.location.global_frame
            dist = distanceInMeters(destinationPoint, currentLocation)
        print ('arrived to waypoint')
        if wp['takePic']:
            client.publish("cameraControllerCommand/takePicture")
        position = wp['lat'] + '*' + wp['lon'] + '*1'
        client.publish("autopilotControllerAnswer/showDronePosition", position)

    vehicle.mode = dronekit.VehicleMode("RTL")

    currentLocation = vehicle.location.global_frame
    dist = distanceInMeters(originPoint, currentLocation)

    while dist > distanceThreshold:
        time.sleep(0.25)
        currentLocation = vehicle.location.global_frame
        dist = distanceInMeters(originPoint, currentLocation)
    print ('arrived to home')
    time.sleep(1)
    timer.cancel()
    wp = waypoints[0]
    position = wp['lat'] + '*' + wp['lon'] + '*0'
    client.publish("autopilotControllerAnswer/showDronePosition", position)




def on_message(client, userdata, message):
    global LEDSequenceOn
    global vehicle
    global timer
    if message.topic == 'connectPlatform':
        print ('Autopilot controller connected')
        client.subscribe('autopilotControllerCommand/+')
        connection_string = "tcp:127.0.0.1:5763"
        vehicle = connect(connection_string, wait_ready=True, baud=115200)

    if message.topic == 'autopilotControllerCommand/armDrone':
        arm ()
    if message.topic == 'autopilotControllerCommand/takeOff':
        client.publish("cameraControllerCommand/takePicture")
        altitude = float (message.payload)
        takeOff (altitude)

    if message.topic == 'autopilotControllerCommand/getDroneAltitude':
        client.publish("autopilotControllerAnswer/droneAltitude", vehicle.location.global_relative_frame.alt)

    if message.topic == 'autopilotControllerCommand/getDroneHeading':
        client.publish("autopilotControllerAnswer/droneHeading" ,vehicle.heading)

    if message.topic == 'autopilotControllerCommand/getDroneGroundSpeed':
        client.publish("autopilotControllerAnswer/droneGroundSpeed", vehicle.groundspeed)

    if message.topic == 'autopilotControllerCommand/getDronePosition':

        lat = vehicle.location.global_frame.lat
        lon = vehicle.location.global_frame.lon

        position = str(lat) + '*' + str(lon)
        client.publish("autopilotControllerAnswer/dronePosition", position)

    if message.topic == 'autopilotControllerCommand/goToPosition':
        positionStr = str(message.payload.decode("utf-8"))
        position = positionStr.split ('*')
        lat = float (position[0])
        lon = float (position[1])
        point = dronekit.LocationGlobalRelative(lat, lon, 20)
        vehicle.simple_goto(point)
        # we start a procedure to get the drone position every 5 seconds
        # and send it to the data service (to be stored there)
        timer = threading.Timer(2, sendPosition)
        sendPosition()

    if message.topic == 'autopilotControllerCommand/returnToLaunch':
        # stop the process of getting positions
        timer.cancel()
        vehicle.mode = dronekit.VehicleMode("RTL")

    if message.topic == 'autopilotControllerCommand/disarmDrone':
        vehicle.armed = True

    if message.topic == 'autopilotControllerCommand/executeFlightPlan':
        waypoints_json = str(message.payload.decode("utf-8"))
        print ('Paso 1')
        print (waypoints_json)
        w = threading.Thread(target=executeFlightPlan, args=[waypoints_json])
        w.start()
        timer = threading.Timer(0.5, sendPosition)
        sendPosition()


client = mqtt.Client("Autopilot controller")
client.on_message = on_message
client.connect(local_broker_address, local_broker_port)
client.loop_start()
print ('Waiting DASH connection ....')
client.subscribe('connectPlatform')

