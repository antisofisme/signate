/**
 * Authentication Middleware for MANTRA MCP Server
 *
 * Validates API keys via MANTRA backend with caching.
 * API keys are managed through the backend /api/v1/api-keys endpoints.
 */

import { Request, Response, NextFunction } from 'express'

export interface AuthenticatedRequest extends Request {
  apiKey?: string
  apiKeyInfo?: {
    id: string
    name: string
    permissions: string[]
  }
}

// =============================================================================
// Configuration
// =============================================================================

const BACKEND_URL = process.env.MANTRA_BACKEND_URL || 'http://localhost:8002'
const CACHE_TTL_MS = 60 * 1000 // 60 seconds cache
const DEV_MODE = process.env.NODE_ENV !== 'production'

// Master key from environment (for emergency access)
const MASTER_API_KEY = process.env.MANTRA_MCP_MASTER_KEY

// =============================================================================
// Cache for validated keys
// =============================================================================

interface CachedKey {
  id: string
  name: string
  permissions: string[]
  cachedAt: number
}

const keyCache = new Map<string, CachedKey>()

function getCachedKey(apiKey: string): CachedKey | null {
  const cached = keyCache.get(apiKey)
  if (!cached) return null

  // Check if cache is still valid
  if (Date.now() - cached.cachedAt > CACHE_TTL_MS) {
    keyCache.delete(apiKey)
    return null
  }

  return cached
}

function cacheKey(apiKey: string, info: CachedKey): void {
  // Limit cache size
  if (keyCache.size > 1000) {
    // Remove oldest entries
    const entries = Array.from(keyCache.entries())
    entries.sort((a, b) => a[1].cachedAt - b[1].cachedAt)
    for (let i = 0; i < 100; i++) {
      keyCache.delete(entries[i][0])
    }
  }

  keyCache.set(apiKey, info)
}

// =============================================================================
// Backend validation
// =============================================================================

interface ValidateResponse {
  valid: boolean
  key_id?: string
  key_name?: string
  permissions?: string[]
  error?: string
}

async function validateKeyWithBackend(apiKey: string): Promise<ValidateResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/api-keys/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ key: apiKey }),
    })

    if (!response.ok) {
      console.error(`Backend validation failed: ${response.status}`)
      return { valid: false, error: `Backend error: ${response.status}` }
    }

    return await response.json() as ValidateResponse
  } catch (error) {
    console.error('Failed to validate key with backend:', error)
    return { valid: false, error: 'Backend unavailable' }
  }
}

// =============================================================================
// Auth Middleware
// =============================================================================

export async function authMiddleware(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> {
  const authHeader = req.headers.authorization

  if (!authHeader) {
    res.status(401).json({
      error: 'Unauthorized',
      message: 'Missing Authorization header. Use: Bearer <api_key>'
    })
    return
  }

  const [scheme, token] = authHeader.split(' ')

  if (scheme.toLowerCase() !== 'bearer' || !token) {
    res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid Authorization format. Use: Bearer <api_key>'
    })
    return
  }

  // Check master key first (environment-based)
  if (MASTER_API_KEY && token === MASTER_API_KEY) {
    req.apiKey = token
    req.apiKeyInfo = {
      id: 'master-key',
      name: 'Master Key',
      permissions: ['read', 'write', 'propose', 'admin']
    }
    next()
    return
  }

  // Check cache first
  const cached = getCachedKey(token)
  if (cached) {
    req.apiKey = token
    req.apiKeyInfo = {
      id: cached.id,
      name: cached.name,
      permissions: cached.permissions
    }
    next()
    return
  }

  // Dev mode fallback: accept any mk_ key without backend validation
  // This allows development when backend is not running
  if (DEV_MODE && token.startsWith('mk_')) {
    // Try backend first, fall back to dev mode if unavailable
    const result = await validateKeyWithBackend(token)

    if (result.valid) {
      // Cache the valid key
      cacheKey(token, {
        id: result.key_id!,
        name: result.key_name!,
        permissions: result.permissions!,
        cachedAt: Date.now()
      })

      req.apiKey = token
      req.apiKeyInfo = {
        id: result.key_id!,
        name: result.key_name!,
        permissions: result.permissions!
      }
      next()
      return
    }

    // If backend says invalid (not unavailable), reject
    if (result.error && !result.error.includes('unavailable')) {
      res.status(401).json({
        error: 'Unauthorized',
        message: result.error || 'Invalid API key'
      })
      return
    }

    // Dev fallback: accept key if backend is unavailable
    console.warn('DEV MODE: Backend unavailable, accepting mk_ key without validation')
    req.apiKey = token
    req.apiKeyInfo = {
      id: 'dev-fallback',
      name: 'Development Fallback',
      permissions: ['read', 'write', 'propose']
    }
    next()
    return
  }

  // Production: must validate with backend
  const result = await validateKeyWithBackend(token)

  if (!result.valid) {
    res.status(401).json({
      error: 'Unauthorized',
      message: result.error || 'Invalid API key'
    })
    return
  }

  // Cache the valid key
  cacheKey(token, {
    id: result.key_id!,
    name: result.key_name!,
    permissions: result.permissions!,
    cachedAt: Date.now()
  })

  req.apiKey = token
  req.apiKeyInfo = {
    id: result.key_id!,
    name: result.key_name!,
    permissions: result.permissions!
  }
  next()
}

// =============================================================================
// Permission checking utility
// =============================================================================

export function requirePermission(permission: string) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    if (!req.apiKeyInfo) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'Authentication required'
      })
      return
    }

    if (!req.apiKeyInfo.permissions.includes(permission) &&
        !req.apiKeyInfo.permissions.includes('admin')) {
      res.status(403).json({
        error: 'Forbidden',
        message: `Missing required permission: ${permission}`
      })
      return
    }

    next()
  }
}

// =============================================================================
// Cache management (for testing)
// =============================================================================

export function clearKeyCache(): void {
  keyCache.clear()
}

export function getCacheSize(): number {
  return keyCache.size
}
