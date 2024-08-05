import streamlit as st
import os
from io import BytesIO
from utils.geocode_utils import GeocodeUtils
from utils.text_processing import FileProcessor
from utils.model_back import ModelBack
from utils.map import Map
from utils.rag import RAG

def upload_and_process_file(llm,rag,processing_info,row1_col1,row1_col2,row2):
    uploaded_file = st.sidebar.file_uploader("上传文件", type=["pdf", "txt"])
    # 确保 data 文件夹存在
    data_dir = './data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if uploaded_file is not None:
        if uploaded_file != st.session_state.uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.processed = False
            st.session_state.file_changed = True
            st.session_state.geo_info_list = []  # 重置geo_info_list
            st.session_state.processed_event_ids = [] # 事件ID列表
            # 获取文件名
            file_name = uploaded_file.name
            
            # 构建保存路径
            save_path = os.path.join(data_dir, file_name)
            
            # 将文件内容写入到指定位置
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            with row1_col1:
                st.success(f"文件已保存到: {save_path}")

        else:
            st.session_state.file_changed = False

        if st.session_state.isRAG and not st.session_state.RAGed:
                rag.build_index_from_file()
                st.session_state.RAGed = True
                with row2:
                    st.success("RAG索引已构建")

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
            if llm and not st.session_state.processed:
                geo_info_list = st.session_state.geo_info_list
                geocode_utils = GeocodeUtils(api_type=st.session_state.geocode_type, baidu_key=st.session_state.baidu_key, user_agent=st.session_state.username)
                with row1_col1:
                    processing_info.info("正在处理文件，请稍候...")
                
                for text in text_list:
                    processed_event_ids = []
                    event_list = llm.get_event_list(text)
                    if event_list:
                        for i, event in enumerate(event_list):
                            event_id = i  # 假设event对象有一个唯一的id属性
                            if event_id is None:
                                st.warning("事件缺少唯一标识符")
                                continue
                            
                            print(f"这是第 {i} 事件，ID: {event_id}")
                            try:
                                if event_id not in processed_event_ids:

                                    event_info = llm.process_event(event, language="英文")
                                    print(event_info)
                                    address = event_info["address"]
                                    print(address,"地址")
                                    geocode_info = geocode_utils.geocode(address)
                                    print(geocode_info,"地理编码")
                                    if geocode_info:
                                        event_info["geocode"] = geocode_info
                                        processed_event_ids.append(event_id)  # 添加到已处理事件的集合中
                                    else:
                                        continue 
                            except Exception as e:
                                print(f"处理事件时出错: {e}")
                                continue
                            event_info["geocode"] = geocode_info
                            processed_event_ids.append(event_id)
                            geo_info_list.append(event_info)
                            if event_info:
                                display_event_info(event_info,row1_col1)
                
                processing_info.empty()  # 清空处理信息
                st.session_state.geo_info_list = geo_info_list  # 保存更新后的geo_info_list
                st.session_state.processed = True
                with row1_col1:
                    st.success("文件处理完成")
        


                
def display_event_info(event_info,row1_col1):
    with row1_col1:
        truncated_title = event_info["event_title"] if len(event_info["event_title"]) <= 6 else event_info["event_title"][:6] + "..."
        with st.expander(truncated_title):
            st.json(event_info)  # 以JSON格式显示事件详细信息
                
def update_map(m):
    geo_info_list = st.session_state.geo_info_list
    if len(geo_info_list) > 0:
        for idx, info in enumerate(geo_info_list):
            geo_info = info["geocode"]
            m.add_marker(info, geo_info)
    else:
        pass
    # 导出按钮
    if len(geo_info_list) > 0:
        st.sidebar.markdown("### 数据导出")
        export_geojson = st.sidebar.button("导出 GeoJSON")
        # export_shp = st.sidebar.button("导出 SHP")

        if export_geojson:
            b = m.export_geojson()
            st.sidebar.download_button(
                label="下载 GeoJSON",
                data=b,
                file_name="data.geojson",
                mime="application/json"
            )
            
        # if export_shp:
        #     b = m.export_shp(crs_type="WGS-84")
        #     st.sidebar.download_button(
        #         label="下载 SHP",
        #         data=b,
        #         file_name="data.zip",
        #         mime="application/zip"
        #     )

