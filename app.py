import streamlit as st
import json
from io import BytesIO
from utils.geocode_utils import GeocodeUtils
from utils.text_processing import FileProcessor
from utils.ModelBack import LLM
from utils.map import Map
from streamlit_folium import st_folium
import folium

def upload_and_process_file(processing_info):
    uploaded_file = st.sidebar.file_uploader("上传文件", type=["pdf", "txt"])
    if uploaded_file is not None and st.session_state.processed != True:
        if uploaded_file != st.session_state.uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.processed = False
            st.session_state.file_changed = True
            st.session_state.geo_info_list = []  # 重置geo_info_list
        else:
            st.session_state.file_changed = False
        
        if not st.session_state.processed:
            file_processor = FileProcessor()
            file_content = uploaded_file.read()
            file_stream = BytesIO(file_content)
            if uploaded_file.name.endswith('.pdf'):
                text_list = file_processor.extract_text_from_pdf(file_stream)
            elif uploaded_file.name.endswith('.txt'):
                text_list = file_processor.extract_text_from_txt(file_stream)
            else:
                st.error("不支持的文件类型")
            
            geo_info_list = st.session_state.geo_info_list  # 使用现有的geo_info_list
            processed_event_ids = set()
            
            if len(st.session_state.api_key) > 0:
                geocode_utils = GeocodeUtils(api_type=st.session_state.geocode_type, baidu_key=st.session_state.baidu_key, user_agent=st.session_state.username)
                llm = LLM(api_key=st.session_state.api_key)
                with col1:
                    processing_info.info("正在处理文件，请稍候...")
                
                for text in text_list:
                    event_list = llm.get_event_list(text)
                    if event_list:
                        for i, event in enumerate(event_list):
                            event_id = i  # 假设event对象有一个唯一的id属性
                            if event_id is None:
                                st.warning("事件缺少唯一标识符")
                                continue
                            
                            print(f"这是第 {i} 件事件，ID: {event_id}")
                            try:
                                if event_id not in processed_event_ids:
                                    event_info = llm.process_event(event, language="英文")
                                    address = event_info["address"]
                                    print(f"这是事件的数量: {len(event_list)}")
                                    geocode_info = geocode_utils.geocode(address)
                                    print(geocode_info)
                            except Exception as e:
                                print(f"处理事件时出错: {e}")
                                continue
                            event_info["geocode"] = geocode_info
                            processed_event_ids.add(event_id)
                            geo_info_list.append(event_info)
                            display_event_info(event_info)
                
                processing_info.empty()  # 清空处理信息
                st.session_state.geo_info_list = geo_info_list  # 保存更新后的geo_info_list
                st.session_state.processed = True
                st.success("文件处理完成")
                
def display_event_info(event_info):
    with col1:
        truncated_title = event_info["event_title"] if len(event_info["event_title"]) <= 6 else event_info["event_title"][:6] + "..."
        with st.expander(truncated_title):
            st.json(event_info)  # 以JSON格式显示事件详细信息
                
def update_map(m):
    geo_info_list = st.session_state.geo_info_list
    if len(geo_info_list) > 0:
        for idx, info in enumerate(geo_info_list):
            geo_info = info["geocode"]
            m.add_marker(info, geo_info)
        print(m.locations)
    else:
        pass
    # 导出按钮
    if len(geo_info_list) > 0:
        st.sidebar.markdown("### 数据导出")
        export_geojson = st.sidebar.button("导出 GeoJSON")
        export_shp = st.sidebar.button("导出 SHP")

        if export_geojson:
            b = m.export_geojson()
            st.sidebar.download_button(
                label="下载 GeoJSON",
                data=b,
                file_name="data.geojson",
                mime="application/json"
            )
            
        if export_shp:
            b = m.export_shp(crs_type="WGS-84")
            st.sidebar.download_button(
                label="下载 SHP",
                data=b,
                file_name="data.zip",
                mime="application/zip"
            )

# 使用session_state来保存状态
if 'username' not in st.session_state:
    st.session_state.username = "GISerLiu"
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'baidu_key' not in st.session_state:
    st.session_state.baidu_key = ""
if 'geocode_type' not in st.session_state:
    st.session_state.geocode_type = "free"
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'file_changed' not in st.session_state:
    st.session_state.file_changed = False
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'geo_info_list' not in st.session_state:
    st.session_state.geo_info_list = []
if 'selected_info' not in st.session_state:
    st.session_state.selected_info = None

st.session_state.geocode_type = st.sidebar.selectbox("地理编码类型", ["free", "baidu"], index=0)
if st.session_state.geocode_type == "baidu":
    st.session_state.baidu_key = st.sidebar.text_input("百度地图API", value=st.session_state.baidu_key, key="baidu_key_input")
else:
    st.session_state.username = st.sidebar.text_input("请输入用户名", value=st.session_state.username, key="username_input")

st.session_state.api_key = st.sidebar.text_input("请输入deepseek_key", value=st.session_state.api_key, key="api_key_input")

# 地图布局
st.title("LLM-MapBook")

# 初始化列布局
col1, col2 = st.columns([3, 8])

def main():
    st.session_state.map = Map()
    m = st.session_state.map
    with col1:
        st.markdown("#### 事件列表")  # 创建较小的标题
        processing_info = st.empty()
    upload_and_process_file(processing_info)
    with col2:
        if m:
            tiles_options = m.tiles_options
            selected_tile_name = st.selectbox("选择地图底图", list(tiles_options.keys()), index=0)
            selected_tile = tiles_options[selected_tile_name]
            m.init_map(selected_tile=selected_tile)
            update_map(m)
            m.add_polyline()
            m.display()
    
    
# 添加CSS样式以实现事件名称字符限制和悬停显示
st.markdown("""
    <style>
    .main{
        overflow-y:hidden !important;
    }
    body {
        overflow: hidden; /* 隐藏滚动条 */
    }
    #map_div{
        width:100% !important;
    }
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

main()
