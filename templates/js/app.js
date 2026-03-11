/**
 * AI-MapBook 主逻辑 - 支持流式输出
 */

// 全局变量
let map;
let markers = [];
let geoData = [];

/**
 * 初始化地图
 */
function initMap() {
    map = L.map('map').setView([35.8617, 104.1954], 4);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);
}

/**
 * 初始化事件监听
 */
function initEvents() {
    // 文件上传
    document.getElementById('fileInput').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('fileName').textContent = file.name;
        }
    });
    
    // 地理编码类型切换
    document.getElementById('geocodeType').addEventListener('change', function(e) {
        const baiduGroup = document.getElementById('baiduKeyGroup');
        baiduGroup.style.display = e.target.value === 'baidu' ? 'block' : 'none';
    });
    
    // 处理按钮
    document.getElementById('processBtn').addEventListener('click', processFile);
    
    // 聊天输入 - 回车发送
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

/**
 * 处理文件
 */
async function processFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('请先选择文件');
        return;
    }
    
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        alert('请输入 API Key');
        return;
    }
    
    showLoading('上传文件中...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadRes = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const uploadData = await uploadRes.json();
        
        if (!uploadData.success) {
            throw new Error(uploadData.error);
        }
        
        showLoading('处理中...');
        
        const processRes = await fetch('/api/process', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                filename: uploadData.filename,
                api_key: apiKey,
                geocode_type: document.getElementById('geocodeType').value,
                baidu_key: document.getElementById('baiduKey').value,
                use_rag: document.getElementById('useRag').checked
            })
        });
        
        const processData = await processRes.json();
        
        if (!processData.success) {
            throw new Error(processData.error);
        }
        
        geoData = processData.data;
        displayEvents(geoData);
        
        updateStatus(`处理完成，共 ${geoData.length} 个事件`);
        
    } catch (error) {
        alert('处理失败: ' + error.message);
        updateStatus('处理失败');
    } finally {
        hideLoading();
    }
}

/**
 * 显示事件
 */
function displayEvents(data) {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    
    const listEl = document.getElementById('eventList');
    document.getElementById('eventCount').textContent = `(${data.length})`;
    
    if (data.length === 0) {
        listEl.innerHTML = '<div style="color: #666; text-align: center; padding: 1rem;">暂无事件数据</div>';
        return;
    }
    
    let html = '';
    data.forEach((item, index) => {
        if (item.geocode) {
            const lat = item.geocode.latitude;
            const lng = item.geocode.longitude;
            
            const marker = L.marker([lat, lng])
                .addTo(map)
                .bindPopup(`
                    <strong>${item.event_title}</strong><br>
                    <small>${item.event_type}</small><br>
                    <small>📍 ${item.address}</small>
                `);
            markers.push(marker);
            
            html += `
                <div class="event-item" onclick="focusEvent(${index})">
                    <div class="event-title">${item.event_title}</div>
                    <div class="event-address">📍 ${item.address}</div>
                </div>
            `;
        }
    });
    
    listEl.innerHTML = html;
    
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

/**
 * 聚焦事件
 */
function focusEvent(index) {
    const item = geoData[index];
    if (item.geocode) {
        map.setView([item.geocode.latitude, item.geocode.longitude], 10);
        markers[index].openPopup();
    }
}

/**
 * 聊天功能 - 流式输出 + MCP 工具
 */
function toggleChat() {
    document.getElementById('chatContainer').classList.toggle('active');
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const messagesEl = document.getElementById('chatMessages');
    
    // 用户消息 (Markdown)
    const userMsg = document.createElement('div');
    userMsg.style.marginBottom = '0.8rem';
    userMsg.innerHTML = `<div style="color: var(--secondary); margin-bottom: 4px;">👤</div><div class="markdown-body" style="background: rgba(0,50,80,0.3); padding: 8px; border-radius: 4px;">${marked.parse(message)}</div>`;
    messagesEl.appendChild(userMsg);
    
    input.value = '';
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    // AI 响应占位
    const aiMsg = document.createElement('div');
    aiMsg.style.marginBottom = '0.8rem';
    const timestamp = Date.now();
    aiMsg.id = 'ai-' + timestamp;
    aiMsg.innerHTML = `<div style="color: var(--primary); margin-bottom: 4px;">🤖</div><div class="markdown-body typing"></div>`;
    messagesEl.appendChild(aiMsg);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    let fullResponse = '';
    let executingTool = false;
    
    try {
        const res = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message, use_mcp: true})
        });
        
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            
            // 检查是否是工具调用指令
            if (chunk.startsWith('[TOOL:')) {
                const toolEnd = chunk.indexOf(']');
                if (toolEnd > 0) {
                    const toolCall = JSON.parse(chunk.slice(6, toolEnd));
                    executingTool = true;
                    
                    // 执行工具
                    await executeTool(toolCall.name, toolCall.args);
                    
                    // 添加工具执行结果
                    const toolResult = `\n\n✅ 已执行: ${toolCall.name}`;
                    fullResponse += toolResult;
                    
                    const typingEl = document.getElementById('ai-' + timestamp).querySelector('.typing');
                    typingEl.innerHTML = marked.parse(fullResponse);
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                    executingTool = false;
                }
            } else {
                fullResponse += chunk;
                
                const typingEl = document.getElementById('ai-' + timestamp).querySelector('.typing');
                typingEl.innerHTML = marked.parse(fullResponse);
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        }
        
    } catch (error) {
        const errorEl = document.getElementById('ai-' + timestamp).querySelector('.typing');
        errorEl.innerHTML = `<span style="color: #ff4444;">错误: ${error.message}</span>`;
    }
}

