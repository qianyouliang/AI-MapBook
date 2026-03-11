"""
智能推荐模块
AI-MapBook 智能推荐功能
"""
from typing import List, Dict, Optional
import re
from collections import Counter


class GeoRecommender:
    """地理信息智能推荐器"""
    
    def __init__(self):
        # 常见地理位置数据库（简化版）
        self.known_locations = {
            # 中国城市
            "北京": {"lat": 39.9042, "lon": 116.4074, "country": "中国", "province": "北京"},
            "上海": {"lat": 31.2304, "lon": 121.4737, "country": "中国", "province": "上海"},
            "广州": {"lat": 23.1291, "lon": 113.2644, "country": "中国", "province": "广东"},
            "深圳": {"lat": 22.5431, "lon": 114.0579, "country": "中国", "province": "广东"},
            "成都": {"lat": 30.5728, "lon": 104.0668, "country": "中国", "province": "四川"},
            "杭州": {"lat": 30.2741, "lon": 120.1551, "country": "中国", "province": "浙江"},
            "西安": {"lat": 34.3416, "lon": 108.9398, "country": "中国", "province": "陕西"},
            "南京": {"lat": 32.0603, "lon": 118.7969, "country": "中国", "province": "江苏"},
            "武汉": {"lat": 30.5928, "lon": 114.3055, "country": "中国", "province": "湖北"},
            "重庆": {"lat": 29.4316, "lon": 106.9123, "country": "中国", "province": "重庆"},
            # 世界著名城市
            "纽约": {"lat": 40.7128, "lon": -74.0060, "country": "美国", "city": "纽约"},
            "伦敦": {"lat": 51.5074, "lon": -0.1278, "country": "英国", "city": "伦敦"},
            "巴黎": {"lat": 48.8566, "lon": 2.3522, "country": "法国", "city": "巴黎"},
            "东京": {"lat": 35.6762, "lon": 139.6503, "country": "日本", "city": "东京"},
            "悉尼": {"lat": -33.8688, "lon": 151.2093, "country": "澳大利亚", "city": "悉尼"},
        }
        
        # 历史事件关键词
        self.event_keywords = {
            "战争": ["战役", "战斗", "冲突", "占领", "攻克"],
            "政治": ["即位", "登基", "建国", "迁都", "签约"],
            "经济": ["通商", "贸易", "建城", "开采"],
            "文化": ["建庙", "办学", "印刷", "书院"],
            "自然灾害": ["洪水", "地震", "饥荒", "瘟疫"],
        }
    
    def recommend_locations(self, text: str, top_n: int = 5) -> List[Dict]:
        """
        从文本中推荐相关地理位置
        
        Args:
            text: 输入文本
            top_n: 返回数量
        
        Returns:
            推荐位置列表
        """
        recommendations = []
        text = text.lower()
        
        # 1. 精确匹配已知位置
        for name, info in self.known_locations.items():
            if name in text:
                recommendations.append({
                    "name": name,
                    "type": "exact_match",
                    "info": info,
                    "confidence": 0.9
                })
        
        # 2. 模糊匹配（基于关键词）
        for name, info in self.known_locations.items():
            if name[:2] in text and name not in [r["name"] for r in recommendations]:
                recommendations.append({
                    "name": name,
                    "type": "partial_match",
                    "info": info,
                    "confidence": 0.6
                })
        
        # 3. 基于事件类型推荐
        for event_type, keywords in self.event_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    # 推荐与该类型相关的热门位置
                    related = self._get_related_locations(event_type)
                    for loc in related:
                        if loc["name"] not in [r["name"] for r in recommendations]:
                            recommendations.append({
                                "name": loc["name"],
                                "type": "event_related",
                                "info": loc["info"],
                                "confidence": 0.4,
                                "reason": f"与'{keyword}'相关"
                            })
        
        # 按置信度排序
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return recommendations[:top_n]
    
    def _get_related_locations(self, event_type: str) -> List[Dict]:
        """获取与事件类型相关的位置"""
        mapping = {
            "战争": ["北京", "南京", "西安", "重庆"],
            "政治": ["北京", "南京", "西安", "杭州"],
            "经济": ["上海", "广州", "深圳", "杭州"],
            "文化": ["北京", "曲阜", "洛阳", "苏州"],
        }
        
        names = mapping.get(event_type, [])
        return [{"name": n, "info": self.known_locations.get(n, {})} for n in names]
    
    def suggest_map_settings(self, recommendations: List[Dict]) -> Dict:
        """
        建议地图设置
        
        Args:
            recommendations: 推荐位置列表
        
        Returns:
            地图设置建议
        """
        if not recommendations:
            return {
                "center": [35.8617, 104.1954],
                "zoom": 4,
                "tile": "OpenStreetMap"
            }
        
        # 计算中心点
        lats = [r["info"]["lat"] for r in recommendations if "lat" in r["info"]]
        lons = [r["info"]["lon"] for r in recommendations if "lon" in r["info"]]
        
        if lats and lons:
            center = [sum(lats) / len(lats), sum(lons) / len(lons)]
        else:
            center = [35.8617, 104.1954]
        
        # 计算合适的缩放级别
        if len(recommendations) == 1:
            zoom = 10
        elif len(recommendations) <= 3:
            zoom = 6
        else:
            zoom = 4
        
        return {
            "center": center,
            "zoom": zoom,
            "tile": "OpenStreetMap"
        }


class RecommendationEngine:
    """推荐引擎"""
    
    def __init__(self):
        self.geo_recommender = GeoRecommender()
        self.user_preferences = {}
    
    def process(self, text: str, existing_locations: List[Dict] = None) -> Dict:
        """
        处理推荐请求
        
        Args:
            text: 输入文本
            existing_locations: 已有位置列表
        
        Returns:
            推荐结果
        """
        # 获取位置推荐
        location_recs = self.geo_recommender.recommend_locations(text)
        
        # 过滤已有位置
        if existing_locations:
            existing_names = [loc.get("event_title", "") for loc in existing_locations]
            location_recs = [r for r in location_recs if r["name"] not in existing_names]
        
        # 获取地图设置建议
        map_settings = self.geo_recommender.suggest_map_settings(location_recs)
        
        return {
            "locations": location_recs,
            "map_settings": map_settings,
            "total": len(location_recs)
        }
    
    def update_preferences(self, user_id: str, preferences: Dict):
        """更新用户偏好"""
        self.user_preferences[user_id] = preferences
    
    def get_recommendation_explanation(self, recommendation: Dict) -> str:
        """获取推荐解释"""
        conf = recommendation.get("confidence", 0)
        rec_type = recommendation.get("type", "unknown")
        
        if conf >= 0.8:
            confidence_text = "非常确定"
        elif conf >= 0.6:
            confidence_text = "比较确定"
        elif conf >= 0.4:
            confidence_text = "可能相关"
        else:
            confidence_text = "建议确认"
        
        return f"{confidence_text} - {rec_type}"


# 全局实例
_recommender = None


def get_recommender() -> RecommendationEngine:
    """获取推荐引擎实例"""
    global _recommender
    if _recommender is None:
        _recommender = RecommendationEngine()
    return _recommender
