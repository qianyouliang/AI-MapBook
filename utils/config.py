"""
统一配置管理模块
AI-MapBook 项目配置集中管理
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class APIConfig:
    """API 配置"""
    # DeepSeek
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    
    # Qwen (讯飞星火)
    qwen_app_id: str = field(default_factory=lambda: os.getenv("APP_ID", ""))
    qwen_api_key: str = field(default_factory=lambda: os.getenv("QWEN_API_KEY", ""))
    qwen_api_secret: str = field(default_factory=lambda: os.getenv("API_SECRET", ""))
    qwen_service_id: str = field(default_factory=lambda: os.getenv("SERVICE_ID", ""))
    qwen_patch_id: str = field(default_factory=lambda: os.getenv("PATCH_ID", ""))
    
    # 百度地图
    baidu_ak: str = field(default_factory=lambda: os.getenv("BAIDU_AK", ""))
    
    @property
    def is_deepseek_configured(self) -> bool:
        return bool(self.deepseek_api_key)
    
    @property
    def is_qwen_configured(self) -> bool:
        return all([
            self.qwen_app_id, 
            self.qwen_api_key, 
            self.qwen_api_secret,
            self.qwen_service_id
        ])
    
    @property
    def is_baidu_configured(self) -> bool:
        return bool(self.baidu_ak)


@dataclass
class PathConfig:
    """路径配置"""
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
    models_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"))
    storage_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage"))
    
    def __post_init__(self):
        """确保目录存在"""
        for dir_path in [self.data_dir, self.models_dir, self.storage_dir]:
            os.makedirs(dir_path, exist_ok=True)


@dataclass
class ModelConfig:
    """模型配置"""
    default_model_type: str = "deepseek"  # deepseek, qwen2.5-3b, ipex_llm
    default_geocode_type: str = "free"    # free, baidu
    
    # IPEX-LLM 配置
    ipex_model_path: str = "models/qwen2chat_int4"
    ipex_threads: int = 8
    
    # 支持的模型类型
    supported_models: list = field(default_factory=lambda: ["deepseek", "qwen2.5-3b", "ipex_llm"])
    
    # 支持的地理编码类型
    supported_geocode_types: list = field(default_factory=lambda: ["free", "baidu"])


@dataclass
class MapConfig:
    """地图配置"""
    default_tile: str = "OpenStreetMap"
    default_center: tuple = (35.8617, 104.1954)  # 中国中心
    default_zoom: int = 4
    
    tiles_options: dict = field(default_factory=lambda: {
        "OpenStreetMap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "CartoDB Positron": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "CartoDB Dark": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "Gaode Map": "https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
        "Gaode Satellite": "https://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}",
    })
    
    tile_attribution: str = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'


@dataclass
class UIConfig:
    """UI 配置"""
    page_title: str = "AI-MapBook"
    page_icon: str = "🗺️"
    layout: str = "wide"
    
    # 侧边栏配置
    sidebar_width: int = 320
    
    # 布局配置
    map_height: int = 600
    event_list_height: int = 600
    chat_height: int = 440
    
    # 颜色主题
    primary_color: str = "#FF4B4B"
    background_color: str = "#FFFFFF"


@dataclass
class RAGConfig:
    """RAG 配置"""
    chunk_size: int = 512
    chunk_overlap: int = 50
    vector_store_type: str = "faiss"
    embedding_model: str = "sentence-transformers"
    

@dataclass
class Config:
    """全局配置"""
    api: APIConfig = field(default_factory=APIConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    map: MapConfig = field(default_factory=MapConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    
    # 用户名（用于免费地理编码）
    username: str = "GISerLiu"


# 全局配置实例
config = Config()


def get_config() -> Config:
    """获取全局配置实例"""
    return config


def reload_config():
    """重新加载配置（从环境变量）"""
    load_dotenv(override=True)
    global config
    config = Config()
    return config
