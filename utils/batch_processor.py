"""
批量文件处理模块
AI-MapBook 批量处理多个文件
"""
import os
from typing import List, Dict, Callable, Optional
from io import BytesIO
from pathlib import Path
import streamlit as st


class BatchProcessor:
    """批量文件处理器"""
    
    def __init__(self, file_processor, llm=None, geocode_utils=None):
        """
        初始化批量处理器
        
        Args:
            file_processor: 文件处理器实例
            llm: LLM 模型实例
            geocode_utils: 地理编码工具实例
        """
        self.file_processor = file_processor
        self.llm = llm
        self.geocode_utils = geocode_utils
        
        # 处理结果
        self.results = []
        self.errors = []
        
        # 回调函数
        self.on_progress = None  # 进度回调
        self.on_complete = None  # 完成回调
        self.on_error = None  # 错误回调
    
    def set_callbacks(self, on_progress: Callable = None, on_complete: Callable = None, on_error: Callable = None):
        """设置回调函数"""
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
    
    def process_files(
        self,
        uploaded_files: List,
        process_func: Callable = None,
        show_progress: bool = True
    ) -> Dict:
        """
        批量处理文件
        
        Args:
            uploaded_files: 上传的文件列表
            process_func: 自定义处理函数，如果为 None 则使用默认处理
            show_progress: 是否显示进度
        
        Returns:
            处理结果字典
        """
        self.results = []
        self.errors = []
        
        total = len(uploaded_files)
        
        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                # 调用进度回调
                if self.on_progress:
                    self.on_progress(idx + 1, total, uploaded_file.name)
                
                # 处理单个文件
                result = self._process_single_file(
                    uploaded_file,
                    process_func
                )
                
                if result:
                    self.results.append(result)
                    
            except Exception as e:
                error_info = {
                    "filename": uploaded_file.name,
                    "error": str(e)
                }
                self.errors.append(error_info)
                
                if self.on_error:
                    self.on_error(error_info)
        
        # 调用完成回调
        if self.on_complete:
            self.on_complete(self.results, self.errors)
        
        return {
            "total": total,
            "success": len(self.results),
            "errors": len(self.errors),
            "results": self.results,
            "error_details": self.errors
        }
    
    def _process_single_file(
        self,
        uploaded_file,
        process_func: Callable = None
    ) -> Optional[Dict]:
        """
        处理单个文件
        
        Args:
            uploaded_file: 上传的文件
            process_func: 自定义处理函数
        
        Returns:
            处理结果
        """
        # 根据文件类型提取文本
        file_content = uploaded_file.read()
        file_stream = BytesIO(file_content)
        
        if uploaded_file.name.endswith('.pdf'):
            text_list = self.file_processor.extract_text_from_pdf(file_stream)
        elif uploaded_file.name.endswith('.txt'):
            text_list = self.file_processor.extract_text_from_txt(file_stream)
        else:
            raise ValueError(f"不支持的文件类型: {uploaded_file.name}")
        
        # 如果有自定义处理函数，使用它
        if process_func:
            return process_func(text_list, uploaded_file.name)
        
        # 默认处理流程
        geo_info_list = []
        
        if self.llm:
            for text in text_list:
                event_list = self.llm.get_event_list(text)
                
                if event_list:
                    for event in event_list:
                        try:
                            event_info = self.llm.process_event(event)
                            
                            if self.geocode_utils and event_info.get("address"):
                                geocode_info = self.geocode_utils.geocode(
                                    event_info["address"]
                                )
                                if geocode_info:
                                    event_info["geocode"] = geocode_info
                                    geo_info_list.append(event_info)
                        except Exception as e:
                            continue
        
        return {
            "filename": uploaded_file.name,
            "text_count": len(text_list),
            "geo_count": len(geo_info_list),
            "geo_info_list": geo_info_list
        }
    
    def get_statistics(self) -> Dict:
        """
        获取处理统计信息
        
        Returns:
            统计信息字典
        """
        total_text = sum(r.get("text_count", 0) for r in self.results)
        total_geo = sum(r.get("geo_count", 0) for r in self.results)
        
        return {
            "total_files": len(self.results) + len(self.errors),
            "success_files": len(self.results),
            "failed_files": len(self.errors),
            "total_text_chunks": total_text,
            "total_geo_points": total_geo,
            "success_rate": len(self.results) / max(len(self.results) + len(self.errors), 1) * 100
        }


class FileTypeDetector:
    """文件类型检测器"""
    
    SUPPORTED_TYPES = {
        "pdf": ["pdf"],
        "txt": ["txt"],
        "docx": ["docx"],
        "epub": ["epub"],
        "mobi": ["mobi"],
        "md": ["md"]
    }
    
    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """
        检查文件类型是否支持
        
        Args:
            filename: 文件名
        
        Returns:
            是否支持
        """
        ext = filename.split('.')[-1].lower()
        return ext in cls.get_all_extensions()
    
    @classmethod
    def get_all_extensions(cls) -> List[str]:
        """获取所有支持的扩展名"""
        extensions = []
        for exts in cls.SUPPORTED_TYPES.values():
            extensions.extend(exts)
        return extensions
    
    @classmethod
    def get_file_category(cls, filename: str) -> str:
        """
        获取文件类别
        
        Args:
            filename: 文件名
        
        Returns:
            文件类别
        """
        ext = filename.split('.')[-1].lower()
        
        for category, exts in cls.SUPPORTED_TYPES.items():
            if ext in exts:
                return category
        
        return "unknown"
    
    @classmethod
    def validate_files(cls, filenames: List[str]) -> Dict:
        """
        验证文件列表
        
        Args:
            filenames: 文件名列表
        
        Returns:
            验证结果
        """
        valid = []
        invalid = []
        
        for filename in filenames:
            if cls.is_supported(filename):
                valid.append(filename)
            else:
                invalid.append({
                    "filename": filename,
                    "reason": f"不支持的文件类型，支持的类型: {', '.join(cls.get_all_extensions())}"
                })
        
        return {
            "valid": valid,
            "invalid": invalid,
            "is_valid": len(invalid) == 0
        }


def create_batch_processor(file_processor, llm=None, geocode_utils=None) -> BatchProcessor:
    """
    创建批量处理器工厂函数
    
    Args:
        file_processor: 文件处理器
        llm: LLM 模型
        geocode_utils: 地理编码工具
    
    Returns:
        BatchProcessor 实例
    """
    return BatchProcessor(file_processor, llm, geocode_utils)
