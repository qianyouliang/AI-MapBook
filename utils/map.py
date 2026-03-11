import folium
import streamlit as st
from streamlit_folium import st_folium
from shapely.geometry import Point, LineString
import geopandas as gpd
import json
from io import BytesIO
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class EnhancedMap:
    """增强型地图类 - 支持更多交互功能"""
    
    def __init__(self):
        self.tiles_options = {
            "OpenStreetMap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "CartoDB Positron": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            "CartoDB Dark": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Gaode Map": "https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
            "Gaode Satellite": "https://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}",
        }
        self.map = None
        self.features = []
        self.locations = []
        self.markers = []  # 存储标记信息
        self.timeline_data = []  # 时间线数据
        
        # 颜色配置
        self.priority_colors = {
            "重要紧急": "red",
            "重要不紧急": "orange",
            "紧急不重要": "blue",
            "不重要不紧急": "gray"
        }
        
        self.status_colors = {
            "completed": "green",
            "in_progress": "blue",
            "pending": "gray"
        }

    def init_map(self, selected_tile: str = None, center: List[float] = None, zoom: int = 4):
        """
        初始化地图
        
        Args:
            selected_tile: 选中的底图名称
            center: 地图中心坐标 [lat, lon]
            zoom: 缩放级别
        """
        if center is None:
            center = [35.8617, 104.1954]  # 中国中心
        
        if selected_tile is None:
            selected_tile = "OpenStreetMap"
        
        if selected_tile in self.tiles_options:
            tile_url = self.tiles_options[selected_tile]
            self.map = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles=tile_url,
                attr='default'
            )
        else:
            # 默认使用 OpenStreetMap
            self.map = folium.Map(location=center, zoom_start=zoom)
        
        return self.map
    
    def add_marker(
        self,
        info: Dict,
        coordinates: Dict,
        priority: str = None,
        status: str = "pending",
        timestamp: str = None,
        show_popup: bool = True
    ):
        """
        添加标记点
        
        Args:
            info: 事件信息字典
            coordinates: 坐标字典 {latitude, longitude}
            priority: 优先级（影响颜色）
            status: 状态
            timestamp: 时间戳
            show_popup: 是否显示弹出框
        """
        try:
            # 确定图标颜色
            color = self.priority_colors.get(priority, "red")
            if status == "completed":
                color = "green"
            
            # 创建属性信息
            properties = {
                "title": info.get("event_title", "未知事件"),
                "type": info.get("event_type", "未知类型"),
                "content": info.get("event_content", ""),
                "keys": info.get("keys", ""),
                "address": info.get("address", ""),
                "priority": priority,
                "status": status,
                "timestamp": timestamp or datetime.now().isoformat()
            }
            
            feature = {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Point",
                    "coordinates": [coordinates["longitude"], coordinates["latitude"]]
                }
            }
            
            self.locations.append([coordinates["latitude"], coordinates["longitude"]])
            
            # 构建弹出框内容
            if show_popup:
                popup_content = self._create_popup_content(properties)
                
                marker = folium.Marker(
                    location=[coordinates["latitude"], coordinates["longitude"]],
                    popup=folium.Popup(popup_content, max_width=400),
                    icon=folium.Icon(color=color, icon="info-sign"),
                    tooltip=properties["title"]  # 鼠标悬停显示标题
                )
            else:
                marker = folium.Marker(
                    location=[coordinates["latitude"], coordinates["longitude"]],
                    icon=folium.Icon(color=color, icon="info-sign"),
                    tooltip=properties["title"]
                )
            
            marker.add_to(self.map)
            
            # 保存标记信息
            self.markers.append({
                "marker": marker,
                "properties": properties,
                "coordinates": coordinates
            })
            
            self.features.append(feature)
            
            # 如果有时间信息，添加到时间线
            if timestamp:
                self.timeline_data.append({
                    "title": properties["title"],
                    "timestamp": timestamp,
                    "coordinates": coordinates,
                    "properties": properties
                })
            
        except Exception as exc:
            print(f"Error adding marker: {exc}")
    
    def _create_popup_content(self, properties: Dict) -> str:
        """创建弹出框内容"""
        # 状态图标
        status_icon = "✅" if properties["status"] == "completed" else "⏳"
        
        popup = f"""
        <div style="min-width: 250px; font-family: Arial, sans-serif;">
            <h4 style="margin-bottom: 10px; color: #333;">
                {status_icon} {properties['title']}
            </h4>
            <table style="width: 100%; font-size: 13px;">
                <tr>
                    <td style="font-weight: bold; color: #666;">类型</td>
                    <td>{properties.get('type', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #666;">地址</td>
                    <td>{properties.get('address', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #666;">优先级</td>
                    <td>{properties.get('priority', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #666;">关键词</td>
                    <td>{properties.get('keys', 'N/A')}</td>
                </tr>
            </table>
            <div style="margin-top: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px;">
                <small style="color: #666;">{properties.get('content', '')[:100]}...</small>
            </div>
        </div>
        """
        return popup
    
    def add_polyline(
        self,
        locations: List = None,
        color: str = "blue",
        weight: float = 2.5,
        opacity: float = 1.0,
        show_arrows: bool = True,
        dash_array: str = None
    ):
        """
        添加折线（路径）
        
        Args:
            locations: 坐标点列表 [[lat, lon], ...]
            color: 线条颜色
            weight: 线宽
            opacity: 透明度
            show_arrows: 是否显示箭头
            dash_array: 虚线样式
        """
        if locations is None:
            locations = self.locations
        
        if len(locations) < 2:
            return
        
        # 创建折线
        if dash_array:
            line = folium.PolyLine(
                locations,
                color=color,
                weight=weight,
                opacity=opacity,
                dash_array=dash_array
            )
        else:
            line = folium.PolyLine(
                locations,
                color=color,
                weight=weight,
                opacity=opacity
            )
        
        line.add_to(self.map)
        
        # 添加方向箭头
        if show_arrows:
            self._add_direction_arrows(locations, color)
    
    def _add_direction_arrows(self, locations: List, color: str):
        """添加方向箭头"""
        for i in range(len(locations) - 1):
            dx = locations[i + 1][0] - locations[i][0]
            dy = locations[i + 1][1] - locations[i][1]
            angle = -int(math.atan2(dx, dy) * 180 / math.pi)
            
            mid_location = [
                (locations[i][0] + locations[i + 1][0]) / 2,
                (locations[i][1] + locations[i + 1][1]) / 2
            ]
            
            folium.RegularPolygonMarker(
                location=mid_location,
                fill_color=color,
                number_of_sides=3,
                radius=6,
                rotation=angle
            ).add_to(self.map)
    
    def add_circle(
        self,
        center: List[float],
        radius: float = 1000,
        color: str = "blue",
        fill_color: str = "blue",
        fill_opacity: float = 0.3,
        popup: str = None
    ):
        """
        添加圆形区域
        
        Args:
            center: 中心坐标 [lat, lon]
            radius: 半径（米）
            color: 边框颜色
            fill_color: 填充颜色
            fill_opacity: 填充透明度
            popup: 弹出框内容
        """
        folium.Circle(
            location=center,
            radius=radius,
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            popup=popup
        ).add_to(self.map)
    
    def add_heatmap(self, data: List[Dict], radius: int = 15):
        """
        添加热力图
        
        Args:
            data: 数据列表 [{latitude, longitude, weight}, ...]
            radius: 热力图半径
        """
        from folium.plugins import HeatMap
        
        heat_data = [
            [item["latitude"], item["longitude"], item.get("weight", 1)]
            for item in data
        ]
        
        HeatMap(heat_data, radius=radius).add_to(self.map)
    
    def add_timeline(self):
        """添加时间线控件"""
        from folium.plugins import TimestampedGeoJson
        
        if not self.timeline_data:
            return
        
        # 按时间排序
        sorted_data = sorted(self.timeline_data, key=lambda x: x.get("timestamp", ""))
        
        # 创建 GeoJSON 特征集合
        features = []
        for item in sorted_data:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        item["coordinates"]["longitude"],
                        item["coordinates"]["latitude"]
                    ]
                },
                "properties": {
                    "time": item.get("timestamp", ""),
                    "popup": item["title"],
                    "icon": "marker",
                    "style": {"color": "red"}
                }
            })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        TimestampedGeoJson(geojson, period="P1D", add_last_point=True).add_to(self.map)
    
    def fit_bounds(self, padding: Tuple[int, int] = (50, 50)):
        """
        自动调整视图以适应所有标记
        
        Args:
            padding: 内边距
        """
        if self.locations and self.map:
            self.map.fit_bounds(self.locations, padding=padding)
    
    def fly_to(self, latitude: float, longitude: float, zoom_level: int = 12):
        """飞向指定位置"""
        if self.map is not None:
            self.map.location = [latitude, longitude]
            self.map.zoom_start = zoom_level
    
    def add_layer_control(self):
        """添加图层控制"""
        folium.LayerControl().add_to(self.map)
    
    def add_fullscreen_control(self):
        """添加全屏控件"""
        from folium.plugins import Fullscreen
        Fullscreen().add_to(self.map)
    
    def add_minimap(self):
        """添加小地图"""
        from folium.plugins import MiniMap
        MiniMap().add_to(self.map)
    
    def add_measure_control(self):
        """添加测量控件"""
        from folium.plugins import MeasureControl
        MeasureControl().add_to(self.map)
    
    def display(self, width: int = None, height: int = None):
        """
        显示地图
        
        Args:
            width: 宽度
            height: 高度
        """
        if self.map is not None:
            st_folium(self.map, width=width, height=height)
        else:
            st.warning("地图未初始化")
    
    def export_geojson(self) -> BytesIO:
        """导出 GeoJSON"""
        geojson_data = {
            "type": "FeatureCollection",
            "features": self.features
        }
        geojson_str = json.dumps(geojson_data, indent=2, ensure_ascii=False)
        b = BytesIO()
        b.write(geojson_str.encode('utf-8'))
        b.seek(0)
        return b
    
    def get_statistics(self) -> Dict:
        """获取地图统计信息"""
        return {
            "total_markers": len(self.markers),
            "total_features": len(self.features),
            "locations_count": len(self.locations),
            "timeline_events": len(self.timeline_data),
            "bounds": self.map.bounds if self.map else None
        }
    
    def clear(self):
        """清除所有标记"""
        self.features = []
        self.locations = []
        self.markers = []
        self.timeline_data = []
        if self.map:
            self.map = self.init_map()


# 兼容性：保留原 Map 类
Map = EnhancedMap
