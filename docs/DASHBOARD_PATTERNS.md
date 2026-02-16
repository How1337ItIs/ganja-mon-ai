# Real-time Dashboard Patterns for Grok & Mon

Comprehensive guide for building real-time monitoring dashboards for IoT cannabis cultivation systems.

## Overview

Grok & Mon requires a real-time dashboard to display:
- Live sensor data (temperature, humidity, VPD, CO2, soil moisture)
- AI decision logs and commentary
- Plant images/webcam feed
- Growth stage progress
- Token metrics (if integrated)
- Historical charts and trends

---

## Architecture Options

### 1. WebSocket (Recommended)

**Best for:** Real-time bidirectional communication

**Pros:**
- Low latency
- Full-duplex communication
- Efficient for frequent updates
- Works well with MQTT bridge

**Cons:**
- More complex to implement
- Requires connection management
- May need reconnection logic

### 2. Server-Sent Events (SSE)

**Best for:** One-way server-to-client updates

**Pros:**
- Simpler than WebSocket
- Automatic reconnection
- HTTP-based (easier firewall traversal)
- Good for sensor data streaming

**Cons:**
- One-way only (server → client)
- Less efficient than WebSocket
- Limited browser support (though good now)

### 3. MQTT over WebSocket

**Best for:** Direct IoT device communication

**Pros:**
- Direct connection to MQTT broker
- Efficient for IoT devices
- Standard protocol
- Can use existing MQTT infrastructure

**Cons:**
- Requires MQTT broker
- More complex setup
- May need authentication layer

**Recommendation:** Use WebSocket for main dashboard, MQTT over WebSocket for direct device access.

---

## Implementation: WebSocket Dashboard

### Backend (FastAPI)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json
from datetime import datetime

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            # Handle client requests (e.g., request historical data)
            if data == "get_history":
                await websocket.send_json({
                    "type": "history",
                    "data": get_historical_data()
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to broadcast sensor updates
async def broadcast_sensor_updates():
    """Continuously broadcast sensor data."""
    while True:
        sensor_data = get_latest_sensor_data()
        await manager.broadcast({
            "type": "sensor_update",
            "timestamp": datetime.now().isoformat(),
            "data": sensor_data
        })
        await asyncio.sleep(5)  # Update every 5 seconds

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_sensor_updates())
```

### Frontend (JavaScript)

```javascript
class DashboardWebSocket {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = 5000;
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.listeners = {};
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.onConnect();
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.onDisconnect();
            this.reconnect();
        };
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectInterval);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    onConnect() {
        // Request initial data
        this.send('get_history');
    }
    
    onDisconnect() {
        // Show connection status
        this.updateConnectionStatus(false);
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        }
    }
    
    handleMessage(message) {
        const { type, data, timestamp } = message;
        
        switch (type) {
            case 'sensor_update':
                this.updateSensorDisplay(data);
                break;
            case 'ai_decision':
                this.updateAIDecision(data);
                break;
            case 'history':
                this.loadHistoricalData(data);
                break;
            default:
                console.log('Unknown message type:', type);
        }
    }
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }
    
    updateSensorDisplay(data) {
        // Update temperature
        document.getElementById('temperature').textContent = 
            `${data.temperature_f.toFixed(1)}°F`;
        
        // Update humidity
        document.getElementById('humidity').textContent = 
            `${data.humidity_percent.toFixed(1)}%`;
        
        // Update VPD
        document.getElementById('vpd').textContent = 
            `${data.vpd_kpa.toFixed(2)} kPa`;
        
        // Update charts
        this.addDataPoint('temperature', data.temperature_f);
        this.addDataPoint('humidity', data.humidity_percent);
        this.addDataPoint('vpd', data.vpd_kpa);
    }
    
    updateAIDecision(data) {
        const decisionEl = document.getElementById('ai-decision');
        decisionEl.innerHTML = `
            <div class="decision-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
            <div class="decision-commentary">${data.commentary}</div>
            <div class="decision-actions">
                ${data.actions.map(a => `<div>${a.tool}: ${JSON.stringify(a.parameters)}</div>`).join('')}
            </div>
        `;
    }
    
    addDataPoint(metric, value) {
        // Add to chart.js or other charting library
        if (window.charts && window.charts[metric]) {
            const chart = window.charts[metric];
            const now = new Date();
            chart.data.labels.push(now.toLocaleTimeString());
            chart.data.datasets[0].data.push(value);
            
            // Keep only last 100 points
            if (chart.data.labels.length > 100) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update('none'); // 'none' = no animation for real-time updates
        }
    }
    
    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        statusEl.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
        statusEl.className = connected ? 'connected' : 'disconnected';
    }
}

