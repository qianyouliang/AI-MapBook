# utils.py
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

class GeocodeUtils:
    def __init__(self, user_agent="GISerLiu"):
        """
        初始化GeocodeUtils类，设置用户代理。
        
        Parameters:
        user_agent (str): 用户代理字符串，默认为"geoapiExercises"。
        """
        self.geolocator = Nominatim(user_agent=user_agent)

    def geocode(self, address):
        """
        地理编码一个地址以获取其纬度和经度。
        
        Parameters:
        address (str): 要地理编码的地址。
        
        Returns:
        dict: 包含纬度、经度和完整地址的字典。
        """
        try:
            location = self.geolocator.geocode(address)
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'address': location.address
                }
            else:
                return {'error': 'Address not found'}
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            return {'error': str(e)}

    def reverse_geocode(self, latitude, longitude):
        """
        反向地理编码纬度和经度以获取地址。
        
        Parameters:
        latitude (float): 要反向地理编码的纬度。
        longitude (float): 要反向地理编码的经度。
        
        Returns:
        dict: 包含完整地址、纬度和经度的字典。
        """
        try:
            location = self.geolocator.reverse((latitude, longitude), exactly_one=True)
            if location:
                return {
                    'address': location.address,
                    'latitude': location.latitude,
                    'longitude': location.longitude
                }
            else:
                return {'error': 'Location not found'}
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            return {'error': str(e)}