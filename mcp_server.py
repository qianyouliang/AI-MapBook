"""
简单的地图控制 MCP 服务
用于测试和演示
"""
from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# 存储标记
markers = {}
polylines = {}


@app.route('/initialize', methods=['POST'])
def initialize():
    """初始化连接"""
    return jsonify({
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "AI-MapBook Map Control",
            "version": "1.0.0"
        },
        "sessionId": str(uuid.uuid4())
    })


@app.route('/tools/list', methods=['POST'])
def list_tools():
    """列出可用工具"""
    return jsonify({
        "tools": [
            {
                "name": "add_marker",
                "description": "在地图上添加标记",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "title": {"type": "string"},
                        "info": {"type": "string"}
                    },
                    "required": ["latitude", "longitude", "title"]
                }
            },
            {
                "name": "remove_marker",
                "description": "移除标记",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "marker_id": {"type": "string"}
                    },
                    "required": ["marker_id"]
                }
            },
            {
                "name": "set_view",
                "description": "设置地图视图",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "zoom": {"type": "number"}
                    },
                    "required": ["latitude", "longitude"]
                }
            },
            {
                "name": "draw_polyline",
                "description": "绘制折线路径",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "points": {"type": "array"},
                        "color": {"type": "string"}
                    },
                    "required": ["points"]
                }
            }
        ]
    })


@app.route('/tools/call', methods=['POST'])
def call_tool():
    """调用工具"""
    data = request.json
    tool_name = data.get("name")
    args = data.get("arguments", {})
    
    if tool_name == "add_marker":
        marker_id = str(uuid.uuid4())[:8]
        markers[marker_id] = {
            "id": marker_id,
            "lat": args.get("latitude"),
            "lng": args.get("longitude"),
            "title": args.get("title"),
            "info": args.get("info", "")
        }
        return jsonify({
            "content": [{
                "type": "text",
                "text": f"已添加标记: {args.get('title')} (ID: {marker_id})"
            }]
        })
    
    elif tool_name == "remove_marker":
        marker_id = args.get("marker_id")
        if marker_id in markers:
            del markers[marker_id]
            return jsonify({
                "content": [{
                    "type": "text",
                    "text": f"已移除标记: {marker_id}"
                }]
            })
        return jsonify({
            "content": [{
                "type": "text",
                "text": f"标记不存在: {marker_id}"
            }]
        })
    
    elif tool_name == "set_view":
        return jsonify({
            "content": [{
                "type": "text",
                "text": f"视图已设置: ({args.get('latitude')}, {args.get('longitude')}), zoom: {args.get('zoom', 10)}"
            }]
        })
    
    elif tool_name == "draw_polyline":
        line_id = str(uuid.uuid4())[:8]
        polylines[line_id] = {
            "id": line_id,
            "points": args.get("points", []),
            "color": args.get("color", "blue")
        }
        return jsonify({
            "content": [{
                "type": "text",
                "text": f"已绘制折线: {len(args.get('points', []))} 个点 (ID: {line_id})"
            }]
        })
    
    return jsonify({"error": "Unknown tool"})


@app.route('/state', methods=['GET'])
def get_state():
    """获取当前状态"""
    return jsonify({
        "markers": markers,
        "polylines": polylines
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
