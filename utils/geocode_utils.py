# # utils.py
from geopy.geocoders import Nominatim, BaiduV3
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

class GeocodeUtils:
    def __init__(self, user_agent="GISerLiu", api_type="free", baidu_key=None):
        """
        初始化GeocodeUtils类，设置用户代理和API类型。
        
        Parameters:
        user_agent (str): 用户代理字符串，默认为"GISerLiu"。
        api_type (str): API类型，"free"使用Nominatim，"baidu"使用百度API。
        baidu_key (str): 百度API的密钥，当api_type为"baidu"时需要提供。
        """
        self.api_type = api_type
        
        if api_type == "free" and len(user_agent)>0:
            self.geolocator = Nominatim(user_agent=user_agent)
        elif api_type == "baidu" and baidu_key is not None:
            self.geolocator = BaiduV3(api_key=baidu_key)
        else:
            raise ValueError("Invalid API type or missing Baidu API key")

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

# 使用示例
# 百度API需要提供密钥
# geocode_utils = GeocodeUtils(api_type="baidu", baidu_key="YourBaiduAPIKey")

# 免费Nominatim API
# geocode_utils = GeocodeUtils(api_type="free")
