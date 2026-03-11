"""
配置管理
AI-MapBook 统一配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """全局配置"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # 目录配置
    DATA_DIR = PROJECT_ROOT / "data"
    MODELS_DIR = PROJECT_ROOT / "models"
    STORAGE_DIR = PROJECT_ROOT / "storage"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # API 配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    
    # 百度地图
    BAIDU_AK = os.getenv("BAIDU_AK", "")
    
    # Embedding 模型
    EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
    
    # 地理编码
    GEOCODE_USER_AGENT = "AI-MapBook"
    
    # 文件处理
    CHUNK_SIZE = 512
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # 确保目录存在
    @classmethod
    def init_dirs(cls):
        for dir_path in [cls.DATA_DIR, cls.MODELS_DIR, cls.STORAGE_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


config = Config()
