/**
 * API Module Entry Point
 * Exports SharedAPIClient singleton, helper functions, and types
 */

export { SharedAPIClient, enableAPIDebug, disableAPIDebug } from './shared-api-client';
export type { APIResponse, APIError, RequestOptions, APIClient } from './api-client.types';
