/**
 * Main API Exports
 * Re-exports all API modules for backward compatibility
 *
 * Usage:
 * - New modular approach: import authAPI from './api/auth.js'
 * - Backward compatible: import { authAPI } from './api/main.js'
 */

export { default as api } from './index'
export { default as authAPI } from './auth'
export { default as devicesAPI } from './devices'
export { default as contentAPI } from './content'
export { default as tagsAPI } from './tags'
export { default as playlistsAPI } from './playlists'
export { default as widgetsAPI } from './widgets'
export { default as usersAPI } from './users'
export { default as settingsAPI } from './settings'
export { default as clientAPI } from './client'
export { default as activitiesAPI } from './activities'
export { default as firebirdAPI } from './firebird'
