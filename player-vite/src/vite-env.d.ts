/// <reference types="vite/client" />

/**
 * Vite Environment Variables
 */
interface ImportMetaEnv {
  // API Configuration
  readonly VITE_API_BASE_URL: string;
  readonly VITE_WS_BASE_URL: string;
  readonly VITE_API_TIMEOUT: string;

  // Device Configuration
  readonly VITE_HEARTBEAT_INTERVAL: string;
  readonly VITE_LOG_SEND_INTERVAL: string;
  readonly VITE_LOG_BUFFER_SIZE: string;

  // Retry Configuration
  readonly VITE_MAX_RETRY_COUNT: string;
  readonly VITE_INITIAL_RETRY_DELAY: string;
  readonly VITE_MAX_RETRY_DELAY: string;

  // Logging Configuration
  readonly VITE_LOG_LEVEL: string;
  readonly VITE_ENABLE_CONSOLE: string;

  // Debug Configuration
  readonly VITE_DEBUG_MODE: string;
  readonly VITE_API_DEBUG: string;
  readonly VITE_WS_DEBUG: string;

  // Vite built-in
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