/**
 * 执行 MCP 工具
 */
async function executeTool(name, args) {
    try {
        const res = await fetch('/api/mcp/execute', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                function: name,
                arguments: args
            })
        });
        
        const result = await res.json();
        console.log('Tool result:', result);
        
        // 根据结果执行地图操作
        if (result.action === 'addMarker' && result.lat) {
            AIMapBook.addMarker(result.lat, result.lng, result.title, result.info);
        } else if (result.action === 'flyTo') {
            AIMapBook.flyTo(result.lat, result.lng, result.zoom);
        } else if (result.action === 'clearMarkers') {
            AIMapBook.clearMarkers();
        } else if (result.action === 'fitBounds') {
            AIMapBook.fitBounds();
        } else if (result.action === 'setMapStyle') {
            AIMapBook.setMapStyle(result.style);
        }
        
    } catch (e) {
        console.error('Tool execution failed:', e);
    }
}

/**
 * 地图控制 - Agent 调用
 */
function addMarker(lat, lng, title, info) {
    const marker = L.marker([lat, lng])
        .addTo(map)
        .bindPopup(`<strong>${title}</strong><br>${info}`);
    markers.push(marker);
    return marker;
}

function flyTo(lat, lng, zoom = 12) {
    map.flyTo([lat, lng], zoom);
}

function fitBounds() {
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function clearMarkers() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
}

function setMapStyle(style) {
    // 切换底图
    const styles = {
        'street': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'dark': 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        'satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    };
    
    // 清除所有图层
    map.eachLayer(layer => {
        if (layer instanceof L.TileLayer) {
            map.removeLayer(layer);
        }
    });
    
    L.tileLayer(styles[style] || styles.street).addTo(map);
}

/**
 * 显示/隐藏加载
 */
function showLoading(text) {
    document.getElementById('loading').classList.add('active');
    updateStatus(text || '处理中...');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('active');
}

function updateStatus(text) {
    document.getElementById('statusText').textContent = text;
}

// 导出供外部调用
window.AIMapBook = {
    initMap,
    initEvents,
    displayEvents,
    focusEvent,
    toggleChat,
    sendMessage,
    showLoading,
    hideLoading,
    updateStatus,
    // 地图控制
    addMarker,
    flyTo,
    fitBounds,
    clearMarkers,
    setMapStyle
};
