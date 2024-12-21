import json
import base64
import hashlib
import hmac
import websockets
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode

class GeoInfo:
    def __init__(self, app_id, api_key, api_secret, service_id,patch_id):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.service_id = service_id
        self.patch_id = patch_id
        self.url = "wss://maas-api.cn-huabei-1.xf-yun.com/v1.1/chat"

    def generate_auth_url(self):
        """生成带有鉴权信息的URL"""
        # 获取主机名
        host = self.url.split("://")[1].split("/")[0]
        
        # 生成当前时间戳，采用RFC1123格式
        cur_time = datetime.now()
        date = format_date_time(mktime(cur_time.timetuple()))
        
        # 拼接签名原始字符串
        signature_origin = f"host: {host}\ndate: {date}\nGET /v1.1/chat HTTP/1.1"
        
        # 使用HMAC-SHA256算法生成签名
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        # 对签名进行base64编码
        signature = base64.b64encode(signature_sha).decode('utf-8')
        
        # 生成authorization_origin
        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        
        # 对authorization_origin进行base64编码
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        # 生成最终的鉴权URL
        params = {
            "authorization": authorization,
            "date": date,
            "host": host
        }
        auth_url = f"{self.url}?{urlencode(params)}"
        return auth_url

    async def chat(self, message, temperature=0.1):
        """发送消息并获取响应"""
        auth_url = self.generate_auth_url()
        async with websockets.connect(auth_url) as websocket:
            request = {
                "header": {
                    "app_id": self.app_id,
                    "uid": "12345",
                    "patch_id": [self.patch_id]
                },
                "parameter": {
                    "chat": {
                        "domain": self.service_id,
                        "temperature": temperature
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "user", "content": message}
                        ]
                    }
                }
            }
            await websocket.send(json.dumps(request))
            # 持续接收消息，直到接收到完整的响应
            full_response = ""
            while True:
                try:
                    response = await websocket.recv()
                    response_json = json.loads(response)
                    
                    # 检查是否是分块消息
                    if "payload" in response_json and "choices" in response_json["payload"]:
                        text = response_json["payload"]["choices"]["text"][0]["content"]
                        full_response += text
                    
                    # 检查是否是结束标志
                    if response_json.get("header", {}).get("status") == 2:
                        break
                except websockets.exceptions.ConnectionClosedOK:
                    break
            
            return full_response

