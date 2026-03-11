"""
导出模块
AI-MapBook 多格式导出
"""
import json
import csv
from io import BytesIO, StringIO
from typing import List, Dict
from datetime import datetime


class Exporter:
    """多格式导出器"""
    
    @staticmethod
    def to_geojson(geo_info_list: List[Dict]) -> BytesIO:
        """导出为 GeoJSON"""
        features = []
        
        for item in geo_info_list:
            if "geocode" in item:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "title": item.get("event_title", ""),
                        "description": item.get("event_content", ""),
                        "address": item.get("address", ""),
                        "type": item.get("event_type", ""),
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            item["geocode"]["longitude"],
                            item["geocode"]["latitude"]
                        ]
                    }
                }
                features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        output = BytesIO()
        output.write(json.dumps(geojson, ensure_ascii=False, indent=2).encode("utf-8"))
        output.seek(0)
        return output
    
    @staticmethod
    def to_kml(geo_info_list: List[Dict]) -> BytesIO:
        """导出为 KML"""
        kml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
        kml_parts.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
        kml_parts.append('<Document>')
        
        for item in geo_info_list:
            if "geocode" in item:
                title = item.get("event_title", "Unknown")
                address = item.get("address", "")
                lat = item["geocode"]["latitude"]
                lon = item["geocode"]["longitude"]
                
                kml_parts.append(f"""
    <Placemark>
        <name>{title}</name>
        <description>{address}</description>
        <Point>
            <coordinates>{lon},{lat},0</coordinates>
        </Point>
    </Placemark>
                """)
        
        kml_parts.append('</Document>')
        kml_parts.append('</kml>')
        
        output = BytesIO()
        output.write("\n".join(kml_parts).encode("utf-8"))
        output.seek(0)
        return output
    
    @staticmethod
    def to_csv(geo_info_list: List[Dict]) -> BytesIO:
        """导出为 CSV"""
        output = StringIO()
        
        fieldnames = ["event_title", "event_type", "address", "event_content", "latitude", "longitude"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in geo_info_list:
            if "geocode" in item:
                row = {
                    "event_title": item.get("event_title", ""),
                    "event_type": item.get("event_type", ""),
                    "address": item.get("address", ""),
                    "event_content": item.get("event_content", ""),
                    "latitude": item["geocode"].get("latitude", ""),
                    "longitude": item["geocode"].get("longitude", ""),
                }
                writer.writerow(row)
        
        output.seek(0)
        return BytesIO(output.getvalue().encode("utf-8"))
    
    @staticmethod
    def to_json(geo_info_list: List[Dict]) -> BytesIO:
        """导出为 JSON"""
        output = BytesIO()
        output.write(json.dumps(geo_info_list, ensure_ascii=False, indent=2).encode("utf-8"))
        output.seek(0)
        return output


def export_data(geo_info_list: List[Dict], format: str = "geojson") -> BytesIO:
    """
    导出数据的便捷函数
    
    Args:
        geo_info_list: 地理信息列表
        format: 导出格式 (geojson, kml, csv, json)
    
    Returns:
        导出数据
    """
    exporter = Exporter()
    
    if format == "geojson":
        return exporter.to_geojson(geo_info_list)
    elif format == "kml":
        return exporter.to_kml(geo_info_list)
    elif format == "csv":
        return exporter.to_csv(geo_info_list)
    elif format == "json":
        return exporter.to_json(geo_info_list)
    else:
        raise ValueError(f"不支持的格式: {format}")
