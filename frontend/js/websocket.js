/**
 * WebSocket Client for Real-time Dashboard Updates
 */

class DashboardWebSocket {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = 3000;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.isConnecting = false;
        this.connect();
    }

    connect() {
        if (this.isConnecting) {
            console.log('Already connecting, skipping...');
            return;
        }

        this.isConnecting = true;
        console.log('Connecting to WebSocket:', this.url);
        showConnectionToast('正在连接WebSocket...', false);

        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('WebSocket connected successfully');
                this.reconnectAttempts = 0;
                this.isConnecting = false;
                updateStatusIndicator('running');
                showConnectionToast('已连接到服务器', true);
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnecting = false;
                updateStatusIndicator('error');
                showConnectionToast('连接错误', false);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnecting = false;
                updateStatusIndicator('disconnected');

                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                    showConnectionToast(`正在重连... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, false);

                    setTimeout(() => this.connect(), this.reconnectInterval);
                } else {
                    console.error('Max reconnection attempts reached');
                    showConnectionToast('无法连接到服务器', false);
                }
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.isConnecting = false;
            updateStatusIndicator('error');
        }
    }

    handleMessage(data) {
        console.log('WebSocket message received:', data.type);

        switch (data.type) {
            case 'connected':
                console.log('Connection acknowledged:', data.message);
                break;

            case 'update':
                // Update dashboard with latest status and metrics
                if (data.status && data.metrics) {
                    updateDashboard(data.status, data.metrics);
                }
                break;

            case 'new_trade':
                // Add new trade to the list
                if (data.trade) {
                    addTradeToList(data.trade);
                }
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Show connection status toast
function showConnectionToast(message, autoHide = true) {
    const toast = document.getElementById('connection-toast');
    const messageElement = document.getElementById('connection-message');

    if (toast && messageElement) {
        messageElement.textContent = message;
        toast.classList.remove('hidden');

        if (autoHide) {
            setTimeout(() => {
                toast.classList.add('hidden');
            }, 3000);
        }
    }
}

// Initialize WebSocket connection
let dashboardWS = null;

function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    dashboardWS = new DashboardWebSocket(wsUrl);
}

// Auto-connect on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWebSocket);
} else {
    initWebSocket();
}
