"""
MCP 客户端模块
AI-MapBook 地图控制服务
"""
import json
from typing import Dict, List, Optional, Any


class MapControlTool:
    """地图控制工具"""
    
    name = "map_control"
    description = "控制交互式地图的工具"
    
    @staticmethod
    def add_marker(lat: float, lng: float, title: str, info: str = "") -> Dict:
        """
        在地图上添加标记
        
        Args:
            lat: 纬度
            lng: 经度
            title: 标题
            info: 详细信息
        
        Returns:
            操作结果
        """
        return {
            "action": "addMarker",
            "lat": lat,
            "lng": lng,
            "title": title,
            "info": info
        }
    
    @staticmethod
    def fly_to(lat: float, lng: float, zoom: int = 12) -> Dict:
        """飞向指定位置"""
        return {
            "action": "flyTo",
            "lat": lat,
            "lng": lng,
            "zoom": zoom
        }
    
    @staticmethod
    def clear_markers() -> Dict:
        """清除所有标记"""
        return {"action": "clearMarkers"}
    
    @staticmethod
    def fit_bounds() -> Dict:
        """调整视图适应所有标记"""
        return {"action": "fitBounds"}
    
    @staticmethod
    def set_style(style: str) -> Dict:
        """
        设置地图样式
        
        Args:
            style: street/dark/satellite
        """
        return {
            "action": "setMapStyle",
            "style": style
        }


class GeoAnalysisTool:
    """地理分析工具"""
    
    name = "geo_analysis"
    description = "地理分析工具"
    
    @staticmethod
    def search_place(query: str) -> Dict:
        """搜索地点"""
        return {
            "action": "searchPlace",
            "query": query
        }
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算两点距离 (km)"""
        import math
        R = 6371  # 地球半径
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c


class MCPClient:
    """MCP 客户端 - 连接 AI Agent"""
    
    def __init__(self, tools: List[Any] = None):
        self.tools = tools or [MapControlTool(), GeoAnalysisTool()]
        self.available_functions = {
            "addMarker": MapControlTool.add_marker,
            "flyTo": MapControlTool.fly_to,
            "clearMarkers": MapControlTool.clear_markers,
            "fitBounds": MapControlTool.fit_bounds,
            "setMapStyle": MapControlTool.set_style,
            "searchPlace": GeoAnalysisTool.search_place,
            "calculateDistance": GeoAnalysisTool.calculate_distance,
        }
    
    def get_tools_schema(self) -> List[Dict]:
        """获取工具 Schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "addMarker",
                    "description": "在地图上添加标记点",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number", "description": "纬度"},
                            "lng": {"type": "number", "description": "经度"},
                            "title": {"type": "string", "description": "标记标题"},
                            "info": {"type": "string", "description": "详细信息"}
                        },
                        "required": ["lat", "lng", "title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flyTo",
                    "description": "飞向指定位置",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"},
                            "zoom": {"type": "number", "default": 12}
                        },
                        "required": ["lat", "lng"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "setMapStyle",
                    "description": "切换地图样式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "style": {"type": "string", "enum": ["street", "dark", "satellite"]}
                        },
                        "required": ["style"]
                    }
                }
            }
        ]
    
    def execute_function(self, name: str, **kwargs) -> Dict:
        """执行函数"""
        if name in self.available_functions:
            return self.available_functions[name](**kwargs)
        return {"error": f"未知函数: {name}"}


# 全局 MCP 客户端
mcp_client = MCPClient()


def get_mcp_client() -> MCPClient:
    return mcp_client
