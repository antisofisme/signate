/**
 * Shared Module Entry Point
 * Exports all shared services, utilities, and components
 *
 * @module Shared
 * @description
 * Shared context contains utilities and services used across all contexts.
 * This includes API client, config, logger, event bus, device state, etc.
 */

// API
export * from './api';

// Config
export * from './config';

// Device
export * from './device';

// Events
export { SharedEventBus, EventNames } from './events/shared-event-bus';
export type { EventName } from './events/shared-event-bus';

// Logger
export * from './logger';

// WebSocket
export { SharedWebSocket } from './websocket/shared-websocket';

// UI Components
export * from './ui';

// Utils
export { cn } from './utils/cn';

// Models
export * from './models';

// Storage
export * from './storage';

// State Management
export * from './state';
