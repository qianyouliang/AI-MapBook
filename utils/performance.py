"""
性能优化模块
AI-MapBook 性能优化
"""
import functools
import time
import hashlib
import json
from typing import Any, Callable, Optional
from pathlib import Path
import os


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = None, max_size_mb: int = 100):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            max_size_mb: 最大缓存大小（MB）
        """
        if cache_dir is None:
            project_root = Path(__file__).parent.parent
            cache_dir = project_root / "storage" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size_mb * 1024 * 1024
        self._current_size = self._calculate_size()
    
    def _calculate_size(self) -> int:
        """计算当前缓存大小"""
        total = 0
        for f in self.cache_dir.glob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total
    
    def _get_cache_key(self, key: str) -> str:
        """生成缓存键"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或 None
        """
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 检查过期
            if time.time() > data.get("expire_at", 0):
                cache_file.unlink()
                return None
                
            return data.get("value")
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        # 清理过期缓存
        self._cleanup()
        
        # 检查大小
        if self._current_size >= self.max_size:
            self._evict_oldest()
        
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        data = {
            "value": value,
            "expire_at": time.time() + ttl,
            "created_at": time.time()
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            self._current_size += cache_file.stat().st_size
        except Exception:
            pass
    
    def _cleanup(self):
        """清理过期缓存"""
        for f in self.cache_dir.glob("*.json"):
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                if time.time() > data.get("expire_at", 0):
                    size = f.stat().st_size
                    f.unlink()
                    self._current_size -= size
            except Exception:
                pass
    
    def _evict_oldest(self):
        """淘汰最旧的缓存"""
        files = sorted(self.cache_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
        
        for f in files[:5]:  # 淘汰5个最旧的
            try:
                size = f.stat().st_size
                f.unlink()
                self._current_size -= size
            except Exception:
                pass
    
    def clear(self):
        """清空所有缓存"""
        for f in self.cache_dir.glob("*"):
            if f.is_file():
                f.unlink()
        self._current_size = 0
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        files = list(self.cache_dir.glob("*.json"))
        return {
            "file_count": len(files),
            "size_bytes": self._current_size,
            "size_mb": round(self._current_size / (1024 * 1024), 2),
            "max_size_mb": self.max_size / (1024 * 1024)
        }


# 缓存装饰器
def cached(ttl: int = 3600, key_func: Callable = None):
    """
    缓存装饰器
    
    Args:
        ttl: 过期时间（秒）
        key_func: 生成缓存键的函数
    """
    _cache = CacheManager()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试获取缓存
            result = _cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存缓存
            _cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class ProgressTracker:
    """进度追踪器 - 优化大文件处理"""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, n: int = 1):
        """更新进度"""
        self.current += n
        self.last_update = time.time()
    
    def get_progress(self) -> dict:
        """获取进度信息"""
        elapsed = time.time() - self.start_time
        percent = (self.current / self.total * 100) if self.total > 0 else 0
        
        if self.current > 0:
            avg_time = elapsed / self.current
            remaining = (self.total - self.current) * avg_time
        else:
            remaining = 0
        
        return {
            "current": self.current,
            "total": self.total,
            "percent": round(percent, 1),
            "elapsed": round(elapsed, 1),
            "remaining": round(remaining, 1),
            "rate": round(self.current / elapsed, 2) if elapsed > 0 else 0
        }
    
    def should_update(self, min_interval: float = 0.5) -> bool:
        """检查是否应该更新UI"""
        return time.time() - self.last_update >= min_interval


class MemoryOptimizer:
    """内存优化工具"""
    
    @staticmethod
    def chunk_list(items: list, chunk_size: int):
        """分块处理列表"""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]
    
    @staticmethod
    def clear_large_variables(*vars):
        """清理大变量"""
        for var in vars:
            if hasattr(var, 'clear'):
                var.clear()
            elif hasattr(var, 'reset'):
                var.reset()


# 全局缓存实例
_cache = None


def get_cache() -> CacheManager:
    """获取缓存管理器"""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache
