"""
用户配置管理
AI-MapBook 用户自定义配置
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class UserConfig:
    """用户配置类"""
    
    DEFAULT_CONFIG = {
        "theme": "light",
        "language": "zh",
        "default_model": "deepseek",
        "default_geocode": "free",
        "auto_save": True,
        "map_tile": "OpenStreetMap",
        "custom_shortcuts": {},
    }
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            project_root = Path(__file__).parent.parent
            config_dir = project_root / "storage" / "config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "user_config.json"
        self.config = self._load()
    
    def _load(self) -> Dict:
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return {**self.DEFAULT_CONFIG, **json.load(f)}
        return self.DEFAULT_CONFIG.copy()
    
    def _save(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str, default=None):
        """获取配置"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置"""
        self.config[key] = value
        self._save()
    
    def get_all(self) -> Dict:
        """获取所有配置"""
        return self.config.copy()
    
    def reset(self):
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save()
    
    def import_config(self, config: Dict):
        """导入配置"""
        self.config = {**self.DEFAULT_CONFIG, **config}
        self._save()
    
    def export_config(self) -> str:
        """导出配置"""
        return json.dumps(self.config, ensure_ascii=False, indent=2)


# 全局实例
_user_config = None


def get_user_config() -> UserConfig:
    """获取用户配置实例"""
    global _user_config
    if _user_config is None:
        _user_config = UserConfig()
    return _user_config
