/**
 * MANTRA MCP Server - Remote SSE Transport
 *
 * Constitutional Law Decision System accessible via MCP protocol.
 * Allows AI assistants to query, propose, and validate decisions.
 */

import express, { Request, Response, NextFunction } from 'express'
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js'
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'

import { authMiddleware, AuthenticatedRequest } from './auth/middleware.js'
import { toolHandlers, toolDefinitions } from './tools/index.js'
import { resourceHandlers, resourceDefinitions } from './resources/index.js'
import { promptHandlers, promptDefinitions } from './prompts/index.js'
import { MantraClient } from './client.js'

// Configuration
const PORT = parseInt(process.env.PORT || '8004')
const HOST = process.env.HOST || '0.0.0.0'
const MANTRA_API_URL = process.env.MANTRA_API_URL || 'http://31.97.111.175:8002'
const CORS_ORIGINS = process.env.CORS_ORIGINS?.split(',') || ['*']

// Initialize Express app
const app = express()

// Middleware
app.use(helmet({ contentSecurityPolicy: false }))
app.use(cors({ origin: CORS_ORIGINS, credentials: true }))
app.use(morgan('combined'))
app.use(express.json())

// Health check (no auth required)
app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'mantra-mcp',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  })
})

// API info
app.get('/', (_req, res) => {
  res.json({
    name: 'MANTRA MCP Server',
    description: 'Constitutional Law Decision System - MCP Interface',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      mcp: '/mcp (SSE)',
      docs: '/docs'
    },
    tools: toolDefinitions.map(t => t.name),
    resources: resourceDefinitions.map(r => r.uri)
  })
})

// Documentation
app.get('/docs', (_req, res) => {
  res.json({
    setup: {
      description: 'Add this to your Claude Code MCP settings',
      config: {
        mcpServers: {
          mantra: {
            url: `http://${HOST === '0.0.0.0' ? 'YOUR_SERVER_IP' : HOST}:${PORT}/mcp`,
            transport: 'sse',
            headers: {
              Authorization: 'Bearer YOUR_API_KEY'
            }
          }
        }
      }
    },
    tools: toolDefinitions,
    resources: resourceDefinitions,
    prompts: promptDefinitions
  })
})

// Store active SSE connections
const connections = new Map<string, {
  transport: SSEServerTransport
  server: Server
  apiKey: string
  createdAt: Date
}>()

// MCP SSE endpoint
app.get('/mcp', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const apiKey = req.apiKey!
  const connectionId = `${apiKey}-${Date.now()}`

  console.log(`[MCP] New SSE connection: ${connectionId}`)

  // Create MCP server instance for this connection
  const server = new Server(
    {
      name: 'mantra-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
        resources: {},
        prompts: {},
      },
    }
  )

  // Initialize MANTRA API client
  const mantraClient = new MantraClient(MANTRA_API_URL, apiKey)

  // Register tool handlers
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: toolDefinitions
  }))

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params
    const handler = toolHandlers[name]

    if (!handler) {
      throw new Error(`Unknown tool: ${name}`)
    }

    console.log(`[MCP] Tool call: ${name}`, args)
    return handler(args || {}, mantraClient)
  })

  // Register resource handlers
  server.setRequestHandler(ListResourcesRequestSchema, async () => ({
    resources: resourceDefinitions
  }))

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const { uri } = request.params
    const handler = resourceHandlers[uri]

    if (!handler) {
      // Try pattern matching for dynamic resources
      for (const [pattern, h] of Object.entries(resourceHandlers)) {
        if (pattern.includes('{') && matchUriPattern(pattern, uri)) {
          console.log(`[MCP] Resource read: ${uri}`)
          return h(uri, mantraClient)
        }
      }
      throw new Error(`Unknown resource: ${uri}`)
    }

    console.log(`[MCP] Resource read: ${uri}`)
    return handler(uri, mantraClient)
  })

  // Register prompt handlers
  server.setRequestHandler(ListPromptsRequestSchema, async () => ({
    prompts: promptDefinitions
  }))

  server.setRequestHandler(GetPromptRequestSchema, async (request) => {
    const { name, arguments: args } = request.params
    const handler = promptHandlers[name]

    if (!handler) {
      throw new Error(`Unknown prompt: ${name}`)
    }

    console.log(`[MCP] Prompt request: ${name}`, args)
    return handler(args, mantraClient)
  })

  // Create SSE transport
  const transport = new SSEServerTransport('/mcp', res)

  // Store connection
  connections.set(connectionId, {
    transport,
    server,
    apiKey,
    createdAt: new Date()
  })

  // Handle disconnect
  res.on('close', () => {
    console.log(`[MCP] Connection closed: ${connectionId}`)
    connections.delete(connectionId)
  })

  // Connect server to transport
  await server.connect(transport)
})

// MCP POST endpoint for messages
app.post('/mcp', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const apiKey = req.apiKey!

  // Find active connection for this API key
  const connection = Array.from(connections.values()).find(c => c.apiKey === apiKey)

  if (!connection) {
    res.status(400).json({ error: 'No active SSE connection. Connect to GET /mcp first.' })
    return
  }

  // Forward message to transport
  await connection.transport.handlePostMessage(req, res)
})

// Helper function to match URI patterns
function matchUriPattern(pattern: string, uri: string): boolean {
  const patternParts = pattern.split('/')
  const uriParts = uri.split('/')

  if (patternParts.length !== uriParts.length) return false

  return patternParts.every((part, i) => {
    if (part.startsWith('{') && part.endsWith('}')) return true
    return part === uriParts[i]
  })
}

// Error handler
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('[Error]', err)
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  })
})

// Start server
app.listen(PORT, HOST, () => {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║           MANTRA MCP Server - Constitutional Law             ║
╠══════════════════════════════════════════════════════════════╣
║  Status:    Running                                          ║
║  Host:      ${HOST.padEnd(46)}║
║  Port:      ${String(PORT).padEnd(46)}║
║  API:       ${MANTRA_API_URL.padEnd(46)}║
║                                                              ║
║  Endpoints:                                                  ║
║    GET  /         - API info                                 ║
║    GET  /health   - Health check                             ║
║    GET  /docs     - Documentation                            ║
║    GET  /mcp      - SSE connection                           ║
║    POST /mcp      - MCP messages                             ║
╚══════════════════════════════════════════════════════════════╝
  `)
})

export default app
