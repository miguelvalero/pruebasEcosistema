import folium
import webbrowser
from folium.plugins import MousePosition

token = "pk.eyJ1IjoibWlndWVsdmFsZXJvIiwiYSI6ImNsMjk3MGk0MDBnaGEzdG1tbGFjbWRmM2MifQ.JZZ6tJwPN28fo3ldg37liA"  # your mapbox token
tileurl = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(token)

my_map = folium.Map(
    location=[41.2750992, 1.9874898], max_zoom=19, zoom_start=19, tiles=tileurl, attr='Mapbox', control_scale=True)

folium.Marker(
    location=[41.275782, 1.987562],
    popup="G",
    icon=folium.Icon(color="red"),
    draggable=True
).add_to(my_map)


formatter = 'function(num) {return L.Util.formatNum(num, 3);};'

MousePosition(
    position="topright",
    separator=" | ",
    empty_string="NaN",
    lng_first=True,
    num_digits=20,
    prefix="Coordinates:",
    lat_formatter=formatter,
    lng_formatter=formatter,
).add_to(my_map)

my_map.add_child(folium.ClickForMarker(popup="Waypoint"))

my_map.add_child(folium.LatLngPopup())
my_map.save("map.html")

webbrowser.open("map.html")