// Initialize
const dashboard = new DashboardWebSocket('ws://localhost:8000/ws');
dashboard.connect();
```

---

## Chart Libraries

### 1. Chart.js (Recommended)

**Best for:** Simple, responsive charts

```javascript
// Temperature chart
const tempCtx = document.getElementById('temperature-chart').getContext('2d');
const tempChart = new Chart(tempCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Temperature (°F)',
            data: [],
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false, // Disable animation for real-time updates
        scales: {
            y: {
                beginAtZero: false,
                min: 60,
                max: 90
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    }
});

window.charts = { temperature: tempChart };
```

### 2. ApexCharts

**Best for:** Advanced features, animations

```javascript
const tempChart = new ApexCharts(document.querySelector("#temperature-chart"), {
    chart: {
        type: 'line',
        height: 300,
        animations: {
            enabled: false // Disable for real-time
        }
    },
    series: [{
        name: 'Temperature',
        data: []
    }],
    xaxis: {
        type: 'datetime'
    },
    yaxis: {
        min: 60,
        max: 90
    }
});

tempChart.render();

// Add data point
function addTemperaturePoint(value) {
    tempChart.appendData([{
        data: [{
            x: new Date(),
            y: value
        }]
    }], true); // true = shift old data
}
```

### 3. Recharts (React)

**Best for:** React applications

```jsx
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts';

function TemperatureChart({ data }) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
                <XAxis dataKey="time" />
                <YAxis domain={[60, 90]} />
                <Line 
                    type="monotone" 
                    dataKey="temperature" 
                    stroke="#ff6384"
                    dot={false}
                    isAnimationActive={false}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}
```

---

## Real-time Gauge Components

### Circular Gauge (Temperature)

```javascript
// Using Chart.js gauge plugin or custom canvas
function drawTemperatureGauge(canvas, value, min = 60, max = 90) {
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 20;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw background arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 0);
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 20;
    ctx.stroke();
    
    // Calculate angle for value
    const normalizedValue = (value - min) / (max - min);
    const angle = Math.PI - (normalizedValue * Math.PI);
    
    // Draw value arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, angle);
    ctx.strokeStyle = getTemperatureColor(value);
    ctx.lineWidth = 20;
    ctx.stroke();
    
    // Draw value text
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`${value.toFixed(1)}°F`, centerX, centerY + 10);
}

function getTemperatureColor(temp) {
    if (temp < 70) return '#4a90e2'; // Blue (cool)
    if (temp < 80) return '#50c878'; // Green (optimal)
    if (temp < 85) return '#ffa500'; // Orange (warm)
    return '#ff4444'; // Red (hot)
}
```

### Linear Progress Bar (Soil Moisture)

```html
<div class="gauge-container">
    <div class="gauge-label">Soil Moisture</div>
    <div class="gauge-bar">
        <div class="gauge-fill" id="soil-moisture-fill" style="width: 0%"></div>
    </div>
    <div class="gauge-value" id="soil-moisture-value">0%</div>
</div>
```

```css
.gauge-container {
    margin: 20px 0;
}

.gauge-label {
    font-size: 14px;
    color: #aaa;
    margin-bottom: 5px;
}

