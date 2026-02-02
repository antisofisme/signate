# MANTRA MCP Server

Remote MCP (Model Context Protocol) server for the MANTRA Constitutional Law Decision System.

## Overview

This MCP server allows AI assistants (like Claude) to:
- **Search** existing decisions and principles
- **Propose** new decisions for review
- **Validate** decisions against constitutional principles
- **Get hints** based on implementation context

## Quick Setup for Users

### 1. Get API Key

Get your API key from MANTRA Dashboard:
- Go to http://31.97.111.175:3001/settings/api-keys
- Create new API key
- Copy the key (starts with `mk_`)

### 2. Configure Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "mantra": {
      "url": "http://31.97.111.175:8004/mcp",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_HERE"
      }
    }
  }
}
```

### 3. Start Using

In Claude Code, you can now use MANTRA tools:

```
"Search for authentication decisions"
→ Claude will use mantra_search_decisions

"Propose a new caching decision"
→ Claude will use mantra_propose_decision

"Check if my implementation follows MANTRA guidelines"
→ Claude will use mantra_validate_decision
```

## Available Tools

| Tool | Description |
|------|-------------|
| `mantra_search_decisions` | Search decisions by query, group, status, layer |
| `mantra_get_decision` | Get full details of a specific decision |
| `mantra_get_principles` | Get Layer 0 principles for a domain |
| `mantra_propose_decision` | Propose a new decision for review |
| `mantra_validate_decision` | Validate decision against principles |
| `mantra_get_hints` | Get AI hints based on context |
| `mantra_compare_decisions` | Compare two decisions |
| `mantra_get_grouped` | Get all decisions by group |

## Available Resources

| URI | Description |
|-----|-------------|
| `mantra://decisions` | All decisions |
| `mantra://decisions/accepted` | Accepted decisions only |
| `mantra://principles` | Layer 0 principles |
| `mantra://groups` | Decisions by group |
| `mantra://decisions/{id}` | Specific decision |
| `mantra://audit` | Audit log |

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `review_decision` | Review a decision for compliance |
| `suggest_decision` | Get suggestions for creating a decision |
| `check_compliance` | Check implementation compliance |
| `generate_rationale` | Generate rationale and alternatives |

## Development

### Local Development

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build
npm run build

# Run production
npm start
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8004 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `MANTRA_API_URL` | http://31.97.111.175:8002 | MANTRA backend URL |
| `CORS_ORIGINS` | * | Allowed CORS origins |
| `MANTRA_MCP_MASTER_KEY` | - | Master API key for admin |

### Docker Build

```bash
docker build -t mantra-mcp-server:v1.0.0 .
```

### Deploy to Nomad

```bash
nomad job run mantra-mcp.nomad
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/docs` | GET | Documentation |
| `/mcp` | GET | SSE connection (MCP) |
| `/mcp` | POST | MCP messages |

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Claude Code    │   SSE   │  MANTRA MCP     │
│  + MCP Client   │◄───────►│  Server (:8004) │
└─────────────────┘         └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  MANTRA Backend │
                            │  API (:8002)    │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  PostgreSQL     │
                            │  (Decisions DB) │
                            └─────────────────┘
```

## License

Internal use only - ATLAS Project
