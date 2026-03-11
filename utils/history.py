"""
历史记录管理模块
AI-MapBook 处理历史管理
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import streamlit as st


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, storage_dir: str = None):
        """
        初始化历史记录管理器
        
        Args:
            storage_dir: 存储目录
        """
        if storage_dir is None:
            project_root = Path(__file__).parent.parent
            storage_dir = project_root / "storage" / "history"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 元数据文件
        self.meta_file = self.storage_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        if self.meta_file.exists():
            with open(self.meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "records": [],
            "last_updated": None
        }
    
    def _save_metadata(self):
        """保存元数据"""
        self.metadata["last_updated"] = datetime.now().isoformat()
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def create_record(
        self,
        filename: str,
        file_type: str,
        geo_count: int,
        status: str = "completed",
        metadata: Dict = None
    ) -> str:
        """
        创建历史记录
        
        Args:
            filename: 文件名
            file_type: 文件类型
            geo_count: 地理点数量
            status: 处理状态
            metadata: 附加元数据
        
        Returns:
            记录ID
        """
        record_id = f"hist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        record = {
            "id": record_id,
            "filename": filename,
            "file_type": file_type,
            "geo_count": geo_count,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # 保存记录详情
        record_file = self.storage_dir / f"{record_id}.json"
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        # 更新元数据索引
        self.metadata["records"].insert(0, {
            "id": record_id,
            "filename": filename,
            "created_at": record["created_at"],
            "geo_count": geo_count,
            "status": status
        })
        
        # 只保留最近100条索引
        self.metadata["records"] = self.metadata["records"][:100]
        self._save_metadata()
        
        return record_id
    
    def get_record(self, record_id: str) -> Optional[Dict]:
        """
        获取历史记录详情
        
        Args:
            record_id: 记录ID
        
        Returns:
            记录详情
        """
        record_file = self.storage_dir / f"{record_id}.json"
        if not record_file.exists():
            return None
        
        with open(record_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_records(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = None,
        file_type: str = None
    ) -> List[Dict]:
        """
        列出历史记录
        
        Args:
            limit: 返回数量
            offset: 偏移量
            status: 按状态筛选
            file_type: 按文件类型筛选
        
        Returns:
            记录列表
        """
        records = self.metadata["records"]
        
        # 筛选
        if status:
            records = [r for r in records if r.get("status") == status]
        if file_type:
            records = [r for r in records if r.get("file_type") == file_type]
        
        return records[offset:offset + limit]
    
    def delete_record(self, record_id: str) -> bool:
        """
        删除历史记录
        
        Args:
            record_id: 记录ID
        
        Returns:
            是否成功
        """
        record_file = self.storage_dir / f"{record_id}.json"
        
        if record_file.exists():
            record_file.unlink()
        
        # 从索引中移除
        self.metadata["records"] = [
            r for r in self.metadata["records"] if r["id"] != record_id
        ]
        self._save_metadata()
        
        return True
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        records = self.metadata["records"]
        
        total = len(records)
        completed = len([r for r in records if r.get("status") == "completed"])
        failed = len([r for r in records if r.get("status") == "failed"])
        
        total_geo = sum(r.get("geo_count", 0) for r in records)
        
        return {
            "total_records": total,
            "completed": completed,
            "failed": failed,
            "total_geo_points": total_geo,
            "success_rate": round(completed / max(total, 1) * 100, 1)
        }
    
    def clear_old_records(self, days: int = 30) -> int:
        """
        清理旧记录
        
        Args:
            days: 保留天数
        
        Returns:
            删除数量
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        for record in self.metadata["records"][:]:
            created = datetime.fromisoformat(record["created_at"])
            if created < cutoff:
                self.delete_record(record["id"])
                deleted += 1
        
        return deleted


# Streamlit UI 组件
def render_history_panel(manager: HistoryManager):
    """
    渲染历史记录面板
    
    Args:
        manager: HistoryManager 实例
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 历史记录")
    
    # 统计信息
    stats = manager.get_statistics()
    
    col1, col2, col3 = st.sidebar.columns(3)
    col1.metric("总数", stats["total_records"])
    col2.metric("成功", stats["completed"])
    col3.metric("失败", stats["failed"])
    
    # 历史记录列表
    records = manager.list_records(limit=10)
    
    if not records:
        st.sidebar.info("暂无历史记录")
        return
    
    for record in records:
        status_icon = "✅" if record.get("status") == "completed" else "❌"
        with st.sidebar.expander(f"{status_icon} {record.get('filename', 'Unknown')}"):
            st.caption(f"时间: {record.get('created_at', '')}")
            st.caption(f"地理点: {record.get('geo_count', 0)}")
            
            if st.button(f"删除", key=f"del_{record['id']}"):
                manager.delete_record(record["id"])
                st.rerun()


# 全局实例
_history_manager = None


def get_history_manager() -> HistoryManager:
    """获取历史记录管理器实例"""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager
