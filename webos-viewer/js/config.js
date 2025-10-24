/**
 * Configuration Module
 * Contains all application configuration constants and state variables
 */

// ========================================
// Configuration Constants
// ========================================

// API Configuration
export const API_BASE_URL = 'http://192.168.5.12:8001';
export const POLL_INTERVAL = 5000; // 5 seconds
export const PRELOAD_TIME = 3000; // 3 seconds
export const HEARTBEAT_INTERVAL = 30000; // 30 seconds
export const PLAYLIST_REFRESH_INTERVAL = 10000; // 10 seconds

// IndexedDB Configuration
export const DB_NAME = 'SignageMediaCache';
export const DB_VERSION = 2; // Incremented to force re-download with MIME type fix
export const STORE_NAME = 'mediaFiles';

// ========================================
// Application State
// ========================================

// Device State
export let deviceId = null;
export let deviceUUID = null;  // Permanent device identifier (webOS specific)
export let isActivated = false;

// Playlist State
export let playlist = [];
export let currentIndex = 0;

// Player State
export let currentContentElement = null;
export let nextContentElement = null;

// Timer References
export let contentTimer = null;
export let pollTimer = null;
export let playlistRefreshTimer = null;
export let heartbeatTimer = null;

// IndexedDB and Media State
export let db = null; // IndexedDB instance
export let currentBlobUrl = null; // Track current blob URL for cleanup

// Debug State
export let debugMode = false;

// ========================================
// State Setters (for updating state from other modules)
// ========================================

export function setDeviceId(value) {
    deviceId = value;
}

export function setDeviceUUID(value) {
    deviceUUID = value;
}

export function setIsActivated(value) {
    isActivated = value;
}

export function setPlaylist(value) {
    playlist = value;
}

export function setCurrentIndex(value) {
    currentIndex = value;
}

export function setCurrentContentElement(value) {
    currentContentElement = value;
}

export function setNextContentElement(value) {
    nextContentElement = value;
}

export function setContentTimer(value) {
    contentTimer = value;
}

export function setPollTimer(value) {
    pollTimer = value;
}

export function setPlaylistRefreshTimer(value) {
    playlistRefreshTimer = value;
}

export function setHeartbeatTimer(value) {
    heartbeatTimer = value;
}

export function setDb(value) {
    db = value;
}

export function setCurrentBlobUrl(value) {
    currentBlobUrl = value;
}

export function setDebugMode(value) {
    debugMode = value;
}
