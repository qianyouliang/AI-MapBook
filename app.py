import streamlit as st
import json
from io import BytesIO
from utils.geocode_utils import GeocodeUtils
from utils.text_processing import FileProcessor
from streamlit_folium import st_folium
import folium
import time

# 使用session_state来保存用户名
if 'username' not in st.session_state:
    st.session_state.username = "qianyouliang"

st.session_state.username = st.sidebar.text_input("请输入用户名", value=st.session_state.username, key="username_input")

# 实例化geocode_utils和file_processor
geocode_utils = GeocodeUtils(user_agent=st.session_state.username)
file_processor = FileProcessor()

def create_geojson(geo_info_list):
    features = []
    for info in geo_info_list:
        time.sleep(3)
        geocode_result = geocode_utils.geocode(info["address"])
        print('坐标为:', info["address"], geocode_result)
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
            # 更新地图
            update_map(feature)
    return {
        "type": "FeatureCollection",
        "features": features
    }

def update_map(feature):
    # 动态更新地图
    coords = feature["geometry"]["coordinates"]
    color = get_marker_color(feature["properties"]["description"]["type"])
    popup_content = f"""
    <b>{feature["properties"]["description"]["title"]}</b><br>
    Type: {feature["properties"]["description"]["type"]}<br>
    Content: {feature["properties"]["description"]["content"]}<br>
    Keys: {feature["properties"]["description"]["keys"]}
    """
    folium.Marker(
        location=[coords[1], coords[0]],
        popup=folium.Popup(popup_content, max_width=300),
        icon=folium.Icon(color=color)
    ).add_to(m)
    map_placeholder.empty()
    map_placeholder.write(st_folium(m, width=700, height=500))

def get_marker_color(event_type):
    color_dict = {
        "Type1": "red",
        "Type2": "blue",
        "Type3": "green",
        "Type4": "purple"
    }
    return color_dict.get(event_type, "gray")

st.title("LLM-MapBook")

# 使用session_state来保存上传的文件内容和处理状态
if 'file_content' not in st.session_state:
    st.session_state.file_content = None
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'geo_info_list' not in st.session_state:
    st.session_state.geo_info_list = []
if 'selected_info' not in st.session_state:
    st.session_state.selected_info = None

uploaded_file = st.sidebar.file_uploader("上传文件", type=["pdf", "txt"])

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
        st.session_state.geo_info_list = geo_info_list
        print(geo_info_list, "地理信息数据")
        
        # 使用下拉抽屉显示GeoJSON数据
        with st.expander("显示事件JSON数据"):
            st.json(geo_info_list)

        st.write("请检查并编辑地理信息数据，然后点击下方按钮展示地图")

        # 编辑地理信息数据
        edited_geo_info_list = []
        for idx, info in enumerate(st.session_state.geo_info_list):
            with st.expander(f"事件 {idx + 1}"):
                event_title = st.text_input(f"事件标题 {idx + 1}", value=info["event_title"])
                event_type = st.text_input(f"事件类型 {idx + 1}", value=info["event_type"])
                event_content = st.text_area(f"事件内容 {idx + 1}", value=info["event_content"])
                keys = st.text_input(f"事件关键词 {idx + 1}", value=info["keys"])
                address = st.text_input(f"事件地址 {idx + 1}", value=info["address"])
                
                edited_info = {
                    "event_title": event_title,
                    "event_type": event_type,
                    "event_content": event_content,
                    "keys": keys,
                    "address": address
                }
                edited_geo_info_list.append(edited_info)

        st.session_state.geo_info_list = edited_geo_info_list
        
        map_placeholder = st.empty()

        if st.button("展示地图"):
            geojson = create_geojson(st.session_state.geo_info_list)
            print(geojson, "geojson数据")
            
            # 切分布局，左侧显示列表和按钮，右侧显示地图
            col1, col2 = st.columns([1, 3])

            with col1:
                st.header("事件列表")
                for idx, info in enumerate(st.session_state.geo_info_list):
                    truncated_title = info["event_title"] if len(info["event_title"]) <= 6 else info["event_title"][:6] + "..."
                    if st.button(truncated_title, key=idx, help=info["event_title"]):
                        st.session_state.selected_info = info
                        st.session_state.selected_coords = info["address"]

            with col2:
                # 地图底图选择框
                tiles_options = {
                    "OpenStreetMap": "OpenStreetMap",
                    "Stamen Terrain": "Stamen Terrain",
                    "Stamen Toner": "Stamen Toner",
                    "Stamen Watercolor": "Stamen Watercolor",
                    "CartoDB positron": "CartoDB positron",
                    "CartoDB dark_matter": "CartoDB dark_matter",
                    "Google Satellite": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
                }
                selected_tile_name = st.selectbox("选择地图底图", list(tiles_options.keys()), index=0)
                selected_tile = tiles_options[selected_tile_name]
                
                # 显示地图
                map_center = [0, 0] if not geojson["features"] else [geojson["features"][0]["geometry"]["coordinates"][1], geojson["features"][0]["geometry"]["coordinates"][0]]
                m = folium.Map(location=map_center, zoom_start=2, tiles=selected_tile, attr=selected_tile_name)
                
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
                    # color = get_marker_color(feature["properties"]["description"]["type"])
                    folium.Marker(
                        location=[coords[1], coords[0]],
                        popup=folium.Popup(popup_content, max_width=300),
                        icon=folium.Icon(color='red')
                    ).add_to(m)
                
                if len(locations) > 1:
                    folium.PolyLine(locations, color="blue", weight=2.5, opacity=1).add_to(m)
                
                folium.LayerControl().add_to(m)
                folium.LatLngPopup().add_to(m)
                
                st_folium(m, width=700, height=500)
                
                if st.session_state.selected_info:
                    st.subheader("选中的事件")
                    st.write(st.session_state.selected_info)

    except Exception as e:
        st.error(f"处理文件时发生错误: {e}")

# 添加CSS样式以实现事件名称字符限制和悬停显示
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }
    .stButton button:hover {
        overflow: visible;
        white-space: normal;
    }
    </style>
""", unsafe_allow_html=True)
