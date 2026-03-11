"""
数据持久化模块
AI-MapBook 数据保存和加载
"""
import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class DataPersistence:
    """数据持久化管理类"""
    
    def __init__(self, storage_dir: str = None):
        """
        初始化数据持久化类
        
        Args:
            storage_dir: 存储目录路径，默认为项目目录下的 storage
        """
        if storage_dir is None:
            project_root = Path(__file__).parent.parent
            storage_dir = project_root / "storage"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # 历史记录目录
        self.history_dir = self.storage_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
        
        # 导出数据目录
        self.exports_dir = self.storage_dir / "exports"
        self.exports_dir.mkdir(exist_ok=True)
    
    def save_to_json(self, data: List[Dict], filename: str = None) -> str:
        """
        保存数据到 JSON 文件
        
        Args:
            data: 要保存的数据列表
            filename: 文件名，默认使用时间戳
        
        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"geo_data_{timestamp}.json"
        
        filepath = self.exports_dir / filename
        
        # 准备可序列化的数据
        serializable_data = self._prepare_for_serialization(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def load_from_json(self, filepath: str) -> List[Dict]:
        """
        从 JSON 文件加载数据
        
        Args:
            filepath: JSON 文件路径
        
        Returns:
            加载的数据列表
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def save_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """
        保存数据到 CSV 文件
        
        Args:
            data: 要保存的数据列表
            filename: 文件名
        
        Returns:
            保存的文件路径
        """
        if not data:
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"geo_data_{timestamp}.csv"
        
        filepath = self.exports_dir / filename
        
        # 提取所有可能的字段
        all_fields = set()
        for item in data:
            if 'fields' in item:
                all_fields.update(item['fields'].keys())
            else:
                all_fields.update(item.keys())
        
        fieldnames = list(all_fields)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                row = item.get('fields', item)
                # 处理嵌套对象
                flat_row = {}
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        flat_row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        flat_row[key] = value
                writer.writerow(flat_row)
        
        return str(filepath)
    
    def save_history(self, data: List[Dict], description: str = "") -> str:
        """
        保存处理历史
        
        Args:
            data: 处理的数据
            description: 描述信息
        
        Returns:
            历史记录文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_{timestamp}.json"
        filepath = self.history_dir / filename
        
        history_entry = {
            "timestamp": timestamp,
            "description": description,
            "record_count": len(data),
            "data": self._prepare_for_serialization(data)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_entry, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def list_history(self) -> List[Dict]:
        """
        列出所有历史记录
        
        Returns:
            历史记录列表（仅包含元数据，不包含实际数据）
        """
        history_list = []
        
        for filepath in sorted(self.history_dir.glob("history_*.json"), reverse=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                    history_list.append({
                        "filename": filepath.name,
                        "timestamp": entry.get("timestamp"),
                        "description": entry.get("description", ""),
                        "record_count": entry.get("record_count", 0)
                    })
            except Exception:
                continue
        
        return history_list
    
    def load_history(self, filename: str) -> Dict:
        """
        加载指定的历史记录
        
        Args:
            filename: 历史文件名
        
        Returns:
            历史记录数据
        """
        filepath = self.history_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"历史记录文件不存在: {filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_history(self, filename: str) -> bool:
        """
        删除指定的历史记录
        
        Args:
            filename: 历史文件名
        
        Returns:
            是否删除成功
        """
        filepath = self.history_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def get_storage_stats(self) -> Dict:
        """
        获取存储统计信息
        
        Returns:
            存储统计字典
        """
        history_files = list(self.history_dir.glob("history_*.json"))
        export_files = list(self.exports_dir.glob("*"))
        
        total_size = sum(f.stat().st_size for f in history_files + export_files if f.is_file())
        
        return {
            "history_count": len(history_files),
            "export_count": len(export_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_dir": str(self.storage_dir)
        }
    
    def _prepare_for_serialization(self, data: List[Dict]) -> List[Dict]:
        """
        准备数据以便 JSON 序列化
        
        Args:
            data: 原始数据
        
        Returns:
            可序列化的数据
        """
        serializable = []
        for item in data:
            new_item = {}
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    # 尝试序列化
                    try:
                        json.dumps(value)
                        new_item[key] = value
                    except (TypeError, ValueError):
                        new_item[key] = str(value)
                elif hasattr(value, 'tolist'):  # numpy array
                    new_item[key] = value.tolist()
                else:
                    new_item[key] = value
            serializable.append(new_item)
        return serializable


# 全局实例
_persistence_instance = None


def get_persistence() -> DataPersistence:
    """获取全局数据持久化实例"""
    global _persistence_instance
    if _persistence_instance is None:
        _persistence_instance = DataPersistence()
    return _persistence_instance
