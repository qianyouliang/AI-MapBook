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
    st.session_state.username = "GISerLiu"
if 'api_key' not in st.session_state:
    st.session_state.api_key = "your deepseek api key"

st.session_state.username = st.sidebar.text_input("请输入用户名", value=st.session_state.username, key="username_input")
st.session_state.api_key = st.sidebar.text_input("请输入deepseek_api_key", value=st.session_state.api_key, key="api_key_input")

# 实例化geocode_utils和file_processor
geocode_utils = GeocodeUtils(user_agent=st.session_state.username)
file_processor = FileProcessor(api_key=st.session_state.api_key)

def create_geojson(geo_info_list, m):
    features = []
    locations = []
    with st.spinner("正在处理地理信息，请稍候..."):
        for info in geo_info_list:
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
                locations.append([geocode_result["latitude"], geocode_result["longitude"]])
                popup_content = f"""
                <b>{feature["properties"]["description"]["title"]}</b><br>
                Type: {feature["properties"]["description"]["type"]}<br>
                Content: {feature["properties"]["description"]["content"]}<br>
                Keys: {feature["properties"]["description"]["keys"]}
                """
                folium.Marker(
                    location=[geocode_result["latitude"], geocode_result["longitude"]],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color='red')
                ).add_to(m)
            if len(locations) > 1:
                folium.PolyLine(locations, color="blue", weight=2.5, opacity=1).add_to(m)
            print(feature, "点位数据")
            features.append(feature)
    return {
        "type": "FeatureCollection",
        "features": features
    }

def upload_and_process_file():
    uploaded_file = st.sidebar.file_uploader("上传文件", type=["pdf", "txt"])
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        file_stream = BytesIO(file_content)
        if uploaded_file.name.endswith('.pdf'):
            text = file_processor.extract_text_from_pdf(file_stream)
        elif uploaded_file.name.endswith('.txt'):
            text = file_processor.extract_text_from_txt(file_stream)
        else:
            st.error("Unsupported file type")
            return None
        geo_info_list = file_processor.process_text(text)
        return geo_info_list
    return None

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
if 'map_instance' not in st.session_state:
    st.session_state.map_instance = None

geo_info_list = upload_and_process_file()

if geo_info_list:
    st.session_state.geo_info_list = geo_info_list
    st.session_state.processed = True

if st.session_state.processed:
    # 切分布局，左侧显示列表和按钮，右侧显示地图
    col1, col2 = st.columns([1, 3])

    with col1:
        # 使用Markdown来控制header的大小
        st.markdown("#### 事件列表")  # 这将创建一个较小的header

        for idx, info in enumerate(st.session_state.geo_info_list):
            truncated_title = info["event_title"] if len(info["event_title"]) <= 6 else info["event_title"][:6] + "..."
            # 添加一个展开器来显示详细信息
            with st.expander(truncated_title):
                st.session_state.selected_info = info
                st.session_state.selected_coords = info["address"]
                st.json(info)  # 显示事件的详细信息，以JSON格式
    with col2:
        # 地图默认显示
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

        if st.session_state.map_instance is None:
            map_center = [0, 0]
            m = folium.Map(location=map_center, zoom_start=2, tiles=selected_tile, attr=selected_tile_name)
            folium.LayerControl().add_to(m)
            st.session_state.map_instance = m
        else:
            m = st.session_state.map_instance
            m.tiles = selected_tile
            m.attr = selected_tile_name

        # 创建并更新地图
        if not st.session_state.get('geojson_created', False):
            print("我又开始创建了")
            geojson = create_geojson(st.session_state.geo_info_list, m)
            print(geojson, "geojson数据")
            st.session_state.geojson_created = True

        st_folium(m, width=700, height=700)

        if st.session_state.selected_info:
            st.subheader("选中的事件")
            st.write(st.session_state.selected_info)

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