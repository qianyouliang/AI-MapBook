"""
MCP 客户端模块
AI-MapBook 地图控制服务
"""
import json
import asyncio
from typing import Dict, List, Optional
import httpx


class MCPClient:
    """MCP 客户端"""
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url or "http://localhost:8080"
        self.session_id = None
        self.tools = []
    
    async def connect(self):
        """连接到 MCP 服务器"""
        try:
            async with httpx.AsyncClient() as client:
                # 发送初始化请求
                resp = await client.post(
                    f"{self.server_url}/initialize",
                    json={
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {}
                        },
                        "clientInfo": {
                            "name": "AI-MapBook",
                            "version": "1.0.0"
                        }
                    },
                    timeout=30.0
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    self.session_id = data.get("sessionId")
                    return True
        except Exception as e:
            print(f"MCP 连接失败: {e}")
        
        return False
    
    async def list_tools(self) -> List[Dict]:
        """列出可用工具"""
        if not self.session_id:
            await self.connect()
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.server_url}/tools/list",
                    json={"sessionId": self.session_id},
                    timeout=30.0
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    self.tools = data.get("tools", [])
                    return self.tools
        except Exception as e:
            print(f"获取工具列表失败: {e}")
        
        return []
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """调用工具"""
        if not self.session_id:
            await self.connect()
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.server_url}/tools/call",
                    json={
                        "sessionId": self.session_id,
                        "name": tool_name,
                        "arguments": arguments
                    },
                    timeout=60.0
                )
                
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"调用工具失败: {e}")
        
        return {"error": str(e)}
    
    async def ping(self) -> bool:
        """健康检查"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.server_url}/health", timeout=5.0)
                return resp.status_code == 200
        except:
            return False


class MapControlClient(MCPClient):
    """地图控制 MCP 客户端"""
    
    def __init__(self, server_url: str = None):
        super().__init__(server_url)
    
    async def add_marker(self, lat: float, lng: float, title: str, info: str = "") -> Dict:
        """添加标记"""
        return await self.call_tool("add_marker", {
            "latitude": lat,
            "longitude": lng,
            "title": title,
            "info": info
        })
    
    async def remove_marker(self, marker_id: str) -> Dict:
        """移除标记"""
        return await self.call_tool("remove_marker", {
            "marker_id": marker_id
        })
    
    async def set_view(self, lat: float, lng: float, zoom: int = 10) -> Dict:
        """设置视图"""
        return await self.call_tool("set_view", {
            "latitude": lat,
            "longitude": lng,
            "zoom": zoom
        })
    
    async def draw_polyline(self, points: List[Dict], color: str = "blue") -> Dict:
        """绘制折线"""
        return await self.call_tool("draw_polyline", {
            "points": points,
            "color": color
        })
    
    async def fit_bounds(self, bounds: List[Dict]) -> Dict:
        """适应边界"""
        return await self.call_tool("fit_bounds", {
            "bounds": bounds
        })


# 全局实例
_mcp_client = None


def get_mcp_client() -> MapControlClient:
    """获取 MCP 客户端"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MapControlClient()
    return _mcp_client