def output(chat_container,placeholder,response):
    with chat_container:
            placeholder.markdown(response + "▌")

def toggle_isRAG():
    st.session_state.isRAG = not st.session_state.isRAG

def toggle_isSmartMap():
    st.session_state.isSmartMap = not st.session_state.isSmartMap


# 设置页面布局为宽屏模式
st.set_page_config(layout="wide")

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
if 'model_type' not in st.session_state:
    st.session_state.model_type = "deepseek"
# 初始化会话状态
if 'isRAG' not in st.session_state:
    st.session_state.isRAG = False
if 'isSmartMap' not in st.session_state:
    st.session_state.isSmartMap = False
if 'RAGed' not in st.session_state:
    st.session_state.RAGed = False

def main():
    st.session_state.map = Map() # 地图类实例化
    llm = ModelBack(api_key=st.session_state.api_key, model_type=st.session_state.model_type) # 模型初始化
    rag = RAG(api_key=st.session_state.api_key, model_type=st.session_state.model_type) # RAG模型初始化
    # 地图布局
    st.title("AI-MapBook")

    tab1, tab2 = st.sidebar.tabs(["应用设置", "项目介绍"])
    with tab1:
        # 对话框和内容生成框

        st.session_state.model_type = st.sidebar.selectbox("选择模型类型(云端勿选ipex_llm)", ["deepseek","ipex_llm"], index=0)
        if st.session_state.model_type == "deepseek":
            st.session_state.api_key = st.sidebar.text_input("请输入deepseek_key", value=st.session_state.api_key, key="api_key_input")


        st.session_state.geocode_type = st.sidebar.selectbox("地理编码类型", ["free", "baidu"], index=0)
        if st.session_state.geocode_type == "baidu":
            st.session_state.baidu_key = st.sidebar.text_input("百度地图API", value=st.session_state.baidu_key, key="baidu_key_input")
        else:
            st.session_state.username = st.sidebar.text_input("请输入用户名", value=st.session_state.username, key="username_input")


    with tab2:
        st.markdown(
            '''
            ## AI-MapBook 项目介绍

            **AI-MapBook** 是一个利用大型语言模型（LLM）技术为故事讲述提供地图支持的项目。它通过LLM从书籍中提取地理信息和属性信息，结合地理编码得到地理坐标数据，并在交互式地图上进行可视化展示，为读者提供沉浸式的故事探索体验。

            该项目适用于故事创作者、教育工作者和地图爱好者，通过结合人工智能和地理空间技术，增强叙事效果。

            - **技术特点**：
                - 利用LLM提取地理信息和属性信息
                - 结合地理编码得到地理坐标数据
                - 在交互式地图上进行可视化展示

            - **应用场景**：
                - 故事创作者
                - 教育工作者
                - 地图爱好者
            
            - **项目地址**： [ModelBack-MapBook](https://github.com/qianyouliang/AI-MapBook)

            ## 联系方式

            - **GitHub**: [qianyouliang](https://github.com/qianyouliang)
            - **兴趣领域**: GIS, RS, GNSS, AI
            - **当前学习**: GIS, AI
            - **合作意向**: GIS, 遥感, AI
            - **电子邮件**: [qianyouliang123@gmail.com](mailto:qianyouliang123@gmail.com)
            - **CSDN博客**: [CSDN](https://blog.csdn.net/qq_45590504)
            ''' 
        )

    # 初始化列布局
    # 第一行布局
    container = st.container(border=True, height=1080)
    with container:
        row1 = st.container(border=True, height=600)
                # 第二行布局
        row2 = st.container(border=True, height=480)
        with row1:
            row1_col1, row1_col2 = st.columns([3, 7])
            with row1_col1:
                st.markdown("#### 事件列表")
                processing_info = st.empty()
            
            with row1_col2:
                st.markdown("#### 地图")
                st.markdown("""
                <style>
                .st-emotion-cache-veb430{
                overflow:hidden !important;
                }
                .st-emotion-cache-1m6pjz2{
                overflow:hidden !important;
                }
                </style>
            """, unsafe_allow_html=True)
                m = st.session_state.map
                if m:
                    tiles_options = m.tiles_options
                    selected_tile_name = st.selectbox("选择地图底图", list(tiles_options.keys()), index=0)
                    selected_tile = tiles_options[selected_tile_name]
                    m.init_map(selected_tile=selected_tile)
                    update_map(m)
                    m.add_polyline()
                    m.display()

        with row2:
            # 创建一个容器来存放聊天记录
            chat_container = st.container(height=440)

            # 在聊天容器中显示聊天记录
            with chat_container:
                st.markdown("#### MapAgent")
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []

                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
            
                # 添加多选框
                # 添加复选框分组
                st.checkbox("RAG", value=st.session_state.isRAG, help="启用RAG功能", key="RAG_checkbox", on_change=lambda: toggle_isRAG())
                # st.checkbox("智能地图", value=st.session_state.isSmartMap, help="启用智能地图功能", key="smartMap_checkbox", on_change=lambda: toggle_isSmartMap())

                prompt = st.chat_input("你想聊点什么?")

                if prompt:
                    print(st.session_state.isRAG,st.session_state.RAGed,"888")
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    if st.session_state.isRAG and st.session_state.RAGed:
                        query = rag.query_index(prompt)
                        prompt = f'''
                            辅助信息：{query};
                            ___________________
                            用户问题：{prompt};
                        '''
                    st.session_state.chat_history.append({"role": "user", "content": prompt})

                    response = str()
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        streamer = llm.chat(st.session_state.chat_history, placeholder)
                        if st.session_state.model_type == 'ipex_llm':
                            for text in streamer:
                                response += text
                                # 更新聊天记录
                                with chat_container:
                                    placeholder.markdown(response + "▌")

                        elif st.session_state.model_type == 'deepseek':
                            for text in streamer:
                                response += text.choices[0].delta.content
                                output(chat_container, placeholder, response)
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

    upload_and_process_file(llm, rag, processing_info, row1_col1, row1_col2,row2)

