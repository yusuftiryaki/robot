// 🤖 Hacı Abi'nin Robot Kontrol JS

class RobotController {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.setupWebSocket();
        this.setupEventListeners();
        this.startStatusUpdates();
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        try {
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('🔗 WebSocket bağlantısı kuruldu');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.websocket.onclose = () => {
                console.log('🔌 WebSocket bağlantısı kesildi');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                // 5 saniye sonra yeniden bağlan
                setTimeout(() => this.setupWebSocket(), 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket hatası:', error);
            };
        } catch (error) {
            console.error('❌ WebSocket kurulum hatası:', error);
        }
    }

    setupEventListeners() {
        // Buton event listeners
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-command]')) {
                const command = e.target.dataset.command;
                const params = JSON.parse(e.target.dataset.params || '{}');
                this.sendCommand(command, params);
            }
        });
    }

    async sendCommand(command, params = {}) {
        try {
            const response = await fetch('/api/robot/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    params: params
                })
            });

            const result = await response.json();

            if (result.success) {
                console.log(`✅ Komut başarılı: ${command}`, result);
                this.showNotification(`Komut başarılı: ${command}`, 'success');
            } else {
                console.error(`❌ Komut hatası: ${command}`, result.error);
                this.showNotification(`Komut hatası: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('❌ API hatası:', error);
            this.showNotification('API bağlantı hatası', 'error');
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/robot/status');
            const result = await response.json();

            if (result.success) {
                this.displayRobotStatus(result.data);
            }
        } catch (error) {
            console.error('❌ Status güncelleme hatası:', error);
        }
    }

    displayRobotStatus(data) {
        // Robot durumunu DOM'a yaz
        const elements = {
            'robot-state': data.robot_status?.state || 'Bilinmeyen',
            'battery-level': `${data.robot_status?.battery_level || 0}%`,
            'position-x': data.robot_status?.position?.x?.toFixed(2) || '0.00',
            'position-y': data.robot_status?.position?.y?.toFixed(2) || '0.00',
            'gps-lat': data.sensors?.gps?.latitude?.toFixed(6) || '0.000000',
            'gps-lng': data.sensors?.gps?.longitude?.toFixed(6) || '0.000000',
            'motor-left': data.motors?.left_speed?.toFixed(2) || '0.00',
            'motor-right': data.motors?.right_speed?.toFixed(2) || '0.00'
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        }

        // Timestamp güncelle
        const timestampElement = document.getElementById('last-update');
        if (timestampElement) {
            timestampElement.textContent = new Date().toLocaleTimeString();
        }
    }

    handleWebSocketMessage(data) {
        if (data.type === 'robot_status') {
            this.displayRobotStatus(data.data);
        } else if (data.type === 'notification') {
            this.showNotification(data.message, data.level || 'info');
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Bağlı' : 'Bağlantı Kesildi';
            statusElement.className = connected ? 'status-connected' : 'status-disconnected';
        }
    }

    showNotification(message, type = 'info') {
        // Basit notification sistemi
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    startStatusUpdates() {
        // Her 2 saniyede status güncelle
        setInterval(() => {
            this.updateStatus();
        }, 2000);

        // İlk güncelleme
        this.updateStatus();
    }
}

// Sayfa yüklendiğinde başlat
document.addEventListener('DOMContentLoaded', () => {
    window.robotController = new RobotController();
    console.log('🤖 Robot Controller başlatıldı!');
});
