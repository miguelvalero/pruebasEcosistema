import os
import webbrowser

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

async def convert():
    browser = await launch(headless=True)
    page = await browser.newPage()
    path = 'file://' + os.path.realpath('map.html')
    await page.goto(path)
    await page.screenshot({'path': 'map.png', 'fullPage': True})
    await browser.close()


token = "pk.eyJ1IjoibWlndWVsdmFsZXJvIiwiYSI6ImNsMjk3MGk0MDBnaGEzdG1tbGFjbWRmM2MifQ.JZZ6tJwPN28fo3ldg37liA"  # your mapbox token
tileurl = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(token)

my_map = folium.Map(
    location=[41.2750992, 1.9874898], max_zoom=19, zoom_start=19, tiles=tileurl, attr='Mapbox',
    control_scale=True)

my_map.save("map.html")
webbrowser.open("map.html")
asyncio.get_event_loop().run_until_complete(convert())