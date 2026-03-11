"""
国际化支持模块
AI-MapBook 多语言支持
"""
from typing import Dict
import streamlit as st


class I18n:
    """国际化类"""
    
    # 翻译字典
    _translations = {
        "zh": {
            "app_title": "AI-MapBook",
            "app_subtitle": "LLM驱动的地图故事可视化",
            "upload_file": "上传文件",
            "select_model": "选择模型",
            "select_geocode": "地理编码类型",
            "map": "地图",
            "event_list": "事件列表",
            "chat_agent": "MapAgent",
            "rag_enabled": "启用RAG",
            "processing": "处理中...",
            "completed": "完成",
            "export_geojson": "导出GeoJSON",
            "download": "下载",
            "settings": "设置",
            "about": "关于",
            "history": "历史记录",
            "clear_history": "清除历史",
            "confirm": "确认",
            "cancel": "取消",
            "error": "错误",
            "success": "成功",
            "warning": "警告",
            "info": "信息",
            "no_data": "暂无数据",
            "loading": "加载中...",
            "file_processed": "文件已处理",
            "geo_points": "地理点",
            "events": "事件",
        },
        "en": {
            "app_title": "AI-MapBook",
            "app_subtitle": "LLM-powered Map Story Visualization",
            "upload_file": "Upload File",
            "select_model": "Select Model",
            "select_geocode": "Geocode Type",
            "map": "Map",
            "event_list": "Event List",
            "chat_agent": "MapAgent",
            "rag_enabled": "Enable RAG",
            "processing": "Processing...",
            "completed": "Completed",
            "export_geojson": "Export GeoJSON",
            "download": "Download",
            "settings": "Settings",
            "about": "About",
            "history": "History",
            "clear_history": "Clear History",
            "confirm": "Confirm",
            "cancel": "Cancel",
            "error": "Error",
            "success": "Success",
            "warning": "Warning",
            "info": "Info",
            "no_data": "No Data",
            "loading": "Loading...",
            "file_processed": "File Processed",
            "geo_points": "Geo Points",
            "events": "Events",
        }
    }
    
    def __init__(self, locale: str = "zh"):
        """
        初始化国际化
        
        Args:
            locale: 语言代码 (zh/en)
        """
        self.locale = locale if locale in self._translations else "zh"
        self._translations_dict = self._translations[self.locale]
    
    def t(self, key: str, default: str = None) -> str:
        """
        翻译
        
        Args:
            key: 翻译键
            default: 默认值
        
        Returns:
            翻译后的文本
        """
        return self._translations_dict.get(key, default or key)
    
    def get(self, key: str) -> str:
        """获取翻译"""
        return self.t(key)
    
    @classmethod
    def get_available_locales(cls) -> list:
        """获取支持的语言列表"""
        return list(cls._translations.keys())
    
    @classmethod
    def get_locale_name(cls, locale: str) -> str:
        """获取语言名称"""
        names = {
            "zh": "中文",
            "en": "English"
        }
        return names.get(locale, locale)


class LocaleManager:
    """语言管理器"""
    
    def __init__(self):
        self._locale = "zh"
        self._i18n = I18n(self._locale)
    
    @property
    def locale(self) -> str:
        return self._locale
    
    @locale.setter
    def locale(self, value: str):
        self._locale = value
        self._i18n = I18n(value)
    
    @property
    def i18n(self) -> I18n:
        return self._i18n
    
    def t(self, key: str, default: str = None) -> str:
        return self._i18n.t(key, default)
    
    @staticmethod
    def create_language_selector():
        """创建语言选择器"""
        locales = I18n.get_available_locales()
        locale_names = {loc: I18n.get_locale_name(loc) for loc in locales}
        
        selected = st.selectbox(
            "语言 / Language",
            options=locales,
            format_func=lambda x: locale_names[x],
            key="language_selector"
        )
        
        return selected


# 全局实例
_i18n_manager = None


def get_i18n_manager() -> LocaleManager:
    """获取国际化管理器"""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = LocaleManager()
    return _i18n_manager


def t(key: str, default: str = None) -> str:
    """便捷翻译函数"""
    return get_i18n_manager().t(key, default)