# 添加CSS样式以实现事件名称字符限制和悬停显示
st.markdown("""
    <style>
    .main {
    height:100%;
    overflow-y: hidden !important;
    }
    .block-container{
        padding:1vh 1vw !important;
        overflow: hidden; /* 隐藏滚动条 */
        
    }
    body {
        height:100vh;
        overflow: hidden; /* 隐藏滚动条 */
    }
    #map_div {
        width: 100% !important;
        height:50% !important;
        
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
    .fixed-sidebar {
        position: fixed;
        top: 0;
        left: 0;
        width: 20%;
        height: 100%;
        overflow-y: auto;
        overflow: hidden; /* 隐藏滚动条 */
    }
    .fixed-content {
        margin-left: 20%;
        width: 80%;
        height: 100%;
        overflow-y: auto;
    }
    .st-emotion-cache-1bcsrn5{
        height:50vh !important;
    }
    .st-emotion-cache-1lx0qav{
        position:absolutely !important;
        bottom:0 !important;
        left:50% !important;
        transform:translateX(-50%);
    }
    .stChatInput{
        position:fixed !important;
        bottom:5%;
        box-shadow:2px 2px 4px black !important;
        background-color:white !important;
    }
    textarea{
        color:#000 !important;
    }
    .st-emotion-cache-3sz198,.st-emotion-cache-1ucia2i{
        overflow:hidden !important;
    }
    .st-emotion-cache-gs4sfp{
        overflow:hidden !important;
    }
    .st-emotion-cache-1bzkvni{
        overflow:scroll;
    }
    .st-emotion-cache-13511py>.stCheckbox{
        display:flex;
        align-item:center;
        position:fixed;
        bottom:25%;
        right:5%;
        width:100px !important;
        z-index:999;
    }
    
    </style>
""", unsafe_allow_html=True)


main()
