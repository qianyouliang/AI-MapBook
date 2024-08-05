import folium
import streamlit as st
from streamlit_folium import st_folium
from shapely.geometry import Point, LineString
import geopandas as gpd
import json
from io import BytesIO
import math

class Map:
    def __init__(self):
        self.tiles_options = {
            "OpenStreetMap": "OpenStreetMap",
            # "Stamen Terrain": "Stamen Terrain",
            # "Stamen Toner": "Stamen Toner",
            # "Stamen Watercolor": "Stamen Watercolor",
            "CartoDB positron": "CartoDB positron",
            "CartoDB dark_matter": "CartoDB dark_matter",
            # "Google Satellite": 'https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            # "高德地图":"http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}",
            # "腾讯地图":"http://rt{s}.map.gtimg.com/realtimerender?z={z}&x={x}&y={y}&type=vector&style=0",
        }
        self.map = None
        self.features = []
        self.locations = []
        

    def init_map(self, selected_tile):
        map_center = [0, 0]
        if selected_tile in self.tiles_options:
            # if selected_tile in ["高德地图", "腾讯地图"]:
            #     self.map = folium.Map(location=map_center, zoom_start=2)
            #     folium.TileLayer(tiles=self.tiles_options[selected_tile], attr=selected_tile).add_to(self.map)
            # else:
                self.map = folium.Map(location=map_center, zoom_start=2, tiles=self.tiles_options[selected_tile],attr = 'default',width=1200,
                height=400)
                # folium.LayerControl().add_to(self.map)
        else:
            print(f"Tile option {selected_tile} not found.")
        return self.map

    def add_marker(self, info, coordinates):
        try:
            feature = {
                "type": "Feature",
                "properties": {
                    "description": {
                        "title": info["event_title"],
                        "type": info["event_type"],
                        "content": info["event_content"],
                        "keys": info["keys"],
                    }
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [coordinates["longitude"], coordinates["latitude"]]
                }
            }
            self.locations.append([coordinates["latitude"], coordinates["longitude"]])
            popup_content = f"""
            <div style="max-height: 200px; overflow-y: auto; font-size: 16px; line-height: 1.5;">
            <b>{feature["properties"]["description"]["title"]}</b><br>
            <strong>事件类型</strong>: {feature["properties"]["description"]["type"]}<br>
            <strong>内容</strong>: {feature["properties"]["description"]["content"]}<br>
            <strong>关键词</strong>:: {feature["properties"]["description"]["keys"]}
            </div>
            """
            folium.Marker(
                location=[coordinates["latitude"], coordinates["longitude"]],
                popup=folium.Popup(popup_content, max_width=400),
                icon=folium.Icon(color='red')
            ).add_to(self.map)
            self.locations.append([coordinates["latitude"], coordinates["longitude"]])
            self.features.append(feature)
        except Exception as exc:
            print(f"Error adding marker: {exc}")

    def add_polyline(self, color="blue", weight=2.5, opacity=1, arrow=True):
        # folium.PolyLine(self.locations, color=color, weight=weight, opacity=opacity).add_to(self.map)
        if len(self.locations) > 1:
            folium.PolyLine(self.locations, color=color, weight=weight, opacity=opacity).add_to(self.map)

            if arrow:
                for i in range(len(self.locations) - 1):
                    dx = self.locations[i + 1][0] - self.locations[i][0]
                    dy = self.locations[i + 1][1] - self.locations[i][1]
                    angle = -int(math.atan2(dx, dy) * 180 / math.pi)

                    mid_location = [
                        (self.locations[i][0] + self.locations[i + 1][0]) / 2,
                        (self.locations[i][1] + self.locations[i + 1][1]) / 2
                    ]

                    folium.RegularPolygonMarker(
                        location=mid_location,
                        fill_color=color,
                        number_of_sides=3,
                        radius=5,
                        rotation=angle
                    ).add_to(self.map)


    def display(self, width=1200, height=400):
        if self.map is not None:
            st_folium(self.map, width=width, height=height)
        else:
            st.warning("Map is not initialized.")

    def fly_to(self, latitude, longitude, zoom_level=12):
        if self.map is not None:
            self.map.location = [latitude, longitude]
            self.map.zoom_start = zoom_level
        else:
            st.warning("Map is not initialized.")

    def export_geojson(self):
        geojson_data = {
            "type": "FeatureCollection",
            "features": self.features
        }
        geojson_str = json.dumps(geojson_data, indent=2, ensure_ascii=False)  # 确保非 ASCII 字符不被转义
        b = BytesIO()
        b.write(geojson_str.encode('utf-8'))
        b.seek(0)
        return b
