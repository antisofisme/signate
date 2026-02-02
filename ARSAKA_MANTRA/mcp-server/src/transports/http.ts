/**
 * Streamable HTTP Transport for MANTRA MCP Server
 * 
 * Per MCP Spec 2025-11-25:
 * - Single endpoint supporting POST and GET
 * - POST for client messages
 * - GET for server-initiated streams (optional)
 * - Session management via MCP-Session-Id header
 */

import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { v4 as uuidv4 } from 'uuid';

import { createServer } from '../index.js';
import { MantraClient } from '../client.js';
import { toolDefinitions } from '../tools/index.js';
import { resourceDefinitions } from '../resources/index.js';
import { promptDefinitions } from '../prompts/index.js';

// Configuration
const PORT = parseInt(process.env.PORT || '8004');
const HOST = process.env.HOST || '0.0.0.0';
const MANTRA_API_URL = process.env.MANTRA_API_URL || 'http://localhost:8002';
const CORS_ORIGINS = process.env.CORS_ORIGINS?.split(',') || ['*'];
const MASTER_KEY = process.env.MANTRA_MCP_MASTER_KEY;

// Validate required environment variables
if (!MASTER_KEY) {
  console.error('ERROR: MANTRA_MCP_MASTER_KEY environment variable is required');
  process.exit(1);
}

// Session storage
interface Session {
  id: string;
  apiKey: string;
  mantraClient: MantraClient;
  createdAt: Date;
  lastActivity: Date;
}

const sessions = new Map<string, Session>();
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes

// Extend Express Request
declare global {
  namespace Express {
    interface Request {
      apiKey?: string;
      session?: Session;
    }
  }
}

/**
 * Authentication middleware
 */
function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing or invalid Authorization header' });
    return;
  }
  
  const apiKey = authHeader.slice(7);
  
  // Validate API key (simple check - in production, validate against DB)
  if (!apiKey.startsWith('mk_') && !apiKey.startsWith('sk_')) {
    res.status(403).json({ error: 'Invalid API key format' });
    return;
  }
  
  req.apiKey = apiKey;
  next();
}

/**
 * Session middleware
 */
function sessionMiddleware(req: Request, res: Response, next: NextFunction) {
  const sessionId = req.headers['mcp-session-id'] as string;
  
  if (sessionId) {
    const session = sessions.get(sessionId);
    if (session) {
      session.lastActivity = new Date();
      req.session = session;
    }
  }
  
  next();
}

/**
 * Clean up expired sessions
 */
function cleanupSessions() {
  const now = Date.now();
  for (const [id, session] of sessions) {
    if (now - session.lastActivity.getTime() > SESSION_TIMEOUT) {
      sessions.delete(id);
      console.log('[Session] Expired:', id);
    }
  }
}

// Run cleanup every 5 minutes
setInterval(cleanupSessions, 5 * 60 * 1000);

/**
 * Start HTTP server with Streamable HTTP transport
 */
