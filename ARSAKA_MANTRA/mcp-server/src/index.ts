/**
 * MANTRA MCP Server v2.0
 * 
 * Dual Transport Support:
 * - STDIO: For Claude Code local integration (recommended)
 * - Streamable HTTP: For remote clients
 * 
 * Usage:
 *   node dist/index.js --stdio     # STDIO mode (for Claude Code)
 *   node dist/index.js --http      # HTTP mode (for remote)
 *   node dist/index.js             # Default: HTTP mode
 * 
 * Per MCP Spec 2025-11-25
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { startHttpServer } from './transports/http.js';
import { toolHandlers, toolDefinitions } from './tools/index.js';
import { resourceHandlers, resourceDefinitions } from './resources/index.js';
import { promptHandlers, promptDefinitions } from './prompts/index.js';
import { MantraClient } from './client.js';

// Configuration
const MANTRA_API_URL = process.env.MANTRA_API_URL || 'http://localhost:8002';
const MANTRA_API_KEY = process.env.MANTRA_API_KEY;

// Validate required environment variables (only for STDIO mode which uses this directly)
if (!MANTRA_API_KEY && process.argv.includes('--stdio')) {
  console.error('ERROR: MANTRA_API_KEY environment variable is required for STDIO mode');
  process.exit(1);
}

/**
 * Create and configure MCP Server instance
 */
export function createServer(mantraClient: MantraClient): Server {
  const server = new Server(
    {
      name: 'mantra-mcp',
      version: '2.0.0',
    },
    {
      capabilities: {
        tools: {},
        resources: {},
        prompts: {},
      },
    }
  );

  // Register tool handlers
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: toolDefinitions
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    const handler = toolHandlers[name];
    
    if (!handler) {
      throw new Error(`Unknown tool: ${name}`);
    }
    
    console.error(`[MCP] Tool call: ${name}`);
    return handler(args || {}, mantraClient);
  });

  // Register resource handlers
  server.setRequestHandler(ListResourcesRequestSchema, async () => ({
    resources: resourceDefinitions
  }));

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const { uri } = request.params;
    const handler = resourceHandlers[uri];
    
    if (!handler) {
      // Try pattern matching for dynamic resources
      for (const [pattern, h] of Object.entries(resourceHandlers)) {
        if (pattern.includes('{') && matchUriPattern(pattern, uri)) {
          console.error(`[MCP] Resource read: ${uri}`);
          return h(uri, mantraClient);
        }
      }
      throw new Error(`Unknown resource: ${uri}`);
    }
    
    console.error(`[MCP] Resource read: ${uri}`);
    return handler(uri, mantraClient);
  });

  // Register prompt handlers
  server.setRequestHandler(ListPromptsRequestSchema, async () => ({
    prompts: promptDefinitions
  }));

  server.setRequestHandler(GetPromptRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    const handler = promptHandlers[name];
    
    if (!handler) {
      throw new Error(`Unknown prompt: ${name}`);
    }
    
    console.error(`[MCP] Prompt request: ${name}`);
    return handler(args, mantraClient);
  });

  return server;
}

/**
 * Match URI patterns like "decisions://{id}"
 */
function matchUriPattern(pattern: string, uri: string): boolean {
  const patternParts = pattern.split('/');
  const uriParts = uri.split('/');
  
  if (patternParts.length !== uriParts.length) return false;
  
  return patternParts.every((part, i) => {
    if (part.startsWith('{') && part.endsWith('}')) return true;
    return part === uriParts[i];
  });
}

/**
 * Start STDIO transport (for Claude Code)
 */
async function startStdio() {
  console.error('Starting MANTRA MCP Server in STDIO mode...');
  console.error(`MANTRA API: ${MANTRA_API_URL}`);
  
  const mantraClient = new MantraClient(MANTRA_API_URL, MANTRA_API_KEY);
  const server = createServer(mantraClient);
  const transport = new StdioServerTransport();
  
  await server.connect(transport);
  
  console.error('MANTRA MCP Server running (STDIO)');
}

/**
 * Main entry point
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--stdio')) {
    await startStdio();
  } else if (args.includes('--http') || args.length === 0) {
    // HTTP mode is default
    await startHttpServer();
  } else {
    console.error('Usage: node index.js [--stdio|--http]');
    console.error('  --stdio  Run in STDIO mode (for Claude Code)');
    console.error('  --http   Run in HTTP mode (default, for remote clients)');
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
