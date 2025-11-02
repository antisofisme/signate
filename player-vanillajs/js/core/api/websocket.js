/**
 * SignageWebSocket - Production-ready WebSocket client for Smart TV Digital Signage
 *
 * Features:
 * - Auto-reconnect with exponential backoff (1s → 30s)
 * - Heartbeat/ping mechanism (30s interval)
 * - Message type handlers (playlist_update, content_ready, command)
 * - Graceful degradation to HTTP polling on max retries
 * - Event-driven architecture
 * - Connection state management
 * - Robust error handling
 *
 * Usage:
 *   const ws = new SignageWebSocket(deviceId, baseUrl);
 *   ws.on('playlist_update', (data) => { ... });
 *   ws.on('content_ready', (data) => { ... });
 *   ws.on('command', (data) => { ... });
 *   ws.connect();
 *
 * @author Smart TV Digital Signage System
 * @version 1.0.0
 */

class SignageWebSocket {
    constructor(deviceId, baseUrl = window.ENV?.API_BASE_URL || 'http://localhost:8001') {
        this.deviceId = deviceId;
        this.baseUrl = baseUrl;
        this.wsUrl = this._buildWebSocketUrl(baseUrl);

        // WebSocket instance
        this.ws = null;

        // Connection state
        this.state = 'disconnected'; // 'disconnected', 'connecting', 'connected', 'reconnecting', 'failed'
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start at 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds

        // Heartbeat
        this.heartbeatInterval = 30000; // 30 seconds
        this.heartbeatTimer = null;
        this.lastPongTime = null;
        this.missedPongs = 0;
        this.maxMissedPongs = 3;

        // Message handlers
        this.eventHandlers = {};

        // Reconnect timer
        this.reconnectTimer = null;

        // Stats for debugging
        this.stats = {
            connectionAttempts: 0,
            messagesReceived: 0,
            messagesSent: 0,
            reconnects: 0,
            errors: 0
        };

        // Bind methods to maintain context
        this._onOpen = this._onOpen.bind(this);
        this._onMessage = this._onMessage.bind(this);
        this._onError = this._onError.bind(this);
        this._onClose = this._onClose.bind(this);
    }

    /**
     * Build WebSocket URL from HTTP base URL
     * Handles both ws:// and wss:// protocols
     */
    _buildWebSocketUrl(baseUrl) {
        // Parse base URL
        const url = new URL(baseUrl);

        // Convert http/https to ws/wss
        const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';

        // Build WebSocket URL
        return `${protocol}//${url.host}/ws/device/${this.deviceId}`;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.state === 'connected' || this.state === 'connecting') {
            console.warn('[WebSocket] Already connected or connecting');
            return;
        }

        this.state = 'connecting';
        this.stats.connectionAttempts++;

        console.log(`[WebSocket] Connecting to ${this.wsUrl}...`);

        try {
            this.ws = new WebSocket(this.wsUrl);

            // Attach event handlers
            this.ws.addEventListener('open', this._onOpen);
            this.ws.addEventListener('message', this._onMessage);
            this.ws.addEventListener('error', this._onError);
            this.ws.addEventListener('close', this._onClose);

        } catch (error) {
            console.error('[WebSocket] Failed to create WebSocket:', error);
            this.stats.errors++;
            this._scheduleReconnect();
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        console.log('[WebSocket] Disconnecting...');

        // Stop heartbeat
        this._stopHeartbeat();

        // Cancel reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // Close WebSocket
        if (this.ws) {
            // Remove event listeners to prevent reconnect
            this.ws.removeEventListener('open', this._onOpen);
            this.ws.removeEventListener('message', this._onMessage);
            this.ws.removeEventListener('error', this._onError);
            this.ws.removeEventListener('close', this._onClose);

            if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
                this.ws.close(1000, 'Client disconnect');
            }

            this.ws = null;
        }

