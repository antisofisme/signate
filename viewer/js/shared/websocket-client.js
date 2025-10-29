/**
 * WebSocket Client for Real-Time Updates
 * Handles connection, reconnection, and message handling for digital signage devices
 */

class WebSocketClient {
    constructor(config = {}) {
        this.config = {
            deviceId: config.deviceId || null,
            token: config.token || null,
            serverUrl: config.serverUrl || window.ENV?.WEBSOCKET_URL || 'ws://localhost:8001',
            reconnectInterval: config.reconnectInterval || 5000, // 5 seconds
            maxReconnectAttempts: config.maxReconnectAttempts || null, // null = infinite
            heartbeatInterval: config.heartbeatInterval || 30000, // 30 seconds
            debug: config.debug || false
        };

        this.ws = null;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.heartbeatTimer = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.messageHandlers = new Map();
        this.connectionListeners = [];

        // Bind methods
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.send = this.send.bind(this);
        this._handleMessage = this._handleMessage.bind(this);
        this._handleError = this._handleError.bind(this);
        this._handleClose = this._handleClose.bind(this);
        this._reconnect = this._reconnect.bind(this);
        this._sendHeartbeat = this._sendHeartbeat.bind(this);
    }

    /**
     * Connect to WebSocket server
     */
    async connect() {
        if (this.isConnected || this.isConnecting) {
            this._log('Already connected or connecting');
            return;
        }

        this.isConnecting = true;
        this._clearReconnectTimer();

        try {
            const url = `${this.config.serverUrl}/ws/device/${this.config.deviceId}` +
                (this.config.token ? `?token=${this.config.token}` : '');

            this._log(`Connecting to ${url}`);

            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                this._log('WebSocket connected');
                this.isConnected = true;
                this.isConnecting = false;
                this.reconnectAttempts = 0;

                // Start heartbeat
                this._startHeartbeat();

                // Notify listeners
                this._notifyConnectionChange(true);
            };

            this.ws.onmessage = this._handleMessage;
            this.ws.onerror = this._handleError;
            this.ws.onclose = this._handleClose;

        } catch (error) {
            this._log('Connection error:', error);
            this.isConnecting = false;
            this._scheduleReconnect();
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        this._log('Disconnecting');

        this._clearReconnectTimer();
        this._stopHeartbeat();

        if (this.ws) {
            this.ws.onclose = null; // Prevent reconnection
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
        this.isConnecting = false;

        // Notify listeners
        this._notifyConnectionChange(false);
    }

    /**
     * Send message to server
     */
    send(type, data = {}) {
        if (!this.isConnected) {
            this._log('Cannot send - not connected');
            return false;
        }

        try {
            const message = {
                type,
                ...data,
                timestamp: new Date().toISOString()
            };

            this.ws.send(JSON.stringify(message));
            this._log('Sent:', message);
            return true;

        } catch (error) {
            this._log('Send error:', error);
            return false;
        }
    }

    /**
     * Register message handler
     */
    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }

    /**
     * Unregister message handler
     */
    off(messageType, handler) {
        const handlers = this.messageHandlers.get(messageType);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Register connection state listener
     */
    onConnectionChange(listener) {
        this.connectionListeners.push(listener);
    }

    /**
     * Handle incoming message
     */
    _handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this._log('Received:', message);

            // Handle system messages
            switch (message.type) {
                case 'connected':
                    this._log('Connection confirmed by server');
                    break;

                case 'heartbeat':
                    // Server heartbeat - respond with heartbeat
                    this.send('heartbeat');
                    break;

                case 'pong':
                    // Response to our heartbeat
                    this._log('Heartbeat acknowledged');
                    break;

                case 'error':
                    this._log('Server error:', message.error);
                    break;

                default:
                    // Handle custom messages
                    const handlers = this.messageHandlers.get(message.type);
                    if (handlers) {
                        handlers.forEach(handler => {
                            try {
                                handler(message);
                            } catch (error) {
                                this._log(`Handler error for ${message.type}:`, error);
                            }
                        });
                    }
            }

            // Also call generic handlers
            const allHandlers = this.messageHandlers.get('*');
            if (allHandlers) {
                allHandlers.forEach(handler => handler(message));
            }

        } catch (error) {
            this._log('Message parsing error:', error);
        }
    }

    /**
     * Handle WebSocket error
     */
    _handleError(event) {
        this._log('WebSocket error:', event);
    }

    /**
     * Handle WebSocket close
     */
    _handleClose(event) {
        this._log('WebSocket closed:', event.code, event.reason);

        this.isConnected = false;
        this.isConnecting = false;
        this.ws = null;

        this._stopHeartbeat();
        this._notifyConnectionChange(false);

        // Schedule reconnection if not manually closed
        if (event.code !== 1000) {
            this._scheduleReconnect();
        }
    }

    /**
     * Schedule reconnection attempt
     */
    _scheduleReconnect() {
        // Check max attempts
        if (this.config.maxReconnectAttempts !== null &&
            this.reconnectAttempts >= this.config.maxReconnectAttempts) {
            this._log('Max reconnection attempts reached');
            return;
        }

        this._clearReconnectTimer();

        const delay = Math.min(
            this.config.reconnectInterval * Math.pow(1.5, this.reconnectAttempts),
            60000 // Max 60 seconds
        );

        this._log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

        this.reconnectTimer = setTimeout(this._reconnect, delay);
    }

    /**
     * Perform reconnection
     */
    _reconnect() {
        this.reconnectAttempts++;
        this.connect();
    }

    /**
     * Clear reconnection timer
     */
    _clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    /**
     * Start heartbeat timer
     */
    _startHeartbeat() {
        this._stopHeartbeat();

        this.heartbeatTimer = setInterval(this._sendHeartbeat, this.config.heartbeatInterval);

        // Send initial heartbeat
        this._sendHeartbeat();
    }

    /**
     * Stop heartbeat timer
     */
    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Send heartbeat message
     */
    _sendHeartbeat() {
        this.send('heartbeat');
    }

    /**
     * Notify connection state listeners
     */
    _notifyConnectionChange(connected) {
        this.connectionListeners.forEach(listener => {
            try {
                listener(connected);
            } catch (error) {
                this._log('Connection listener error:', error);
            }
        });
    }

    /**
     * Debug logging
     */
    _log(...args) {
        if (this.config.debug) {
            console.log('[WebSocket]', ...args);
        }
    }

    /**
     * Get connection status
     */
    get connected() {
        return this.isConnected;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}

// Example usage:
/*
const wsClient = new WebSocketClient({
    deviceId: 123,
    token: 'activation_code_here',
    serverUrl: window.ENV?.WEBSOCKET_URL,  // Uses ENV config (recommended)
    debug: true
});

// Register message handlers
wsClient.on('playlist_update', (message) => {
    console.log('Playlist updated:', message);
    // Reload playlist
});

wsClient.on('content_ready', (message) => {
    console.log('Content ready:', message);
    // Preload content
});

wsClient.on('command', (message) => {
    console.log('Command received:', message);

    switch (message.command) {
        case 'reload':
            location.reload();
            break;
        case 'screenshot':
            // Take screenshot
            break;
        case 'restart':
            // Restart application
            break;
    }

    // Send response
    wsClient.send('command_response', {
        command: message.command,
        success: true,
        result: 'Command executed'
    });
});

// Connection state listener
wsClient.onConnectionChange((connected) => {
    console.log('Connection state:', connected ? 'Connected' : 'Disconnected');
    // Update UI connection indicator
});

// Connect
wsClient.connect();
*/