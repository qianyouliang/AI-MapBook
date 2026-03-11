"""
Flask 应用入口
AI-MapBook - 复古科技风格
"""
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid

# 导入核心模块
from core.llm import LLMModel
from core.rag import RAGModel
from core.geocode import GeocodeModel
from config.settings import config

# 初始化 Flask
app = Flask(__name__, 
    template_folder='templates',
    static_folder='static')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = config.DATA_DIR
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE

# 初始化目录
config.init_dirs()

# 全局模型实例
llm_model = None
rag_model = None
geocode_model = None

# 当前处理的数据
current_geo_data = []


def get_llm():
    """获取 LLM 实例"""
    global llm_model
    if llm_model is None:
        try:
            llm_model = LLMModel()
        except Exception as e:
            print(f"LLM 初始化失败: {e}")
    return llm_model


def get_rag():
    """获取 RAG 实例"""
    global rag_model
    if rag_model is None:
        rag_model = RAGModel()
    return rag_model


def get_geocode(api_type="free", baidu_key=None):
    """获取地理编码实例"""
    global geocode_model
    if geocode_model is None or geocode_model.api_type != api_type:
        geocode_model = GeocodeModel(api_type=api_type, baidu_key=baidu_key)
    return geocode_model


# 路由
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 保存文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'filepath': filepath
    })


@app.route('/api/process', methods=['POST'])
def process_file():
    """处理文件"""
    global current_geo_data
    
    data = request.json
    filename = data.get('filename')
    use_rag = data.get('use_rag', False)
    geocode_type = data.get('geocode_type', 'free')
    baidu_key = data.get('baidu_key', '')
    
    if not filename:
        return jsonify({'error': '没有文件名'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 400
    
    # 获取模型
    llm = get_llm()
    geocode = get_geocode(geocode_type, baidu_key)
    
    if not llm:
        return jsonify({'error': 'LLM 未初始化，请检查 API Key'}), 500
    
    # 读取文件
    try:
        if filename.endswith('.pdf'):
            from utils.pdf_reader import read_pdf
            text_list = read_pdf(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                text_list = [text[i:i+5000] for i in range(0, len(text), 5000)]
    except Exception as e:
        return jsonify({'error': f'读取文件失败: {str(e)}'}), 500
    
    # 处理文本
    current_geo_data = []
    
    for text in text_list:
        events = llm.get_event_list(text)
        
        for event in events:
            event_info = llm.process_event(event)
            
            # 地理编码
            if event_info.get('address'):
                geo_result = geocode.geocode(event_info['address'])
                if geo_result:
                    event_info['geocode'] = geo_result
                    current_geo_data.append(event_info)
    
    return jsonify({
        'success': True,
        'count': len(current_geo_data),
        'data': current_geo_data
    })


@app.route('/api/geojson')
def get_geojson():
    """获取 GeoJSON 数据"""
    global current_geo_data
    
    features = []
    for item in current_geo_data:
        if 'geocode' in item:
            features.append({
                "type": "Feature",
                "properties": {
                    "title": item.get('event_title', ''),
                    "type": item.get('event_type', ''),
                    "content": item.get('event_content', ''),
                    "address": item.get('address', '')
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        item['geocode']['longitude'],
                        item['geocode']['latitude']
                    ]
                }
            })
    
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口 - 支持 Agent 控制地图"""
    data = request.json
    message = data.get('message', '')
    
    llm = get_llm()
    if not llm:
        return jsonify({'error': 'LLM 未初始化'}), 500
    
    # 对话
    response = llm.chat([
        {"role": "system", "content": """你是 AI-MapBook 助手，可以控制地图。
        
可用的地图控制命令：
- 添加标记: 在地图上添加一个标记点
- 移除标记: 移除指定的标记
- 设置视图: 移动地图到指定位置
- 绘制路径: 在地图上绘制一条路径

当用户请求时，自动执行相应的地图操作。
返回结果时，使用 Markdown 格式。"""},
        {"role": "user", "content": message}
    ], stream=False)
    
    response_text = response.choices[0].message.content
    
    # 检测是否需要执行地图操作
    # 这里可以集成更复杂的 Agent 来自动执行
    
    return jsonify({
        'response': response_text
    })


@app.route('/api/map/add_marker', methods=['POST'])
def map_add_marker():
    """添加标记"""
    data = request.json
    return jsonify({
        'success': True,
        'action': 'add_marker',
        'data': data
    })


@app.route('/api/map/set_view', methods=['POST'])
def map_set_view():
    """设置视图"""
    data = request.json
    return jsonify({
        'success': True,
        'action': 'set_view',
        'data': data
    })


@app.route('/api/mcp/status', methods=['GET'])
def mcp_status():
    """MCP 服务状态"""
    return jsonify({
        'connected': False,
        'message': 'MCP 服务未连接'
    })


# PDF 读取工具
def read_pdf(filepath):
    """读取 PDF 文件"""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(filepath)
        text_list = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_list.append(text)
        return text_list
    except Exception as e:
        print(f"PDF 读取错误: {e}")
        return []





@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天接口"""
    from flask import Response
    
    data = request.json
    message = data.get('message', '')
    
    llm = get_llm()
    if not llm:
        return jsonify({'error': 'LLM 未初始化'}), 500
    
    def generate():
        try:
            response = llm.chat([
                {"role": "system", "content": """你是 AI-MapBook 助手，专门帮助用户处理地理信息。
你可以根据需要控制地图，调用前端函数：
- AIMapBook.addMarker(lat, lng, title, info) - 添加标记
- AIMapBook.flyTo(lat, lng, zoom) - 飞向位置
- AIMapBook.clearMarkers() - 清除标记
- AIMapBook.setMapStyle(style) - 切换底图 (street/dark/satellite)
- AIMapBook.fitBounds() - 调整视图"""},
                {"role": "user", "content": message}
            ], stream=True)
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"\n\n[错误: {str(e)}]"
    
    return Response(generate(), mimetype='text/event-stream')


# MCP 工具集成
from core.mcp import get_mcp_client, MapControlTool

@app.route('/api/mcp/tools', methods=['GET'])
def get_mcp_tools():
    """获取 MCP 工具列表"""
    mcp = get_mcp_client()
    return jsonify({
        "tools": mcp.get_tools_schema()
    })


@app.route('/api/mcp/execute', methods=['POST'])
def execute_mcp():
    """执行 MCP 工具"""
    data = request.json
    function_name = data.get('function')
    arguments = data.get('arguments', {})
    
    mcp = get_mcp_client()
    result = mcp.execute_function(function_name, **arguments)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
