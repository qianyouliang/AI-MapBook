/**
 * AI-MapBook 主逻辑
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
    
    // 聊天发送
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
    
    // 显示加载
    showLoading('上传文件中...');
    
    try {
        // 1. 上传文件
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
        
        // 2. 处理文件
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
        
        // 显示数据
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
    // 清除标记
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    
    // 更新列表
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
    
    // 调整视图
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
 * 聊天功能
 */
function toggleChat() {
    document.getElementById('chatContainer').classList.toggle('active');
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const messagesEl = document.getElementById('chatMessages');
    messagesEl.innerHTML += `<div style="margin-bottom: 0.5rem;">👤 ${message}</div>`;
    input.value = '';
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message})
        });
        
        const data = await res.json();
        messagesEl.innerHTML += `<div style="margin-bottom: 0.5rem; color: var(--primary);">🤖 ${data.response}</div>`;
    } catch (error) {
        messagesEl.innerHTML += `<div style="color: #ff4444;">错误: ${error.message}</div>`;
    }
    
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

/**
 * 显示加载
 */
function showLoading(text) {
    document.getElementById('loading').classList.add('active');
    updateStatus(text || '处理中...');
}

/**
 * 隐藏加载
 */
function hideLoading() {
    document.getElementById('loading').classList.remove('active');
}

/**
 * 更新状态
 */
function updateStatus(text) {
    document.getElementById('statusText').textContent = text;
}

// 导出
window.AIMapBook = {
    initMap,
    initEvents,
    displayEvents,
    focusEvent,
    toggleChat,
    sendMessage,
    showLoading,
    hideLoading,
    updateStatus
};