export async function startHttpServer() {
  const app = express();
  
  // Middleware
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(cors({ origin: CORS_ORIGINS, credentials: true }));
  app.use(morgan('combined'));
  app.use(express.json());
  
  // Health check (no auth)
  app.get('/health', (_req, res) => {
    res.json({
      status: 'healthy',
      service: 'mantra-mcp',
      version: '2.0.0',
      transport: 'streamable-http',
      timestamp: new Date().toISOString(),
      activeSessions: sessions.size
    });
  });
  
  // API info (no auth)
  app.get('/', (_req, res) => {
    res.json({
      name: 'MANTRA MCP Server',
      description: 'Constitutional Law Decision System - MCP Interface',
      version: '2.0.0',
      protocol: 'MCP 2025-11-25',
      transports: ['stdio', 'streamable-http'],
      endpoints: {
        health: 'GET /health',
        mcp: 'POST /mcp (Streamable HTTP)',
        docs: 'GET /docs'
      },
      tools: toolDefinitions.map(t => t.name),
      resources: resourceDefinitions.map(r => r.uri)
    });
  });
  
  // Documentation
  app.get('/docs', (_req, res) => {
    res.json({
      setup: {
        stdio: {
          description: 'For Claude Code local integration (recommended)',
          config: {
            mcpServers: {
              mantra: {
                command: 'node',
                args: ['/path/to/mantra-mcp/dist/index.js', '--stdio'],
                env: {
                  MANTRA_API_URL: MANTRA_API_URL,
                  MANTRA_API_KEY: 'YOUR_API_KEY'
                }
              }
            }
          }
        },
        http: {
          description: 'For remote clients',
          config: {
            mcpServers: {
              mantra: {
                type: 'http',
                url: 'http://YOUR_SERVER_IP:' + PORT + '/mcp',
                headers: {
                  Authorization: 'Bearer YOUR_API_KEY'
                }
              }
            }
          }
        }
      },
      tools: toolDefinitions,
      resources: resourceDefinitions,
      prompts: promptDefinitions
    });
  });
  
  // MCP Endpoint - Streamable HTTP
  app.post('/mcp', authMiddleware, sessionMiddleware, async (req, res) => {
    try {
      const message = req.body;
      const apiKey = req.apiKey!;
      
      // Handle initialization
      if (message.method === 'initialize') {
        const sessionId = uuidv4();
        const mantraClient = new MantraClient(MANTRA_API_URL, apiKey);
        
        const session: Session = {
          id: sessionId,
          apiKey,
          mantraClient,
          createdAt: new Date(),
          lastActivity: new Date()
        };
        
        sessions.set(sessionId, session);
        
        res.setHeader('MCP-Session-Id', sessionId);
        res.setHeader('MCP-Protocol-Version', '2025-11-25');
        res.json({
          jsonrpc: '2.0',
          id: message.id,
          result: {
            protocolVersion: '2025-11-25',
            capabilities: { tools: {}, resources: {}, prompts: {} },
            serverInfo: { name: 'mantra-mcp', version: '2.0.0' }
          }
        });
        
        console.log('[Session] Created:', sessionId);
        return;
      }
      
      // Require session for other requests
      if (!req.session) {
        res.status(400).json({ 
          jsonrpc: '2.0',
          error: { code: -32600, message: 'No active session. Send initialize first.' }
        });
        return;
      }
      
      const { mantraClient } = req.session;
      
      // Handle different message types
      if (message.method === 'tools/list') {
        res.json({ jsonrpc: '2.0', id: message.id, result: { tools: toolDefinitions } });
      } else if (message.method === 'tools/call') {
        const { name, arguments: args } = message.params;
        const { toolHandlers } = await import('../tools/index.js');
        const handler = toolHandlers[name];
        
        if (!handler) {
          res.json({ jsonrpc: '2.0', id: message.id, error: { code: -32601, message: 'Unknown tool: ' + name } });
          return;
        }
        
        console.log('[MCP] Tool call:', name);
        const result = await handler(args || {}, mantraClient);
        res.json({ jsonrpc: '2.0', id: message.id, result });
      } else if (message.method === 'resources/list') {
        res.json({ jsonrpc: '2.0', id: message.id, result: { resources: resourceDefinitions } });
      } else if (message.method === 'resources/read') {
        const { uri } = message.params;
        const { resourceHandlers } = await import('../resources/index.js');
        const handler = resourceHandlers[uri];
        
        if (!handler) {
          res.json({ jsonrpc: '2.0', id: message.id, error: { code: -32601, message: 'Unknown resource: ' + uri } });
          return;
        }
        
        console.log('[MCP] Resource read:', uri);
        const result = await handler(uri, mantraClient);
        res.json({ jsonrpc: '2.0', id: message.id, result });
      } else if (message.method === 'prompts/list') {
        res.json({ jsonrpc: '2.0', id: message.id, result: { prompts: promptDefinitions } });
      } else if (message.method === 'prompts/get') {
        const { name, arguments: args } = message.params;
        const { promptHandlers } = await import('../prompts/index.js');
        const handler = promptHandlers[name];
        
        if (!handler) {
          res.json({ jsonrpc: '2.0', id: message.id, error: { code: -32601, message: 'Unknown prompt: ' + name } });
          return;
        }
        
        console.log('[MCP] Prompt get:', name);
        const result = await handler(args, mantraClient);
        res.json({ jsonrpc: '2.0', id: message.id, result });
      } else if (message.method === 'notifications/initialized') {
        res.status(202).send();
      } else {
        res.json({ jsonrpc: '2.0', id: message.id, error: { code: -32601, message: 'Method not found: ' + message.method } });
      }
    } catch (error) {
      console.error('[MCP] Error:', error);
      res.status(500).json({
        jsonrpc: '2.0',
        error: { code: -32603, message: error instanceof Error ? error.message : 'Internal error' }
      });
    }
  });
  
  // DELETE: Terminate session
  app.delete('/mcp', authMiddleware, sessionMiddleware, (req, res) => {
    if (req.session) {
      sessions.delete(req.session.id);
      console.log('[Session] Terminated:', req.session.id);
      res.status(204).send();
    } else {
      res.status(404).json({ error: 'Session not found' });
    }
  });
  
  // Error handler
  app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
    console.error('[Error]', err);
    res.status(500).json({ error: 'Internal server error', message: err.message });
  });
  
  // Start server
  app.listen(PORT, HOST, () => {
    console.log('');
    console.log('MANTRA MCP Server v2.0 - Streamable HTTP Transport');
    console.log('==================================================');
    console.log('Host:     ', HOST);
    console.log('Port:     ', PORT);
    console.log('API:      ', MANTRA_API_URL);
    console.log('Protocol:  MCP 2025-11-25');
    console.log('');
  });
}
