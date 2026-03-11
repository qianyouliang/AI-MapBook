"""
数据分析模块
AI-MapBook 数据统计分析
"""
from typing import Dict, List
from collections import Counter
import json


class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self):
        self.data = []
    
    def add_data(self, geo_info_list: List[Dict]):
        """添加数据"""
        self.data = geo_info_list
    
    def analyze(self) -> Dict:
        """
        分析数据
        
        Returns:
            分析结果
        """
        if not self.data:
            return {
                "total_points": 0,
                "message": "No data to analyze"
            }
        
        # 基本统计
        total = len(self.data)
        
        # 提取地点信息
        locations = []
        types = []
        keywords = []
        
        for item in self.data:
            if "address" in item:
                locations.append(item["address"])
            if "event_type" in item:
                types.append(item["event_type"])
            if "keys" in item:
                keywords.extend(item["keys"].split(",") if isinstance(item["keys"], str) else [])
        
        # 地点分布
        location_counts = Counter(locations).most_common(10)
        
        # 类型分布
        type_counts = Counter(types)
        
        # 关键词统计
        keyword_counts = Counter([k.strip() for k in keywords if k]).most_common(20)
        
        return {
            "total_points": total,
            "unique_locations": len(set(locations)),
            "location_distribution": dict(location_counts),
            "type_distribution": dict(type_counts),
            "top_keywords": keyword_counts,
            "has_coordinates": sum(1 for d in self.data if "geocode" in d),
        }
    
    def generate_report(self) -> str:
        """生成文本报告"""
        analysis = self.analyze()
        
        if analysis.get("total_points", 0) == 0:
            return "暂无数据"
        
        report = f"""
📊 数据分析报告
================

总数据点: {analysis['total_points']}
唯一地点数: {analysis.get('unique_locations', 0)}
有坐标数据: {analysis.get('has_coordinates', 0)}

📍 热门地点 (Top 10):
"""
        for loc, count in analysis.get("location_distribution", {}).items():
            report += f"  - {loc}: {count} 次\n"
        
        report += "\n🏷️ 热门关键词 (Top 10):\n"
        for kw, count in analysis.get("top_keywords", [])[:10]:
            report += f"  - {kw}: {count} 次\n"
        
        return report
    
    def export_json(self) -> str:
        """导出 JSON"""
        return json.dumps(self.analyze(), ensure_ascii=False, indent=2)


def analyze_geo_data(geo_info_list: List[Dict]) -> Dict:
    """
    分析地理数据的便捷函数
    
    Args:
        geo_info_list: 地理信息列表
    
    Returns:
        分析结果
    """
    analyzer = DataAnalyzer()
    analyzer.add_data(geo_info_list)
    return analyzer.analyze()
