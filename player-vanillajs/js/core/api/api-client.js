/**
 * API Client Wrapper for Viewer
 *
 * @namespace SharedAPIClient
 * @global
 * @description
 * Lightweight wrapper for standardized backend API responses with automatic response unwrapping.
 * Handles both new standardized format and legacy direct-response format.
 *
 * @features
 * - **Auto-unwrapping**: Detects `{success, data, meta}` format and returns just `data`
 * - **Backward compatible**: Works with old direct-response format
 * - **Zero dependencies**: Pure vanilla JavaScript
 * - **WebOS TV compatible**: ES6+ with fallbacks for older browsers
 * - **Error handling**: Enhanced errors with request context and timing
 * - **Debug mode**: Optional verbose logging via localStorage or URL parameter
 * - **Request tracing**: Unique request IDs for debugging
 *
 * @response_formats
 * **New Standardized Format (auto-unwrapped):**
 * ```json
 * {
 *   "success": true,
 *   "data": { ... },  // <- This is what you get
 *   "meta": { "timestamp": "...", "version": "1.0" }
 * }
 * ```
 *
 * **Legacy Format (passed through):**
 * ```json
 * { "id": 1, "name": "..." }  // <- This is what you get
 * ```
 *
 * @usage
 * ```javascript
 * // GET request
 * const device = await SharedAPIClient.get('/api/devices/123');
 * SharedLogger.log(device.name); // Direct access to data
 *
 * // POST request
 * const result = await SharedAPIClient.post('/api/devices', {
 *   code: '123456',
 *   name: 'Lobby Display'
 * });
 *
 * // PUT request
 * await SharedAPIClient.put('/api/devices/123', {
 *   name: 'Updated Name'
 * });
 *
 * // DELETE request
 * await SharedAPIClient.delete('/api/devices/123');
 *
 * // Error handling
 * try {
 *   const data = await SharedAPIClient.get('/api/playlist');
 * } catch (error) {
 *   if (error.status === 404) {
 *     SharedLogger.log('Playlist not found');
 *   } else if (error.isNetworkError) {
 *     SharedLogger.log('Network error:', error.message);
 *   }
 * }
 * ```
 *
 * @error_handling
 * All errors are enhanced with additional context:
 * - **status**: HTTP status code (404, 500, etc.)
 * - **statusText**: HTTP status text ("Not Found", etc.)
 * - **requestId**: Unique request identifier for tracing
 * - **duration**: Request duration in milliseconds
 * - **isNetworkError**: true for network/fetch failures, false for HTTP errors
 * - **errorData**: Parsed error response body (if available)
 *
 * @debug_mode
 * Enable verbose logging for all API requests:
 * ```javascript
 * // Enable via console
 * enableAPIDebug();
 *
 * // Enable via localStorage
 * localStorage.setItem('API_DEBUG', 'true');
 *
 * // Enable via URL parameter
 * http://localhost:8080/?api_debug=true
 *
 * // Disable
 * disableAPIDebug();
 * ```
 *
 * @browser_compatibility
 * - Modern browsers (Chrome 60+, Firefox 55+, Safari 12+)
 * - WebOS TV 3.0+ (2017 models and newer)
 * - Tizen TV 3.0+ (2017 models and newer)
 * - Internet Explorer NOT supported (requires Fetch API)
 *
 * @author Generated for Smart TV Digital Signage System
 * @version 2.0.0
 */