.gauge-bar {
    width: 100%;
    height: 30px;
    background: #333;
    border-radius: 15px;
    overflow: hidden;
    position: relative;
}

.gauge-fill {
    height: 100%;
    background: linear-gradient(90deg, #4a90e2 0%, #50c878 50%, #ff4444 100%);
    transition: width 0.3s ease;
    border-radius: 15px;
}

.gauge-value {
    text-align: center;
    margin-top: 5px;
    font-size: 18px;
    font-weight: bold;
}
```

```javascript
function updateSoilMoisture(value) {
    const fill = document.getElementById('soil-moisture-fill');
    const valueEl = document.getElementById('soil-moisture-value');
    
    fill.style.width = `${value}%`;
    valueEl.textContent = `${value.toFixed(1)}%`;
    
    // Change color based on value
    if (value < 30) {
        fill.style.background = '#ff4444'; // Red (dry)
    } else if (value < 60) {
        fill.style.background = '#50c878'; // Green (optimal)
    } else {
        fill.style.background = '#4a90e2'; // Blue (wet)
    }
}
```

---

## Mobile-Responsive Layout

### CSS Grid Layout

```css
.dashboard-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    padding: 20px;
}

.sensor-card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 20px;
}

.sensor-card h3 {
    margin: 0 0 10px 0;
    color: #fff;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.sensor-value {
    font-size: 32px;
    font-weight: bold;
    color: #50c878;
    margin: 10px 0;
}

.chart-container {
    grid-column: 1 / -1; /* Full width on mobile */
    min-height: 300px;
}

@media (min-width: 768px) {
    .chart-container {
        grid-column: span 2; /* 2 columns on tablet */
    }
}

@media (min-width: 1024px) {
    .chart-container {
        grid-column: span 3; /* 3 columns on desktop */
    }
}
```

---

## Dark Theme Design

### Color Palette

```css
:root {
    /* Background */
    --bg-primary: #0a0a0a;
    --bg-secondary: #1a1a1a;
    --bg-tertiary: #2a2a2a;
    
    /* Text */
    --text-primary: #ffffff;
    --text-secondary: #aaaaaa;
    --text-muted: #666666;
    
    /* Accents */
    --accent-green: #50c878;
    --accent-blue: #4a90e2;
    --accent-orange: #ffa500;
    --accent-red: #ff4444;
    --accent-purple: #9b59b6;
    
    /* Borders */
    --border-color: #333333;
    
    /* Status */
    --status-online: #50c878;
    --status-offline: #ff4444;
    --status-warning: #ffa500;
}
```

### Terminal/Console Aesthetic

```css
.console-output {
    background: #0a0a0a;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 15px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    color: #50c878;
    max-height: 400px;
    overflow-y: auto;
}

.console-line {
    margin: 5px 0;
    line-height: 1.5;
}

.console-line.info {
    color: #4a90e2;
}

.console-line.success {
    color: #50c878;
}

.console-line.warning {
    color: #ffa500;
}

.console-line.error {
    color: #ff4444;
}

.console-timestamp {
    color: #666;
    margin-right: 10px;
}
```

---

## Performance Optimization

### 1. Throttle Updates

```javascript
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Throttle chart updates to 1 per second
const updateChart = throttle((data) => {
    chart.update('none');
}, 1000);
```

### 2. Data Point Limiting

```javascript
const MAX_DATA_POINTS = 100;

