"""
UI 工具模块
AI-MapBook 界面优化组件
"""
import streamlit as st
from typing import Optional, Callable


def init_page_config(config):
    """初始化页面配置"""
    st.set_page_config(
        page_title=config.ui.page_title,
        page_icon=config.ui.page_icon,
        layout=config.ui.layout,
    )


def apply_custom_css(config, hide_default_scripts: bool = True):
    """应用自定义CSS样式"""
    css = f"""
    <style>
    /* 主容器样式 */
    .main {{
        height: 100%;
        overflow-y: hidden !important;
    }}
    
    /* 页面容器 */
    .block-container {{
        padding: 1vh 1vw !important;
        overflow: hidden;
    }}
    
    /* 隐藏滚动条 */
    body {{
        height: 100vh;
        overflow: hidden;
    }}
    
    /* 地图容器 */
    #map_div {{
        width: 100% !important;
        height: 50% !important;
    }}
    
    /* 按钮样式 */
    .stButton button {{
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }}
    .stButton button:hover {{
        overflow: visible;
        white-space: normal;
    }}
    
    /* 侧边栏固定 */
    .fixed-sidebar {{
        position: fixed;
        top: 0;
        left: 0;
        width: {config.ui.sidebar_width}px;
        height: 100%;
        overflow-y: auto;
    }}
    
    /* 内容区域 */
    .fixed-content {{
        margin-left: {config.ui.sidebar_width}px;
        width: calc(100% - {config.ui.sidebar_width}px);
        height: 100%;
        overflow-y: auto;
    }}
    
    /* 输入框样式 */
    textarea {{
        color: #000 !important;
    }}
    
    /* 聊天输入框固定底部 */
    .stChatInput {{
        position: fixed !important;
        bottom: 5%;
        box-shadow: 2px 2px 4px black !important;
        background-color: white !important;
    }}
    
    /* 事件列表样式 */
    .event-item {{
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        background-color: #f0f2f6;
    }}
    
    /* 加载动画 */
    .loading-spinner {{
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-radius: 50%;
        border-top: 3px solid {config.ui.primary_color};
        animation: spin 1s linear infinite;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    /* 成功提示 */
    .success-message {{
        padding: 10px;
        background-color: #d4edda;
        border-radius: 5px;
        color: #155724;
    }}
    
    /* 错误提示 */
    .error-message {{
        padding: 10px;
        background-color: #f8d7da;
        border-radius: 5px;
        color: #721c24;
    }}
    
    /* 信息提示 */
    .info-message {{
        padding: 10px;
        background-color: #cce5ff;
        border-radius: 5px;
        color: #004085;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def show_loading(message: str = "加载中..."):
    """显示加载动画"""
    return st.markdown(
        f'<div class="loading-spinner"></div> {message}',
        unsafe_allow_html=True
    )


def show_success(message: str):
    """显示成功消息"""
    return st.markdown(
        f'<div class="success-message">✅ {message}</div>',
        unsafe_allow_html=True
    )


def show_error(message: str):
    """显示错误消息"""
    return st.markdown(
        f'<div class="error-message">❌ {message}</div>',
        unsafe_allow_html=True
    )


def show_info(message: str):
    """显示信息消息"""
    return st.markdown(
        f'<div class="info-message">ℹ️ {message}</div>',
        unsafe_allow_html=True
    )


class SidebarManager:
    """侧边栏管理器"""
    
    def __init__(self, config):
        self.config = config
        self.tabs = None
    
    def create_tabs(self):
        """创建侧边栏标签页"""
        self.tabs = st.sidebar.tabs(["应用设置", "项目介绍"])
        return self.tabs
    
    def render_settings_tab(self, session_state):
        """渲染设置标签页"""
        with self.tabs[0]:
            st.session_state.model_type = st.sidebar.selectbox(
                "选择模型类型",
                self.config.model.supported_models,
                index=self.config.model.supported_models.index(
                    session_state.get('model_type', self.config.model.default_model_type)
                )
            )
            
            if st.session_state.model_type == "deepseek":
                st.session_state.api_key = st.sidebar.text_input(
                    "请输入 DeepSeek API Key",
                    value=session_state.get('api_key', ''),
                    key="api_key_input",
                    type="password"
                )
            elif st.session_state.model_type == "qwen2.5-3b":
                st.sidebar.info("Qwen 模型使用环境变量配置")
            
            st.session_state.geocode_type = st.sidebar.selectbox(
                "地理编码类型",
                self.config.model.supported_geocode_types,
                index=self.config.model.supported_geocode_types.index(
                    session_state.get('geocode_type', self.config.model.default_geocode_type)
                )
            )
            
            if st.session_state.geocode_type == "baidu":
                st.session_state.baidu_key = st.sidebar.text_input(
                    "百度地图 API Key",
                    value=session_state.get('baidu_key', ''),
                    key="baidu_key_input",
                    type="password"
                )
            else:
                st.session_state.username = st.sidebar.text_input(
                    "用户名（用于地理编码）",
                    value=session_state.get('username', self.config.username),
                    key="username_input"
                )
    
    def render_intro_tab(self):
        """渲染项目介绍标签页"""
        with self.tabs[1]:
            st.markdown("""
            ## 🗺️ AI-MapBook 项目介绍

            **AI-MapBook** 是一个利用大型语言模型（LLM）技术为故事讲述提供地图支持的项目。
            
            ### ✨ 功能特点
            - 利用 LLM 提取地理信息和属性信息
            - 结合地理编码得到地理坐标数据
            - 交互式地图可视化展示
            - RAG 智能问答
            
            ### 🎯 应用场景
            - 故事创作者
            - 教育工作者
            - 地理历史学习
            - 军事情报检索
            
            ### 📱 项目地址
            [GitHub](https://github.com/qianyouliang/AI-MapBook)
            
            ### 📧 联系方式
            - Email: qianyouliang123@gmail.com
            - GitHub: @qianyouliang
            """)


class LayoutManager:
    """布局管理器"""
    
    def __init__(self, config):
        self.config = config
    
    def create_main_layout(self):
        """创建主布局"""
        container = st.container(border=True, height=1080)
        with container:
            row1 = st.container(border=True, height=self.config.ui.map_height)
            row2 = st.container(border=True, height=self.config.ui.event_list_height)
        return container, row1, row2
    
    def create_map_section(self, row):
        """创建地图区域"""
        with row:
            col1, col2 = st.columns([3, 7])
            with col1:
                st.markdown("#### 📋 事件列表")
                processing_info = st.empty()
            with col2:
                st.markdown("#### 🗺️ 地图")
        return col1, col2, processing_info
    
    def create_chat_section(self, row):
        """创建聊天区域"""
        with row:
            chat_container = st.container(height=self.config.ui.chat_height)
            with chat_container:
                st.markdown("#### 🤖 MapAgent")
        return chat_container


def render_event_card(event_info: dict, expanded: bool = False):
    """渲染事件卡片"""
    title = event_info.get("event_title", "未知事件")
    address = event_info.get("address", "未知地址")
    
    truncated_title = title if len(title) <= 20 else title[:20] + "..."
    
    with st.expander(truncated_title, expanded=expanded):
        st.json(event_info)
        st.caption(f"📍 {address}")


def render_map_selector(map_config, map_instance):
    """渲染地图选择器"""
    tiles_options = map_instance.tiles_options if hasattr(map_instance, 'tiles_options') else map_config.tiles_options
    selected_tile_name = st.selectbox(
        "选择地图底图",
        list(tiles_options.keys()),
        index=0
    )
    selected_tile = tiles_options[selected_tile_name]
    return selected_tile_name, selected_tile


def create_export_buttons(map_instance, geo_info_list: list):
    """创建导出按钮"""
    if len(geo_info_list) > 0:
        st.sidebar.markdown("### 📤 数据导出")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            export_geojson = st.button("📥 GeoJSON")
        
        # with col2:
        #     export_shp = st.button("📥 SHP")
        
        if export_geojson:
            b = map_instance.export_geojson()
            st.sidebar.download_button(
                label="下载 GeoJSON",
                data=b,
                file_name="data.geojson",
                mime="application/json"
            )
        
        # if export_shp:
        #     b = map_instance.export_shp(crs_type="WGS-84")
        #     st.sidebar.download_button(
        #         label="下载 SHP",
        #         data=b,
        #         file_name="data.zip",
        #         mime="application/zip"
        #     )
