import streamlit as st
import json
from io import BytesIO
from utils.geocode_utils import GeocodeUtils
from utils.text_processing import FileProcessor
from streamlit_folium import st_folium
import folium
import time

geocode_utils = GeocodeUtils()
file_processor = FileProcessor()

def create_geojson(geo_info_list):
    features = []
    for info in geo_info_list:
        time.sleep(5)
        geocode_result = geocode_utils.geocode(info["address"])
        print('坐标为:', info["address"],geocode_result)
        if 'error' not in geocode_result:
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
                    "coordinates": [geocode_result["longitude"], geocode_result["latitude"]]
                }
            }
            print(feature, "点位数据")
            features.append(feature)
    return {
        "type": "FeatureCollection",
        "features": features
    }

st.title("文件上传与地理位置展示")

# 使用session_state来保存上传的文件内容和处理状态
if 'file_content' not in st.session_state:
    st.session_state.file_content = None
if 'processed' not in st.session_state:
    st.session_state.processed = False

uploaded_file = st.file_uploader("上传文件", type=["pdf", "txt"])

if uploaded_file is not None and not st.session_state.processed:
    file_content = uploaded_file.read()
    st.session_state.file_content = file_content  # 缓存文件内容
    st.session_state.processed = True  # 设置处理状态为已处理
else:
    file_content = st.session_state.file_content

if file_content and st.session_state.processed:
    file_stream = BytesIO(file_content)
    
    try:
        if uploaded_file.name.endswith('.pdf'):
            text = file_processor.extract_text_from_pdf(file_stream)
        elif uploaded_file.name.endswith('.txt'):
            text = file_processor.extract_text_from_txt(file_stream)
        else:
            st.error("Unsupported file type")
            st.stop()
        
        geo_info_list = file_processor.process_text(text)
        print(geo_info_list, "地理信息数据")
        geojson = create_geojson(geo_info_list)
        print(geojson, "geojson数据")
        # 显示GeoJSON数据
        st.json(geojson)
        
        # 在地图上显示点
        map_center = [0, 0] if not geojson["features"] else [geojson["features"][0]["geometry"]["coordinates"][1], geojson["features"][0]["geometry"]["coordinates"][0]]
        m = folium.Map(location=map_center, zoom_start=2)
        
        locations = []
        for feature in geojson["features"]:
            coords = feature["geometry"]["coordinates"]
            locations.append([coords[1], coords[0]])
            popup_content = f"""
            <b>{feature["properties"]["description"]["title"]}</b><br>
            Type: {feature["properties"]["description"]["type"]}<br>
            Content: {feature["properties"]["description"]["content"]}<br>
            Keys: {feature["properties"]["description"]["keys"]}
            """
            folium.Marker(
                location=[coords[1], coords[0]],
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(m)
        
        if len(locations) > 1:
            folium.PolyLine(locations, color="blue", weight=2.5, opacity=1).add_to(m)
        
        # 显示地图
        st_folium(m, width=700, height=500)
    except Exception as e:
        st.error(f"处理文件时发生错误: {e}")