function addDataPoint(chart, value) {
    chart.data.labels.push(new Date().toLocaleTimeString());
    chart.data.datasets[0].data.push(value);
    
    // Remove old points
    if (chart.data.labels.length > MAX_DATA_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    chart.update('none');
}
```

### 3. Virtual Scrolling for Logs

```javascript
// Only render visible log entries
class VirtualLogViewer {
    constructor(container, itemHeight = 30) {
        this.container = container;
        this.itemHeight = itemHeight;
        this.entries = [];
        this.visibleStart = 0;
        this.visibleEnd = 0;
    }
    
    addEntry(entry) {
        this.entries.push(entry);
        this.render();
    }
    
    render() {
        const containerHeight = this.container.clientHeight;
        const visibleCount = Math.ceil(containerHeight / this.itemHeight);
        
        this.visibleStart = Math.max(0, this.entries.length - visibleCount);
        this.visibleEnd = this.entries.length;
        
        const visibleEntries = this.entries.slice(this.visibleStart, this.visibleEnd);
        
        this.container.innerHTML = visibleEntries.map(entry => 
            `<div class="log-entry">${entry}</div>`
        ).join('');
    }
}
```

---

## MQTT WebSocket Client

### Direct MQTT Connection

```javascript
// Using MQTT.js
const mqtt = require('mqtt');

const client = mqtt.connect('ws://mqtt.example.com:9001', {
    username: 'grokmon',
    password: 'your-password',
    clientId: 'dashboard-' + Math.random().toString(16).substr(2, 8)
});

client.on('connect', () => {
    console.log('MQTT connected');
    
    // Subscribe to sensor topics
    client.subscribe('sensors/temperature');
    client.subscribe('sensors/humidity');
    client.subscribe('sensors/vpd');
    client.subscribe('sensors/soil_moisture');
    client.subscribe('ai/decisions');
});

client.on('message', (topic, message) => {
    const data = JSON.parse(message.toString());
    
    switch (topic) {
        case 'sensors/temperature':
            updateTemperature(data.value);
            break;
        case 'sensors/humidity':
            updateHumidity(data.value);
            break;
        case 'ai/decisions':
            updateAIDecision(data);
            break;
    }
});
```

---

## Complete Dashboard Example

### HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>Grok & Mon Dashboard</title>
    <link rel="stylesheet" href="dashboard.css">
</head>
<body>
    <div class="dashboard-header">
        <h1>🌿 Grok & Mon</h1>
        <div id="connection-status" class="status-indicator">🟢 Connected</div>
    </div>
    
    <div class="dashboard-container">
        <!-- Sensor Cards -->
        <div class="sensor-card">
            <h3>Temperature</h3>
            <div class="sensor-value" id="temperature">--°F</div>
            <canvas id="temp-gauge"></canvas>
        </div>
        
        <div class="sensor-card">
            <h3>Humidity</h3>
            <div class="sensor-value" id="humidity">--%</div>
            <div class="gauge-bar">
                <div class="gauge-fill" id="humidity-fill"></div>
            </div>
        </div>
        
        <div class="sensor-card">
            <h3>VPD</h3>
            <div class="sensor-value" id="vpd">-- kPa</div>
        </div>
        
        <div class="sensor-card">
            <h3>Soil Moisture</h3>
            <div class="sensor-value" id="soil-moisture">--%</div>
            <div class="gauge-bar">
                <div class="gauge-fill" id="soil-fill"></div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="chart-container">
            <h3>Temperature History</h3>
            <canvas id="temp-chart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Humidity History</h3>
            <canvas id="humidity-chart"></canvas>
        </div>
        
        <!-- AI Decision Log -->
        <div class="console-container">
            <h3>Grok's Latest Decision</h3>
            <div class="console-output" id="ai-decision">
                Waiting for Grok...
            </div>
        </div>
        
        <!-- Webcam Feed -->
        <div class="webcam-container">
            <h3>Live Feed</h3>
            <img id="webcam" src="/api/webcam/latest" alt="Plant webcam">
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="dashboard.js"></script>
</body>
</html>
```

---

## Sources & References

1. **Chart.js** - https://www.chartjs.org/
2. **ApexCharts** - https://apexcharts.com/
3. **Recharts** - https://recharts.org/
4. **WebSocket API** - https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
5. **Server-Sent Events** - https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
6. **MQTT.js** - https://github.com/mqttjs/MQTT.js

---

*Last Updated: 2025-01-12*
*For use with Grok & Mon AI-autonomous cannabis cultivation system*