        this.state = 'disconnected';
        this._emit('disconnected');
    }

    /**
     * Send message to server
     */
    send(type, data = {}) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('[WebSocket] Cannot send message - not connected');
            return false;
        }

        try {
            const message = JSON.stringify({
                type,
                ...data
            });

            this.ws.send(message);
            this.stats.messagesSent++;

            return true;
        } catch (error) {
            console.error('[WebSocket] Failed to send message:', error);
            this.stats.errors++;
            return false;
        }
    }

    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    /**
     * Unregister event handler
     */
    off(event, handler) {
        if (!this.eventHandlers[event]) return;

        if (handler) {
            this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
        } else {
            delete this.eventHandlers[event];
        }
    }

    /**
     * Get connection state
     */
    getState() {
        return this.state;
    }

    /**
     * Get connection stats
     */
    getStats() {
        return {
            ...this.stats,
            state: this.state,
            reconnectAttempts: this.reconnectAttempts,
            lastPongTime: this.lastPongTime
        };
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.state === 'connected' && this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Handle WebSocket open event
     * @private
     */
    _onOpen() {
        console.log('[WebSocket] ✅ Connected');

        this.state = 'connected';
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.missedPongs = 0;

        // Start heartbeat
        this._startHeartbeat();

        // Emit connected event
        this._emit('connected');
    }

    /**
     * Handle WebSocket message event
     * @private
     */
    _onMessage(event) {
        this.stats.messagesReceived++;

        try {
            const message = JSON.parse(event.data);
            const { type, ...data } = message;

            // Handle pong response
            if (type === 'pong') {
                this.lastPongTime = Date.now();
                this.missedPongs = 0;
                return;
            }

            // Log message (debug mode)
            if (this._isDebugMode()) {
                console.log('[WebSocket] ← Message:', type, data);
            }

            // Emit type-specific event
            this._emit(type, data);

            // Emit generic message event
            this._emit('message', message);

        } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
            this.stats.errors++;
        }
    }

    /**
     * Handle WebSocket error event
     * @private
     */
    _onError(event) {
        console.error('[WebSocket] ❌ Error:', event);
        this.stats.errors++;

        // Emit error event
        this._emit('error', event);
    }

    /**
     * Handle WebSocket close event
     * @private
     */
    _onClose(event) {
        console.log(`[WebSocket] 🔌 Closed (code: ${event.code}, reason: ${event.reason || 'none'})`);

        // Stop heartbeat
        this._stopHeartbeat();

        // Clean up WebSocket instance
        if (this.ws) {
            this.ws.removeEventListener('open', this._onOpen);
            this.ws.removeEventListener('message', this._onMessage);
            this.ws.removeEventListener('error', this._onError);
            this.ws.removeEventListener('close', this._onClose);
            this.ws = null;
        }

        // Emit close event
        this._emit('close', { code: event.code, reason: event.reason });

        // Attempt reconnect (unless closed by client)
        if (event.code !== 1000) {
            this._scheduleReconnect();
        } else {
            this.state = 'disconnected';
            this._emit('disconnected');
        }
    }

    /**
     * Start heartbeat mechanism
     * @private
     */
    _startHeartbeat() {
        // Clear existing heartbeat
        this._stopHeartbeat();

        console.log(`[WebSocket] ❤️ Starting heartbeat (${this.heartbeatInterval}ms)`);

        this.heartbeatTimer = setInterval(() => {
            // Check if still connected
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this._stopHeartbeat();
                return;
            }

            // Check missed pongs
            if (this.lastPongTime && this.missedPongs >= this.maxMissedPongs) {
                console.warn(`[WebSocket] ⚠️ Missed ${this.missedPongs} pongs - connection may be dead`);
                this._stopHeartbeat();
                this.ws.close(1006, 'Heartbeat timeout');
                return;
            }

            // Send ping
            this.send('ping', { timestamp: Date.now() });
            this.missedPongs++;

        }, this.heartbeatInterval);
    }

    /**
     * Stop heartbeat mechanism
     * @private
     */
    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Schedule reconnect with exponential backoff
     * @private
     */
    _scheduleReconnect() {
        // Check if max retries reached
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error(`[WebSocket] ⛔ Max reconnect attempts (${this.maxReconnectAttempts}) reached`);
            this.state = 'failed';
            this._emit('failed');
            return;
        }

        this.state = 'reconnecting';
        this.reconnectAttempts++;
        this.stats.reconnects++;

        // Calculate exponential backoff delay
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );

        console.log(`[WebSocket] 🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        // Emit reconnecting event
        this._emit('reconnecting', {
            attempt: this.reconnectAttempts,
            maxAttempts: this.maxReconnectAttempts,
            delay
        });

        // Schedule reconnect
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, delay);
    }

    /**
     * Emit event to registered handlers
     * @private
     */
    _emit(event, data) {
        if (!this.eventHandlers[event]) return;

        this.eventHandlers[event].forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`[WebSocket] Error in ${event} handler:`, error);
            }
        });
    }

    /**
     * Check if debug mode is enabled
     * @private
     */
    _isDebugMode() {
        try {
            return localStorage.getItem('WS_DEBUG') === 'true' ||
                   localStorage.getItem('API_DEBUG') === 'true';
        } catch (e) {
            return false;
        }
    }
}

// Export to global scope (WebOS compatible)
window.SignageWebSocket = SignageWebSocket;

// Debug helpers
window.enableWSDebug = function() {
    localStorage.setItem('WS_DEBUG', 'true');
    console.log('[WebSocket] Debug mode enabled');
};

window.disableWSDebug = function() {
    localStorage.removeItem('WS_DEBUG');
    console.log('[WebSocket] Debug mode disabled');
};

console.log('[WebSocket] SignageWebSocket loaded (v1.0.0)');
