/**
 * Logger Module Entry Point
 * Exports SharedLogger singleton, LogNamespace, and types
 */

export { SharedLogger, LogNamespace } from './shared-logger';
export { SharedLogger as logger } from './shared-logger';
export type { LogLevel, LogEntry, Logger, LoggerConfig } from './logger.types';