window.SharedAPIClient = {
    /**
     * Execute fetch request with automatic response unwrapping
     *
     * @param {string} url - Full URL or relative path to API endpoint
     * @param {Object} options - Fetch options (method, headers, body, etc.)
     * @returns {Promise<any>} - Unwrapped response data
     * @throws {APIClientError} - Enhanced error with request context
     */
    request: async function(url, options = {}) {
        const startTime = performance.now();
        const requestId = this._generateRequestId();

        // Default headers
        const defaultHeaders = {
            'Content-Type': 'application/json'
        };

        // 🔑 Add Authorization header if device token exists
        const deviceToken = localStorage.getItem('device_token');
        if (deviceToken) {
            defaultHeaders['Authorization'] = `Bearer ${deviceToken}`;
        }

        // Merge options with defaults
        const requestOptions = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...(options.headers || {})
            }
        };

        // Log outgoing request (debug mode)
        this._logRequest(requestId, url, requestOptions);

        try {
            const response = await fetch(url, requestOptions);
            const duration = Math.round(performance.now() - startTime);

            // Handle non-OK responses (4xx, 5xx)
            if (!response.ok) {
                await this._handleErrorResponse(response, requestId, duration);
            }

            // Parse JSON response
            const jsonData = await response.json();

            // Log successful response (debug mode)
            this._logResponse(requestId, response.status, duration, jsonData);

            // Auto-unwrap standardized API format
            const unwrappedData = this._unwrapResponse(jsonData);

            return unwrappedData;

        } catch (error) {
            const duration = Math.round(performance.now() - startTime);

            // Enhance error with context
            const apiError = this._createAPIError(error, requestId, url, duration);

            // Log error
            this._logError(requestId, apiError);

            throw apiError;
        }
    },

    /**
     * Convenience method for GET requests
     *
     * @param {string} url - API endpoint URL
     * @param {Object} options - Additional fetch options
     * @returns {Promise<any>} - Unwrapped response data
     */
    get: async function(url, options = {}) {
        return this.request(url, {
            ...options,
            method: 'GET'
        });
    },

    /**
     * Convenience method for POST requests
     *
     * @param {string} url - API endpoint URL
     * @param {Object} body - Request body (will be JSON.stringify'd)
     * @param {Object} options - Additional fetch options
     * @returns {Promise<any>} - Unwrapped response data
     */
    post: async function(url, body = {}, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    /**
     * Convenience method for PUT requests
     *
     * @param {string} url - API endpoint URL
     * @param {Object} body - Request body (will be JSON.stringify'd)
     * @param {Object} options - Additional fetch options
     * @returns {Promise<any>} - Unwrapped response data
     */
    put: async function(url, body = {}, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(body)
        });
    },

    /**
     * Convenience method for DELETE requests
     *
     * @param {string} url - API endpoint URL
     * @param {Object} options - Additional fetch options
     * @returns {Promise<any>} - Unwrapped response data
     */
    delete: async function(url, options = {}) {
        return this.request(url, {
            ...options,
            method: 'DELETE'
        });
    },

    /**
     * Unwrap standardized API response format
     *
     * Detects new format: {success: true, data: {...}, meta: {...}}
     * If detected, returns just the data field
     * Otherwise, returns response as-is (backward compatibility)
     *
     * @param {Object} response - Raw JSON response from API
     * @returns {any} - Unwrapped data or original response
     * @private
     */
    _unwrapResponse: function(response) {
        // Check if response matches new standardized format
        if (
            response &&
            typeof response === 'object' &&
            'success' in response &&
            'data' in response
        ) {
            // New format detected - return just the data field
            return response.data;
        }

        // Old format or unknown structure - return as-is
        return response;
    },

    /**
     * Handle HTTP error responses (4xx, 5xx)
     *
     * @param {Response} response - Fetch Response object
     * @param {string} requestId - Unique request identifier
     * @param {number} duration - Request duration in ms
     * @throws {APIClientError} - Enhanced error with response details
     * @private
     */
    _handleErrorResponse: async function(response, requestId, duration) {
        let errorData = null;
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

        // Try to parse error response body
        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                errorData = await response.json();

                // Extract error message from standardized error format
                if (errorData && errorData.error && errorData.error.message) {
                    errorMessage = errorData.error.message;
                } else if (errorData && errorData.detail) {
                    // FastAPI validation error format
                    errorMessage = errorData.detail;
                }
            }
        } catch (parseError) {
            // Unable to parse error body - use status text
            SharedLogger.warn('[SharedAPIClient] Failed to parse error response:', parseError);
        }

        // Create enhanced error
        const error = new Error(errorMessage);
        error.name = 'APIClientError';
        error.status = response.status;
        error.statusText = response.statusText;
        error.requestId = requestId;
        error.duration = duration;
        error.errorData = errorData;
        error.isNetworkError = false;

        throw error;
    },

    /**
     * Create enhanced API error from caught exception
     *
     * @param {Error} error - Original error
     * @param {string} requestId - Unique request identifier
     * @param {string} url - Request URL
     * @param {number} duration - Request duration in ms
     * @returns {Error} - Enhanced error object
     * @private
     */
    _createAPIError: function(error, requestId, url, duration) {
        // If already an APIClientError, return as-is
        if (error.name === 'APIClientError') {
            return error;
        }

        // Create new enhanced error for network/parsing errors
        const apiError = new Error(error.message || 'Network request failed');
        apiError.name = 'APIClientError';
        apiError.requestId = requestId;
        apiError.duration = duration;
        apiError.url = url;
        apiError.isNetworkError = true;
        apiError.originalError = error;

        // Detect common error types
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            apiError.message = 'Network error: Unable to connect to server';
        } else if (error.name === 'SyntaxError') {
            apiError.message = 'Invalid JSON response from server';
        }

        return apiError;
    },

    /**
     * Generate unique request ID for tracing
     *
     * @returns {string} - Unique request ID (timestamp + random)
     * @private
     */
    _generateRequestId: function() {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2, 9);
        return `${timestamp}-${random}`;
    },

    /**
     * Log outgoing request (debug mode only)
     *
     * @param {string} requestId - Request identifier
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @private
     */
    _logRequest: function(requestId, url, options) {
        if (!this._isDebugMode()) return;

        console.log(`[SharedAPIClient] → ${options.method || 'GET'} ${url}`, {
            requestId,
            headers: options.headers,
            bodyLength: options.body ? options.body.length : 0
        });
    },

    /**
     * Log successful response (debug mode only)
     *
     * @param {string} requestId - Request identifier
     * @param {number} status - HTTP status code
     * @param {number} duration - Request duration in ms
     * @param {any} data - Response data
     * @private
     */
    _logResponse: function(requestId, status, duration, data) {
        if (!this._isDebugMode()) return;

        // Check if response was unwrapped
        const wasUnwrapped = data && typeof data === 'object' && 'success' in data && 'data' in data;

        SharedLogger.log(`[SharedAPIClient] ← ${status} (${duration}ms)`, {
            requestId,
            unwrapped: wasUnwrapped,
            dataType: Array.isArray(data) ? 'array' : typeof data
        });
    },

    /**
     * Log error (always logged, regardless of debug mode)
     *
     * @param {string} requestId - Request identifier
     * @param {Error} error - API error
     * @private
     */
    _logError: function(requestId, error) {
        SharedLogger.error(`[SharedAPIClient] ✗ Error (${error.duration || 0}ms)`, {
            requestId,
            message: error.message,
            status: error.status,
            isNetwork: error.isNetworkError,
            url: error.url
        });
    },

    /**
     * Check if debug mode is enabled
     *
     * Debug mode can be enabled by:
     * 1. localStorage.setItem('API_DEBUG', 'true')
     * 2. URL parameter: ?api_debug=true
     *
     * @returns {boolean} - True if debug mode enabled
     * @private
     */
    _isDebugMode: function() {
        try {
            // Check localStorage
            if (localStorage.getItem('API_DEBUG') === 'true') {
                return true;
            }

            // Check URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('api_debug') === 'true') {
                return true;
            }
        } catch (e) {
            // localStorage might be disabled
        }

        return false;
    }
};

// Enable debug logging via console command
// Usage: enableAPIDebug() / disableAPIDebug()
window.enableAPIDebug = function() {
    localStorage.setItem('API_DEBUG', 'true');
    SharedLogger.log('[SharedAPIClient] Debug mode enabled');
};

window.disableAPIDebug = function() {
    localStorage.removeItem('API_DEBUG');
    SharedLogger.log('[SharedAPIClient] Debug mode disabled');
};

SharedLogger.log('[SharedAPIClient] Loaded (v2.0.0) - Standardized response format support enabled');
