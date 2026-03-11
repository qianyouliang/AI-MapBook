"""
地理编码模块
AI-MapBook 地理编码功能
"""
from typing import Dict, Optional

try:
    from geopy.geocoders import Nominatim, BaiduV3
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False


class GeocodeModel:
    """地理编码模型"""
    
    def __init__(self, api_type: str = "free", user_agent: str = "AI-MapBook", baidu_key: str = None):
        self.api_type = api_type
        self.geolocator = None
        
        if not GEOPY_AVAILABLE:
            return
        
        if api_type == "free":
            self.geolocator = Nominatim(user_agent=user_agent)
        elif api_type == "baidu" and baidu_key:
            self.geolocator = BaiduV3(api_key=baidu_key)
    
    def geocode(self, address: str) -> Optional[Dict]:
        """地理编码"""
        if not self.geolocator:
            return None
        
        try:
            location = self.geolocator.geocode(address)
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'address': location.address
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"地理编码错误: {e}")
        
        return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """反向地理编码"""
        if not self.geolocator:
            return None
        
        try:
            location = self.geolocator.reverse((lat, lon), exactly_one=True)
            if location:
                return {
                    'address': location.address,
                    'latitude': location.latitude,
                    'longitude': location.longitude
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"反向地理编码错误: {e}")
        
        return None
