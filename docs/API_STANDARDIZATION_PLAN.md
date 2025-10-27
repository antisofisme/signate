# API Standardization & Architecture Improvement Plan
## Smart TV Digital Signage System

**Document Version:** 1.0.0
**Date:** October 27, 2025
**Status:** Implementation Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [API Design Standards](#3-api-design-standards)
4. [Contract-First Development](#4-contract-first-development)
5. [Architecture Layers](#5-architecture-layers)
6. [Validation & Error Handling](#6-validation--error-handling)
7. [Migration Strategy](#7-migration-strategy)
8. [Implementation Examples](#8-implementation-examples)
9. [Testing Strategy](#9-testing-strategy)
10. [Performance & Monitoring](#10-performance--monitoring)
11. [Security Considerations](#11-security-considerations)
12. [Implementation Timeline](#12-implementation-timeline)
13. [Appendices](#13-appendices)

---

## 1. Executive Summary

### 1.1 Purpose
This document outlines a comprehensive plan to standardize and improve the API architecture of the Smart TV Digital Signage system. The goal is to establish a scalable, maintainable, and consistent API layer that serves as the foundation for all system communications.

### 1.2 Key Objectives
- **Standardization**: Implement consistent RESTful API patterns across all endpoints
- **Contract-First**: Establish OpenAPI 3.1 specifications as the single source of truth
- **Type Safety**: Ensure compile-time and runtime validation across all layers
- **Maintainability**: Create clear separation of concerns with proper abstraction layers
- **Scalability**: Design for future growth with versioning and backward compatibility

### 1.3 Expected Outcomes
- Reduced development time through auto-generated clients and documentation
- Decreased bug rate from type mismatches and API contract violations
- Improved developer experience with consistent patterns and clear documentation
- Enhanced system reliability through comprehensive validation
- Simplified onboarding for new team members

### 1.4 Success Metrics
- 100% API endpoint coverage with OpenAPI specifications
- Zero runtime type errors in production
- 50% reduction in API-related bug reports
- 80% reduction in API integration time for new features
- Complete elimination of naming inconsistencies

---

## 2. Current State Analysis

### 2.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Current Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Web Admin   │    │   Viewer     │    │   Anthias    │  │
│  │  (React)     │    │ (Vanilla JS) │    │    (CMS)     │  │
│  │  Port 3000   │    │  Port 8080   │    │  Port 8000   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘  │
│         │                    │                                │
│         │                    │                                │
│     Direct fetch()       Direct fetch()                       │
│         │                    │                                │
│         ▼                    ▼                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Backend API (FastAPI)                      │  │
│  │                  Port 8001                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Identified Problems

#### 2.2.1 Inconsistent Naming Conventions
**Current State:**
```javascript
// Different naming for similar operations
devicesAPI.registerTV()        // "register" for creation
contentAPI.upload()             // "upload" for creation
tagsAPI.create()               // "create" for creation
contentAPI.assign()            // "assign" for association
devicesAPI.assignContent()    // "assignContent" for association
```

**Impact:** Cognitive overhead, increased learning curve, potential for errors

#### 2.2.2 No API Client Abstraction
**Current State:**
```javascript
// Web Admin - Direct axios calls
const response = await api.get('/api/devices', { params })

// Viewer - Direct fetch calls
const response = await fetch(`${API_BASE_URL}/api/client/playlist?device_id=${deviceId}`)
```

**Impact:** Code duplication, inconsistent error handling, difficult to maintain

#### 2.2.3 Inconsistent Response Formats
**Current State:**
```python
# Different response structures
return {"status": "success", "data": content}  # Some endpoints
return content  # Other endpoints
return {"message": "Created", "id": device.id}  # Yet others
```

**Impact:** Client-side complexity, unpredictable data handling

#### 2.2.4 Database Schema Issues
**Current State:**
- Table naming confusion: `content` vs `contents`
- Migration conflicts in versions 007
- No clear naming convention for junction tables

**Impact:** Database integrity risks, migration failures, confusion

#### 2.2.5 Missing Contract Validation
**Current State:**
- No OpenAPI specification
- Manual type checking in frontend
- Runtime errors from type mismatches

**Impact:** Increased bug rate, longer development cycles

### 2.3 Technical Debt Analysis

| Area | Debt Level | Impact | Priority |
|------|------------|--------|----------|
| API Naming | High | Developer confusion, maintenance overhead | Critical |
| Response Formats | High | Client complexity, error handling issues | Critical |
| Type Safety | Medium | Runtime errors, debugging time | High |
| Documentation | High | Onboarding difficulty, integration errors | High |
| Database Schema | Medium | Data integrity risks | Medium |
| Versioning | Low | Future compatibility issues | Medium |

---

## 3. API Design Standards

### 3.1 RESTful Principles

#### 3.1.1 Resource Naming Convention
```
/api/{version}/{resource}/{id}/{sub-resource}
```

**Standards:**
- Use plural nouns for collections: `/devices`, `/contents`, `/tags`
- Use kebab-case for multi-word resources: `/speed-tests`, `/activity-logs`
- Avoid verbs in resource names (use HTTP methods instead)

#### 3.1.2 HTTP Method Semantics

| Method | Purpose | Idempotent | Safe | Example |
|--------|---------|------------|------|---------|
| GET | Retrieve resource(s) | Yes | Yes | `GET /api/v1/devices` |
| POST | Create new resource | No | No | `POST /api/v1/devices` |
| PUT | Full update | Yes | No | `PUT /api/v1/devices/123` |
| PATCH | Partial update | No | No | `PATCH /api/v1/devices/123` |
| DELETE | Remove resource | Yes | No | `DELETE /api/v1/devices/123` |

#### 3.1.3 Resource Operations Mapping

**Standard CRUD Operations:**
```
GET    /api/v1/devices          → List all devices
GET    /api/v1/devices/{id}     → Get specific device
POST   /api/v1/devices          → Create new device
PUT    /api/v1/devices/{id}     → Full update device
PATCH  /api/v1/devices/{id}     → Partial update device
DELETE /api/v1/devices/{id}     → Delete device
```

**Resource Relationships:**
```
# One-to-Many
GET    /api/v1/devices/{id}/contents     → List device contents
POST   /api/v1/devices/{id}/contents     → Assign content to device
DELETE /api/v1/devices/{id}/contents/{content_id}  → Unassign content

# Many-to-Many
GET    /api/v1/tags/{id}/devices        → List devices with tag
POST   /api/v1/tag-assignments          → Create tag assignment
DELETE /api/v1/tag-assignments/{id}     → Remove tag assignment
```

**Custom Actions (when unavoidable):**
```
POST   /api/v1/devices/{id}/activate    → Activate device
POST   /api/v1/devices/{id}/heartbeat   → Send heartbeat
POST   /api/v1/speed-tests              → Run speed test
```

### 3.2 Versioning Strategy

#### 3.2.1 URL Path Versioning
```
/api/v1/devices
/api/v2/devices
```

**Benefits:**
- Clear version visibility
- Easy to route and maintain
- Simple client implementation

#### 3.2.2 Version Lifecycle
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Active  │ →  │ Deprecated│ →  │  Sunset  │ →  │ Removed  │
│ (Current)│    │ (6 months)│    │(3 months)│    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 3.3 Response Format Standardization

#### 3.3.1 Success Response Structure
```json
{
  "data": {
    // Resource data
  },
  "meta": {
    "timestamp": "2025-10-27T12:00:00Z",
    "version": "1.0.0"
  }
}
```

#### 3.3.2 Collection Response Structure
```json
{
  "data": [
    // Array of resources
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  },
  "meta": {
    "timestamp": "2025-10-27T12:00:00Z",
    "version": "1.0.0"
  }
}
```

#### 3.3.3 Error Response Structure
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Device not found",
    "details": {
      "device_id": "123",
      "timestamp": "2025-10-27T12:00:00Z"
    },
    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 3.4 HTTP Status Code Conventions

| Status Code | Meaning | Use Case |
|------------|---------|----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST creating resource |
| 202 | Accepted | Request accepted for async processing |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Conflicting resource state |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Service temporarily down |

### 3.5 Query Parameter Standards

#### 3.5.1 Filtering
```
GET /api/v1/devices?status=active&tag=lobby
```

#### 3.5.2 Sorting
```
GET /api/v1/devices?sort=created_at&order=desc
```

#### 3.5.3 Pagination
```
GET /api/v1/devices?page=2&limit=20
```

#### 3.5.4 Field Selection
```
GET /api/v1/devices?fields=id,name,status,last_seen
```

#### 3.5.5 Search
```
GET /api/v1/devices?q=monitor&search_in=name,description
```

---

## 4. Contract-First Development

### 4.1 OpenAPI 3.1 Specification

#### 4.1.1 Specification Structure
```yaml
# /api-spec/openapi.yaml
openapi: 3.1.0
info:
  title: Smart TV Digital Signage API
  version: 1.0.0
  description: |
    Comprehensive API for managing digital signage devices,
    content, and playback across Smart TV and monitor displays.
  contact:
    name: API Support
    email: api@signage.local
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://192.168.5.12:8001/api/v1
    description: Production server
  - url: http://localhost:8001/api/v1
    description: Development server

tags:
  - name: devices
    description: Device management operations
  - name: content
    description: Content management operations
  - name: playlists
    description: Playlist management
  - name: tags
    description: Tag management
  - name: auth
    description: Authentication operations

paths:
  /devices:
    get:
      tags: [devices]
      summary: List all devices
      operationId: listDevices
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/DeviceStatus'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeviceListResponse'

components:
  schemas:
    Device:
      type: object
      required: [id, name, type, status]
      properties:
        id:
          type: integer
          format: int64
        name:
          type: string
          minLength: 1
          maxLength: 100
        type:
          $ref: '#/components/schemas/DeviceType'
        status:
          $ref: '#/components/schemas/DeviceStatus'
        activation_code:
          type: string
          pattern: '^[0-9]{6}$'
        last_seen:
          type: string
          format: date-time
        created_at:
          type: string
          format: date-time
```

#### 4.1.2 Schema Generation Strategy

**Backend (FastAPI) → OpenAPI:**
```python
# Automatic generation from Pydantic models
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Smart TV Digital Signage API",
        version="1.0.0",
        description="API Documentation",
        routes=app.routes,
    )

    # Custom modifications
    openapi_schema["info"]["x-logo"] = {
        "url": "https://signage.local/logo.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 4.2 Code Generation Pipeline

#### 4.2.1 TypeScript Client Generation
```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -D

# Generate TypeScript client
npx openapi-generator-cli generate \
  -i ./api-spec/openapi.yaml \
  -g typescript-fetch \
  -o ./web-admin/src/api/generated \
  --additional-properties=supportsES6=true,npmName=@signage/api-client
```

#### 4.2.2 Generated Client Structure
```typescript
// web-admin/src/api/generated/apis/DevicesApi.ts
export class DevicesApi extends BaseAPI {
    async listDevices(
        requestParameters: ListDevicesRequest = {},
        initOverrides?: RequestInit
    ): Promise<DeviceListResponse> {
        const response = await this.request({
            path: `/devices`,
            method: 'GET',
            query: {
                page: requestParameters.page,
                limit: requestParameters.limit,
                status: requestParameters.status,
            },
        });
        return await response.json();
    }

    async createDevice(
        requestParameters: CreateDeviceRequest,
        initOverrides?: RequestInit
    ): Promise<Device> {
        const response = await this.request({
            path: `/devices`,
            method: 'POST',
            body: requestParameters.device,
        });
        return await response.json();
    }
}
```

### 4.3 Contract Validation

#### 4.3.1 Request Validation Pipeline
```
┌────────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│   Client   │ →  │   Zod     │ →  │  Request │ →  │ Pydantic │
│   Input    │    │Validation │    │          │    │Validation│
└────────────┘    └───────────┘    └──────────┘    └──────────┘
                       ↓                                 ↓
                   Invalid: 400                     Invalid: 422
```

#### 4.3.2 Response Validation Pipeline
```
┌──────────┐    ┌──────────┐    ┌───────────┐    ┌────────────┐
│ Database │ →  │ Pydantic │ →  │ Response  │ →  │    Zod     │
│   Data   │    │  Schema  │    │           │    │ Validation │
└──────────┘    └──────────┘    └───────────┘    └────────────┘
```

---

## 5. Architecture Layers

### 5.1 Backend Architecture (FastAPI)

#### 5.1.1 Directory Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/                 # Version 1 endpoints
│   │   │   ├── __init__.py
│   │   │   ├── devices.py
│   │   │   ├── content.py
│   │   │   ├── playlists.py
│   │   │   └── tags.py
│   │   └── v2/                 # Future version
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   ├── security.py         # Auth & security
│   │   └── database.py         # Database setup
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── device.py
│   │   ├── content.py
│   │   └── base.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── device.py
│   │   ├── content.py
│   │   └── common.py          # Shared schemas
│   ├── services/               # Business logic
│   │   ├── device_service.py
│   │   ├── content_service.py
│   │   └── anthias_service.py
│   ├── repositories/           # Data access layer
│   │   ├── device_repo.py
│   │   └── content_repo.py
│   └── main.py                # Application entry
├── tests/
├── migrations/
└── requirements.txt
```

#### 5.1.2 Layered Architecture Pattern
```python
# API Layer (app/api/v1/devices.py)
from fastapi import APIRouter, Depends, status
from app.schemas.device import DeviceCreate, DeviceResponse
from app.services.device_service import DeviceService

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    service: DeviceService = Depends()
):
    """Create a new device"""
    return await service.create_device(device)

# Service Layer (app/services/device_service.py)
from app.repositories.device_repo import DeviceRepository
from app.schemas.device import DeviceCreate
from app.models.device import Device

class DeviceService:
    def __init__(self, repo: DeviceRepository = Depends()):
        self.repo = repo

    async def create_device(self, device_data: DeviceCreate) -> Device:
        # Business logic
        if await self.repo.exists_by_name(device_data.name):
            raise ValueError("Device name already exists")

        # Create device
        return await self.repo.create(device_data)

# Repository Layer (app/repositories/device_repo.py)
from sqlalchemy.orm import Session
from app.models.device import Device
from app.core.database import get_db

class DeviceRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def create(self, device_data: dict) -> Device:
        device = Device(**device_data.dict())
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    async def exists_by_name(self, name: str) -> bool:
        return self.db.query(Device).filter(Device.name == name).first() is not None
```

### 5.2 Web Admin Architecture (React)

#### 5.2.1 Directory Structure
```
web-admin/src/
├── api/
│   ├── generated/              # OpenAPI generated code
│   │   ├── apis/
│   │   ├── models/
│   │   └── runtime.ts
│   ├── client.ts               # API client configuration
│   ├── hooks/                  # React hooks for API
│   │   ├── useDevices.ts
│   │   ├── useContent.ts
│   │   └── usePlaylists.ts
│   └── services/               # Service layer
│       ├── DeviceService.ts
│       ├── ContentService.ts
│       └── BaseService.ts
├── types/
│   ├── api.ts                  # API types
│   └── domain.ts               # Domain types
├── utils/
│   ├── validation.ts           # Zod schemas
│   └── error-handler.ts
└── config/
    └── api.config.ts
```

#### 5.2.2 API Client Pattern
```typescript
// api/client.ts
import { Configuration, DevicesApi, ContentApi } from './generated';

class ApiClient {
  private config: Configuration;
  public devices: DevicesApi;
  public content: ContentApi;

  constructor() {
    this.config = new Configuration({
      basePath: import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
      middleware: [
        {
          pre: async (context) => {
            const token = localStorage.getItem('token');
            if (token) {
              context.init.headers = {
                ...context.init.headers,
                Authorization: `Bearer ${token}`,
              };
            }
            return context;
          },
          post: async (context) => {
            if (context.response.status === 401) {
              localStorage.removeItem('token');
              window.location.href = '/login';
            }
            return context;
          },
        },
      ],
    });

    this.devices = new DevicesApi(this.config);
    this.content = new ContentApi(this.config);
  }
}

export const apiClient = new ApiClient();
```

#### 5.2.3 React Hook Pattern
```typescript
// api/hooks/useDevices.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { z } from 'zod';
import { DeviceSchema } from '../../utils/validation';

export const useDevices = (filters?: DeviceFilters) => {
  return useQuery({
    queryKey: ['devices', filters],
    queryFn: () => apiClient.devices.listDevices(filters),
    select: (data) => {
      // Validate response with Zod
      return z.array(DeviceSchema).parse(data.data);
    },
  });
};

export const useCreateDevice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (device: DeviceCreate) => {
      // Validate input with Zod
      const validated = DeviceCreateSchema.parse(device);
      return apiClient.devices.createDevice({ device: validated });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });
};
```

### 5.3 Viewer Architecture (Vanilla JS)

#### 5.3.1 Directory Structure
```
viewer/js/
├── api/
│   ├── client.js               # API client
│   ├── endpoints.js            # Endpoint definitions
│   └── validator.js            # Response validation
├── services/
│   ├── DeviceService.js
│   ├── ContentService.js
│   └── PlaylistService.js
├── utils/
│   ├── http.js                 # HTTP utilities
│   └── error-handler.js
└── config/
    └── api.config.js
```

#### 5.3.2 Lightweight API Client
```javascript
// api/client.js
class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl || 'http://192.168.5.12:8001/api/v1';
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        throw new ApiError(response.status, await response.text());
      }

      const data = await response.json();
      return this.validateResponse(data);
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  validateResponse(data) {
    // Basic validation
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid response format');
    }
    return data;
  }

  handleError(error) {
    console.error('[API Error]', error);

    if (error.status === 401) {
      // Handle authentication error
      this.onAuthError();
    }
  }

  onAuthError() {
    // Clear local storage and reload
    localStorage.clear();
    window.location.reload();
  }

  // API Methods
  async getPlaylist(deviceId) {
    return this.request(`/client/playlists?device_id=${deviceId}`);
  }

  async sendHeartbeat(deviceId) {
    return this.request(`/devices/${deviceId}/heartbeat`, {
      method: 'POST',
    });
  }

  async registerDevice(data) {
    return this.request('/devices', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

// Export singleton instance
window.apiClient = new ApiClient();
```

### 5.4 Database Schema Standardization

#### 5.4.1 Naming Conventions
```sql
-- Tables: plural, snake_case
CREATE TABLE devices (...);
CREATE TABLE contents (...);
CREATE TABLE playlists (...);

-- Columns: snake_case
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction tables: singular components joined with underscore
CREATE TABLE device_content (...);  -- Not devices_contents
CREATE TABLE playlist_content (...);
CREATE TABLE device_tag (...);

-- Indexes: idx_{table}_{columns}
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen_at);

-- Foreign keys: fk_{table}_{column}_{reference_table}
ALTER TABLE device_content
    ADD CONSTRAINT fk_device_content_device_id_devices
    FOREIGN KEY (device_id) REFERENCES devices(id);
```

---

## 6. Validation & Error Handling

### 6.1 Backend Validation (Pydantic)

#### 6.1.1 Schema Validation
```python
# app/schemas/device.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import re

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal["tv", "monitor", "tablet"]
    location: Optional[str] = Field(None, max_length=200)
    activation_code: Optional[str] = Field(None, pattern="^[0-9]{6}$")

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "name": "Lobby Display 1",
                "type": "tv",
                "location": "Main Lobby",
                "activation_code": "123456"
            }
        }

class DeviceResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    location: Optional[str]
    last_seen: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True
```

#### 6.1.2 Custom Validators
```python
# app/schemas/validators.py
from pydantic import validator
import re

class CommonValidators:
    @staticmethod
    def validate_email(email: str) -> str:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError('Invalid email format')
        return email.lower()

    @staticmethod
    def validate_url(url: str) -> str:
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
        if not re.match(pattern, url):
            raise ValueError('Invalid URL format')
        return url

    @staticmethod
    def validate_uuid(uuid: str) -> str:
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        if not re.match(pattern, uuid, re.IGNORECASE):
            raise ValueError('Invalid UUID format')
        return uuid.lower()
```

### 6.2 Frontend Validation (Zod)

#### 6.2.1 Schema Definitions
```typescript
// utils/validation.ts
import { z } from 'zod';

// Device schemas
export const DeviceTypeSchema = z.enum(['tv', 'monitor', 'tablet']);

export const DeviceStatusSchema = z.enum(['active', 'inactive', 'pending']);

export const DeviceSchema = z.object({
  id: z.number().int().positive(),
  name: z.string().min(1).max(100),
  type: DeviceTypeSchema,
  status: DeviceStatusSchema,
  location: z.string().max(200).nullable(),
  activation_code: z.string().regex(/^[0-9]{6}$/).optional(),
  last_seen: z.string().datetime().nullable(),
  created_at: z.string().datetime(),
});

export const DeviceCreateSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(100, 'Name too long')
    .regex(/^[a-zA-Z0-9\s\-_]+$/, 'Name contains invalid characters'),
  type: DeviceTypeSchema,
  location: z.string().max(200).optional(),
  activation_code: z.string()
    .regex(/^[0-9]{6}$/, 'Activation code must be 6 digits')
    .optional(),
});

// Content schemas
export const ContentTypeSchema = z.enum(['image', 'video', 'web']);

export const ContentSchema = z.object({
  id: z.number().int().positive(),
  title: z.string().min(1).max(200),
  description: z.string().max(1000).nullable(),
  content_type: ContentTypeSchema,
  url: z.string().url(),
  duration: z.number().int().min(1).max(3600),
  is_active: z.boolean(),
  created_at: z.string().datetime(),
});

// Type inference
export type Device = z.infer<typeof DeviceSchema>;
export type DeviceCreate = z.infer<typeof DeviceCreateSchema>;
export type Content = z.infer<typeof ContentSchema>;
```

#### 6.2.2 Form Validation
```typescript
// components/DeviceForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { DeviceCreateSchema, type DeviceCreate } from '../utils/validation';

export const DeviceForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DeviceCreate>({
    resolver: zodResolver(DeviceCreateSchema),
  });

  const onSubmit = async (data: DeviceCreate) => {
    try {
      // Data is already validated by Zod
      await apiClient.devices.createDevice({ device: data });
    } catch (error) {
      console.error('Failed to create device:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        {...register('name')}
        placeholder="Device Name"
      />
      {errors.name && (
        <span className="error">{errors.name.message}</span>
      )}

      <select {...register('type')}>
        <option value="tv">TV</option>
        <option value="monitor">Monitor</option>
        <option value="tablet">Tablet</option>
      </select>
      {errors.type && (
        <span className="error">{errors.type.message}</span>
      )}

      <button type="submit">Create Device</button>
    </form>
  );
};
```

### 6.3 Centralized Error Handling

#### 6.3.1 Backend Error Handler
```python
# app/core/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Optional
import traceback
import uuid

class ApiException(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[dict] = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.trace_id = str(uuid.uuid4())

class NotFoundException(ApiException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource} not found",
            details={"resource": resource, "id": id}
        )

class ValidationException(ApiException):
    def __init__(self, errors: dict):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            details={"errors": errors}
        )

class ConflictException(ApiException):
    def __init__(self, message: str, details: dict):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            message=message,
            details=details
        )

async def api_exception_handler(request: Request, exc: ApiException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "trace_id": exc.trace_id
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    trace_id = str(uuid.uuid4())

    # Log the error
    logger.error(f"Unhandled exception {trace_id}: {str(exc)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "trace_id": trace_id
            }
        }
    )
```

#### 6.3.2 Frontend Error Handler
```typescript
// utils/error-handler.ts
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public errorCode: string,
    public details?: Record<string, any>,
    public traceId?: string
  ) {
    super(`API Error: ${errorCode}`);
    this.name = 'ApiError';
  }
}

export class ErrorHandler {
  static handle(error: unknown): ApiError {
    if (error instanceof ApiError) {
      return error;
    }

    if (error instanceof Response) {
      return new ApiError(
        error.status,
        error.statusText,
        { url: error.url }
      );
    }

    if (error instanceof Error) {
      return new ApiError(
        500,
        'CLIENT_ERROR',
        { message: error.message }
      );
    }

    return new ApiError(
      500,
      'UNKNOWN_ERROR',
      { error: String(error) }
    );
  }

  static async handleResponse(response: Response): Promise<any> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      throw new ApiError(
        response.status,
        errorData.error?.code || 'API_ERROR',
        errorData.error?.details,
        errorData.error?.trace_id
      );
    }

    return response.json();
  }

  static notify(error: ApiError) {
    // Display user-friendly error message
    const message = this.getUserMessage(error);

    // Use toast notification system
    toast.error(message, {
      duration: 5000,
      position: 'top-right',
    });

    // Log to monitoring service
    if (window.errorReporter) {
      window.errorReporter.log(error);
    }
  }

  static getUserMessage(error: ApiError): string {
    const messages: Record<string, string> = {
      'RESOURCE_NOT_FOUND': 'The requested resource was not found',
      'VALIDATION_ERROR': 'Please check your input and try again',
      'UNAUTHORIZED': 'Please login to continue',
      'FORBIDDEN': 'You do not have permission to perform this action',
      'RATE_LIMIT_EXCEEDED': 'Too many requests, please try again later',
      'SERVICE_UNAVAILABLE': 'Service is temporarily unavailable',
    };

    return messages[error.errorCode] || 'An error occurred, please try again';
  }
}
```

---

## 7. Migration Strategy

### 7.1 Phased Implementation Approach

#### 7.1.1 Phase Overview
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Phase 1   │ →  │   Phase 2   │ →  │   Phase 3   │ →  │   Phase 4   │
│ Foundation  │    │   Backend   │    │  Frontend   │    │ Deployment  │
│  (2 weeks)  │    │  (3 weeks)  │    │  (3 weeks)  │    │  (1 week)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 7.2 Phase 1: Foundation (Weeks 1-2)

#### 7.2.1 Tasks
- [ ] Create OpenAPI 3.1 specification for existing API
- [ ] Set up code generation pipeline
- [ ] Establish naming conventions document
- [ ] Create validation schemas (Pydantic & Zod)
- [ ] Set up error handling framework

#### 7.2.2 Deliverables
- Complete OpenAPI specification
- Generated TypeScript client
- Validation library setup
- Error handling utilities

### 7.3 Phase 2: Backend Standardization (Weeks 3-5)

#### 7.3.1 Tasks
- [ ] Refactor API endpoints to follow REST standards
- [ ] Implement versioned routes (/api/v1/)
- [ ] Standardize response formats
- [ ] Add comprehensive validation
- [ ] Implement service layer pattern
- [ ] Create repository layer

#### 7.3.2 Migration Steps
```python
# Step 1: Create new versioned endpoints alongside existing ones
app.include_router(legacy_router, prefix="/api")  # Keep existing
app.include_router(v1_router, prefix="/api/v1")   # Add new

# Step 2: Add deprecation headers to legacy endpoints
@router.get("/api/devices")
async def legacy_list_devices(response: Response):
    response.headers["X-API-Deprecation-Date"] = "2025-12-01"
    response.headers["X-API-Deprecation-Info"] = "Use /api/v1/devices"
    # ... existing logic

# Step 3: Implement forwarding from legacy to new
@router.get("/api/devices")
async def legacy_list_devices():
    # Forward to new endpoint
    return RedirectResponse(url="/api/v1/devices", status_code=301)
```

### 7.4 Phase 3: Frontend Integration (Weeks 6-8)

#### 7.4.1 Tasks
- [ ] Replace direct API calls with generated client
- [ ] Implement service layer in Web Admin
- [ ] Add Zod validation to all forms
- [ ] Update Viewer API client
- [ ] Implement error handling

#### 7.4.2 Migration Steps
```typescript
// Step 1: Create adapter for existing API calls
class ApiAdapter {
  // Old method (to be deprecated)
  async getDevices() {
    return api.get('/api/devices');
  }

  // New method using generated client
  async getDevicesV1() {
    return apiClient.devices.listDevices();
  }
}

// Step 2: Gradually replace calls
// Before:
const devices = await api.get('/api/devices');

// After:
const devices = await apiClient.devices.listDevices();

// Step 3: Remove adapter once migration complete
```

### 7.5 Phase 4: Deployment & Monitoring (Week 9)

#### 7.5.1 Tasks
- [ ] Deploy v1 API to production
- [ ] Set up API versioning in nginx/proxy
- [ ] Configure monitoring and alerting
- [ ] Update documentation
- [ ] Team training

#### 7.5.2 Deployment Configuration
```nginx
# nginx.conf - API versioning setup
location /api/v1/ {
    proxy_pass http://backend:8001/api/v1/;
    proxy_set_header X-API-Version "1.0.0";
}

location /api/ {
    # Legacy API with deprecation header
    proxy_pass http://backend:8001/api/;
    add_header X-API-Deprecation-Date "2025-12-01";
    add_header X-API-Deprecation-Info "Please migrate to /api/v1/";
}
```

### 7.6 Backward Compatibility Strategy

#### 7.6.1 Dual Route Support
```python
# Support both old and new endpoints during transition
@router.post("/api/devices/tv")  # Legacy
@router.post("/api/v1/devices")  # New standard
async def create_device(device: DeviceCreate):
    return device_service.create_device(device)
```

#### 7.6.2 Response Format Adapter
```python
class ResponseAdapter:
    @staticmethod
    def adapt_response(data: any, version: str = "1.0"):
        if version == "legacy":
            # Old format
            return {"status": "success", "data": data}
        else:
            # New standard format
            return {
                "data": data,
                "meta": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": version
                }
            }
```

---

## 8. Implementation Examples

### 8.1 Before and After Comparison

#### 8.1.1 Endpoint Naming
**Before:**
```javascript
// Inconsistent naming
POST   /api/devices/tv           // Create TV device
POST   /api/content/upload       // Upload content
POST   /api/tags                 // Create tag
POST   /api/content/{id}/assign  // Assign content
DELETE /api/tags/assign          // Unassign tag
```

**After:**
```javascript
// Consistent RESTful naming
POST   /api/v1/devices                          // Create any device
POST   /api/v1/contents                         // Create content
POST   /api/v1/tags                            // Create tag
POST   /api/v1/devices/{id}/contents           // Assign content to device
DELETE /api/v1/devices/{id}/contents/{content_id} // Unassign content
```

#### 8.1.2 Response Format
**Before:**
```json
// Inconsistent formats
{
  "status": "success",
  "data": {...}
}

// or
{
  "message": "Created",
  "id": 123
}

// or just
{...}
```

**After:**
```json
// Standardized format
{
  "data": {
    "id": 123,
    "name": "Device 1",
    "type": "tv"
  },
  "meta": {
    "timestamp": "2025-10-27T12:00:00Z",
    "version": "1.0.0"
  }
}
```

### 8.2 Complete CRUD Example

#### 8.2.1 Backend Implementation
```python
# app/api/v1/devices.py
from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse
)
from app.services.device_service import DeviceService
from app.core.deps import get_current_user

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("/", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    type: Optional[str] = None,
    service: DeviceService = Depends()
):
    """List all devices with pagination and filtering"""
    devices, total = await service.list_devices(
        page=page,
        limit=limit,
        filters={"status": status, "type": type}
    )

    return DeviceListResponse(
        data=devices,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    )

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    service: DeviceService = Depends()
):
    """Get specific device by ID"""
    device = await service.get_device(device_id)
    return DeviceResponse(data=device)

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    service: DeviceService = Depends(),
    current_user = Depends(get_current_user)
):
    """Create new device"""
    created = await service.create_device(device, current_user.id)
    return DeviceResponse(data=created)

@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device: DeviceUpdate,
    service: DeviceService = Depends()
):
    """Partial update device"""
    updated = await service.update_device(device_id, device)
    return DeviceResponse(data=updated)

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    service: DeviceService = Depends()
):
    """Delete device"""
    await service.delete_device(device_id)
```

#### 8.2.2 Frontend Implementation
```typescript
// api/services/DeviceService.ts
import { apiClient } from '../client';
import {
  Device, DeviceCreate, DeviceUpdate, DeviceListParams
} from '../../types/api';
import { DeviceSchema, DeviceListSchema } from '../../utils/validation';

export class DeviceService {
  async listDevices(params?: DeviceListParams): Promise<Device[]> {
    const response = await apiClient.devices.listDevices(params);

    // Validate response
    const validated = DeviceListSchema.parse(response);
    return validated.data;
  }

  async getDevice(id: number): Promise<Device> {
    const response = await apiClient.devices.getDevice({ deviceId: id });

    // Validate response
    const validated = DeviceSchema.parse(response.data);
    return validated;
  }

  async createDevice(device: DeviceCreate): Promise<Device> {
    const response = await apiClient.devices.createDevice({
      device
    });

    // Validate response
    const validated = DeviceSchema.parse(response.data);
    return validated;
  }

  async updateDevice(id: number, device: DeviceUpdate): Promise<Device> {
    const response = await apiClient.devices.updateDevice({
      deviceId: id,
      device
    });

    // Validate response
    const validated = DeviceSchema.parse(response.data);
    return validated;
  }

  async deleteDevice(id: number): Promise<void> {
    await apiClient.devices.deleteDevice({ deviceId: id });
  }
}

// React component using the service
import { useDeviceService } from '../hooks/useDeviceService';

export const DeviceList: React.FC = () => {
  const deviceService = useDeviceService();
  const [devices, setDevices] = useState<Device[]>([]);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      const data = await deviceService.listDevices({
        page: 1,
        limit: 20,
        status: 'active'
      });
      setDevices(data);
    } catch (error) {
      ErrorHandler.notify(error);
    }
  };

  const handleCreate = async (device: DeviceCreate) => {
    try {
      const created = await deviceService.createDevice(device);
      setDevices([...devices, created]);
      toast.success('Device created successfully');
    } catch (error) {
      ErrorHandler.notify(error);
    }
  };

  return (
    <div>
      {devices.map(device => (
        <DeviceCard key={device.id} device={device} />
      ))}
    </div>
  );
};
```

### 8.3 Database Migration Example

#### 8.3.1 Table Rename Migration
```sql
-- Migration: 008_standardize_table_names.sql

-- Step 1: Rename tables to follow plural convention
ALTER TABLE content RENAME TO contents;
ALTER TABLE device_tag RENAME TO device_tags;
ALTER TABLE playlist_content RENAME TO playlist_contents;

-- Step 2: Update foreign key constraints
ALTER TABLE content_assignments
    DROP CONSTRAINT fk_content_assignment_content_id,
    ADD CONSTRAINT fk_content_assignments_content_id_contents
    FOREIGN KEY (content_id) REFERENCES contents(id);

-- Step 3: Update indexes
DROP INDEX idx_content_type;
CREATE INDEX idx_contents_type ON contents(content_type);

-- Step 4: Create migration tracking
INSERT INTO schema_migrations (version, applied_at)
VALUES ('008_standardize_table_names', NOW());
```

---

## 9. Testing Strategy

### 9.1 API Contract Testing

#### 9.1.1 Backend Contract Tests
```python
# tests/test_api_contracts.py
import pytest
from fastapi.testclient import TestClient
from jsonschema import validate
import yaml

class TestApiContracts:
    @pytest.fixture
    def openapi_spec(self):
        with open('api-spec/openapi.yaml', 'r') as f:
            return yaml.safe_load(f)

    def test_device_list_response_contract(self, client: TestClient, openapi_spec):
        response = client.get("/api/v1/devices")
        assert response.status_code == 200

        # Get schema from OpenAPI spec
        schema = openapi_spec['components']['schemas']['DeviceListResponse']

        # Validate response matches schema
        validate(instance=response.json(), schema=schema)

    def test_device_create_request_contract(self, client: TestClient, openapi_spec):
        device_data = {
            "name": "Test Device",
            "type": "tv",
            "location": "Test Location"
        }

        # Get schema from OpenAPI spec
        schema = openapi_spec['components']['schemas']['DeviceCreate']

        # Validate request data matches schema
        validate(instance=device_data, schema=schema)

        response = client.post("/api/v1/devices", json=device_data)
        assert response.status_code == 201
```

#### 9.1.2 Frontend Contract Tests
```typescript
// tests/api.contract.test.ts
import { describe, it, expect } from 'vitest';
import { z } from 'zod';
import { DeviceSchema, DeviceListSchema } from '../src/utils/validation';
import openApiSpec from '../api-spec/openapi.json';

describe('API Contract Tests', () => {
  it('should validate device schema matches OpenAPI spec', () => {
    const openApiDeviceSchema = openApiSpec.components.schemas.Device;

    // Test data
    const device = {
      id: 1,
      name: 'Test Device',
      type: 'tv',
      status: 'active',
      location: null,
      last_seen: '2025-10-27T12:00:00Z',
      created_at: '2025-10-27T12:00:00Z',
    };

    // Validate with Zod schema
    const result = DeviceSchema.safeParse(device);
    expect(result.success).toBe(true);

    // Ensure all required fields from OpenAPI are present
    const requiredFields = openApiDeviceSchema.required || [];
    requiredFields.forEach(field => {
      expect(device).toHaveProperty(field);
    });
  });
});
```

### 9.2 Integration Testing

#### 9.2.1 End-to-End API Tests
```python
# tests/integration/test_device_flow.py
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

class TestDeviceFlow:
    def test_complete_device_lifecycle(self, client: TestClient, db: Session):
        # Create device
        create_data = {
            "name": "Integration Test Device",
            "type": "monitor",
            "location": "Test Lab"
        }

        create_response = client.post("/api/v1/devices", json=create_data)
        assert create_response.status_code == 201
        device_id = create_response.json()["data"]["id"]

        # List devices
        list_response = client.get("/api/v1/devices")
        assert list_response.status_code == 200
        devices = list_response.json()["data"]
        assert any(d["id"] == device_id for d in devices)

        # Get specific device
        get_response = client.get(f"/api/v1/devices/{device_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["name"] == create_data["name"]

        # Update device
        update_data = {"status": "inactive"}
        update_response = client.patch(
            f"/api/v1/devices/{device_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["status"] == "inactive"

        # Delete device
        delete_response = client.delete(f"/api/v1/devices/{device_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_deleted = client.get(f"/api/v1/devices/{device_id}")
        assert get_deleted.status_code == 404
```

### 9.3 Performance Testing

#### 9.3.1 Load Testing Script
```python
# tests/performance/load_test.py
import asyncio
import aiohttp
import time
from typing import List

class ApiLoadTester:
    def __init__(self, base_url: str, concurrent_users: int = 10):
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.results: List[dict] = []

    async def make_request(self, session: aiohttp.ClientSession, endpoint: str):
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                await response.text()
                duration = time.time() - start_time
                self.results.append({
                    "endpoint": endpoint,
                    "status": response.status,
                    "duration": duration
                })
        except Exception as e:
            self.results.append({
                "endpoint": endpoint,
                "error": str(e),
                "duration": time.time() - start_time
            })

    async def run_test(self, endpoint: str, requests_per_user: int = 100):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(self.concurrent_users):
                for _ in range(requests_per_user):
                    tasks.append(self.make_request(session, endpoint))

            await asyncio.gather(*tasks)

    def analyze_results(self):
        successful = [r for r in self.results if "error" not in r]
        failed = [r for r in self.results if "error" in r]

        if successful:
            durations = [r["duration"] for r in successful]
            return {
                "total_requests": len(self.results),
                "successful": len(successful),
                "failed": len(failed),
                "avg_response_time": sum(durations) / len(durations),
                "min_response_time": min(durations),
                "max_response_time": max(durations),
                "p95_response_time": sorted(durations)[int(len(durations) * 0.95)]
            }
        return {"error": "No successful requests"}

# Usage
async def main():
    tester = ApiLoadTester("http://192.168.5.12:8001", concurrent_users=20)
    await tester.run_test("/api/v1/devices", requests_per_user=50)
    results = tester.analyze_results()
    print(f"Performance Results: {results}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 10. Performance & Monitoring

### 10.1 API Performance Optimization

#### 10.1.1 Response Caching
```python
# app/core/cache.py
from functools import wraps
import hashlib
import json
from typing import Optional
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_response(expire: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hashlib.md5(
                json.dumps({'args': args, 'kwargs': kwargs},
                          sort_keys=True, default=str).encode()
            ).hexdigest()}"

            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            redis_client.setex(
                cache_key,
                expire,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

# Usage
@router.get("/devices")
@cache_response(expire=60)  # Cache for 60 seconds
async def list_devices():
    # ... implementation
```

#### 10.1.2 Database Query Optimization
```python
# app/repositories/device_repo.py
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload

class DeviceRepository:
    async def get_devices_optimized(self, page: int, limit: int):
        # Use eager loading for relationships
        stmt = (
            select(Device)
            .options(
                selectinload(Device.tags),
                selectinload(Device.contents),
                joinedload(Device.location)
            )
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        devices = result.scalars().unique().all()

        # Get total count in single query
        count_stmt = select(func.count()).select_from(Device)
        total = await self.db.scalar(count_stmt)

        return devices, total
```

### 10.2 Monitoring Setup

#### 10.2.1 API Metrics Collection
```python
# app/core/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'api_active_connections',
    'Active API connections'
)

def track_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            status = "success"
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time

            # Record metrics
            request_count.labels(
                method=kwargs.get('request').method,
                endpoint=kwargs.get('request').url.path,
                status=status
            ).inc()

            request_duration.labels(
                method=kwargs.get('request').method,
                endpoint=kwargs.get('request').url.path
            ).observe(duration)

    return wrapper
```

#### 10.2.2 Logging Configuration
```python
# app/core/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    # JSON formatter for structured logging
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logHandler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(logHandler)

    # SQL query logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # API request logging
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)

    return root_logger

# Middleware for request logging
from fastapi import Request
import uuid

async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Add request ID to context
    request.state.request_id = request_id

    # Log request
    logger.info("API Request", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "client": request.client.host if request.client else None
    })

    # Process request
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Log response
    logger.info("API Response", extra={
        "request_id": request_id,
        "status_code": response.status_code,
        "duration": duration
    })

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response
```

---

## 11. Security Considerations

### 11.1 Authentication & Authorization

#### 11.1.1 JWT Token Implementation
```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class JWTHandler:
    SECRET_KEY = "your-secret-key"  # Use environment variable
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @classmethod
    def create_access_token(cls, subject: str) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": subject,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            return payload.get("sub")
        except JWTError:
            return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    user_id = JWTHandler.verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id
```

### 11.2 Input Sanitization

#### 11.2.1 SQL Injection Prevention
```python
# app/repositories/base_repo.py
from sqlalchemy import text
from typing import Any, Dict

class BaseRepository:
    def safe_query(self, query: str, params: Dict[str, Any]):
        """Execute parameterized query to prevent SQL injection"""
        # Use parameterized queries
        stmt = text(query)
        result = self.db.execute(stmt, params)
        return result.fetchall()

    # Never do this:
    # query = f"SELECT * FROM users WHERE name = '{user_input}'"

    # Always do this:
    def get_user_by_name(self, name: str):
        stmt = text("SELECT * FROM users WHERE name = :name")
        return self.db.execute(stmt, {"name": name}).fetchone()
```

### 11.3 Rate Limiting

#### 11.3.1 Rate Limiter Implementation
```python
# app/core/rate_limiter.py
from fastapi import Request, HTTPException, status
from typing import Optional
import time
import redis

class RateLimiter:
    def __init__(
        self,
        redis_client: redis.Redis,
        requests: int = 100,
        window: int = 60
    ):
        self.redis = redis_client
        self.requests = requests
        self.window = window

    async def check_rate_limit(self, request: Request) -> bool:
        # Get client identifier
        client_id = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_id}"

        try:
            pipeline = self.redis.pipeline()
            now = time.time()
            pipeline.zremrangebyscore(key, 0, now - self.window)
            pipeline.zadd(key, {str(now): now})
            pipeline.zcount(key, now - self.window, now)
            pipeline.expire(key, self.window)
            results = pipeline.execute()

            request_count = results[2]

            if request_count > self.requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            return True
        except redis.RedisError:
            # If Redis is down, allow the request
            return True

# Usage as dependency
rate_limiter = RateLimiter(redis_client)

@router.get("/devices")
async def list_devices(
    rate_limited: bool = Depends(rate_limiter.check_rate_limit)
):
    # ... implementation
```

---

## 12. Implementation Timeline

### 12.1 Gantt Chart Overview

```
Week  1  2  3  4  5  6  7  8  9
─────────────────────────────────
Phase 1: Foundation
      ████████

Phase 2: Backend
         ██████████████

Phase 3: Frontend
                  ██████████████

Phase 4: Deploy
                           ████

Testing & QA
      ████████████████████████████

Documentation
      ████████████████████████████
```

### 12.2 Detailed Timeline

#### Week 1-2: Foundation Phase
- **Week 1:**
  - Day 1-2: Create OpenAPI specification
  - Day 3-4: Set up code generation pipeline
  - Day 5: Establish conventions document

- **Week 2:**
  - Day 1-2: Create Pydantic schemas
  - Day 3-4: Create Zod schemas
  - Day 5: Set up error handling

#### Week 3-5: Backend Implementation
- **Week 3:**
  - Day 1-2: Refactor device endpoints
  - Day 3-4: Refactor content endpoints
  - Day 5: Implement versioning

- **Week 4:**
  - Day 1-2: Standardize responses
  - Day 3-4: Add validation layer
  - Day 5: Implement service pattern

- **Week 5:**
  - Day 1-2: Create repository layer
  - Day 3-4: Add caching
  - Day 5: Performance testing

#### Week 6-8: Frontend Integration
- **Week 6:**
  - Day 1-2: Replace Web Admin API calls
  - Day 3-4: Implement service layer
  - Day 5: Add Zod validation

- **Week 7:**
  - Day 1-2: Update Viewer API client
  - Day 3-4: Implement error handling
  - Day 5: Integration testing

- **Week 8:**
  - Day 1-2: Final testing
  - Day 3-4: Bug fixes
  - Day 5: Performance optimization

#### Week 9: Deployment
- **Day 1:** Deploy to staging
- **Day 2:** Staging tests
- **Day 3:** Deploy to production
- **Day 4:** Monitor and verify
- **Day 5:** Team training

### 12.3 Success Criteria Checklist

#### Phase 1 Completion
- [ ] OpenAPI specification covers 100% of endpoints
- [ ] Code generation pipeline functional
- [ ] Validation schemas created
- [ ] Error handling framework ready

#### Phase 2 Completion
- [ ] All endpoints follow REST standards
- [ ] Versioned routes implemented
- [ ] Response formats standardized
- [ ] Service/repository pattern implemented

#### Phase 3 Completion
- [ ] Generated client integrated
- [ ] All forms use Zod validation
- [ ] Error handling implemented
- [ ] Viewer uses new API client

#### Phase 4 Completion
- [ ] Production deployment successful
- [ ] Monitoring active
- [ ] Documentation complete
- [ ] Team trained

---

## 13. Appendices

### Appendix A: Naming Convention Reference

#### A.1 API Endpoints
```
Resource Collection:    /devices (plural)
Single Resource:       /devices/{id}
Sub-resource:         /devices/{id}/contents
Action (rare):        /devices/{id}/activate
```

#### A.2 Database Tables
```
Tables:               devices, contents (plural)
Columns:              device_name, created_at (snake_case)
Junction Tables:      device_content (singular)
Indexes:              idx_devices_status
Foreign Keys:         fk_device_content_device_id_devices
```

#### A.3 Code Conventions
```python
# Python (snake_case)
def get_device_by_id(device_id: int) -> Device:
    pass

class DeviceService:
    pass
```

```typescript
// TypeScript (camelCase)
function getDeviceById(deviceId: number): Device {
    // ...
}

class DeviceService {
    // ...
}
```

### Appendix B: Error Code Reference

| Code | HTTP Status | Description |
|------|------------|-------------|
| RESOURCE_NOT_FOUND | 404 | Resource doesn't exist |
| VALIDATION_ERROR | 422 | Input validation failed |
| UNAUTHORIZED | 401 | Missing/invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| RESOURCE_CONFLICT | 409 | Conflicting resource state |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Unexpected server error |

### Appendix C: Migration Scripts

#### C.1 Database Migration Template
```sql
-- Migration: XXX_description.sql
-- Author: [Name]
-- Date: [YYYY-MM-DD]
-- Description: [What this migration does]

BEGIN;

-- Add your changes here

-- Update migration tracking
INSERT INTO schema_migrations (version, applied_at)
VALUES ('XXX_description', NOW());

COMMIT;

-- Rollback script (in separate file)
-- BEGIN;
-- -- Rollback changes
-- DELETE FROM schema_migrations WHERE version = 'XXX_description';
-- COMMIT;
```

### Appendix D: Tools & Libraries

#### Backend
- **FastAPI**: 0.104.1
- **Pydantic**: 2.4.2
- **SQLAlchemy**: 2.0.23
- **Alembic**: 1.12.1
- **Redis**: 5.0.1
- **Prometheus Client**: 0.19.0

#### Frontend
- **React**: 18.2.0
- **TypeScript**: 5.2.2
- **Zod**: 3.22.4
- **React Query**: 5.8.4
- **OpenAPI Generator**: 7.1.0

#### Development
- **Pytest**: 7.4.3
- **Vitest**: 1.0.4
- **Docker**: 24.0.7
- **nginx**: 1.25.3

### Appendix E: References

1. **REST API Design Best Practices**
   - [RESTful Web API Design](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design)
   - [Google API Design Guide](https://cloud.google.com/apis/design)

2. **OpenAPI Specification**
   - [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
   - [OpenAPI Generator](https://openapi-generator.tech/)

3. **Validation Libraries**
   - [Pydantic Documentation](https://docs.pydantic.dev/)
   - [Zod Documentation](https://zod.dev/)

4. **Performance**
   - [FastAPI Performance](https://fastapi.tiangolo.com/benchmarks/)
   - [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-27 | System Architect | Initial document creation |

---

## Approval & Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | | | |
| Backend Developer | | | |
| Frontend Developer | | | |
| QA Lead | | | |
| Project Manager | | | |

---

**End of Document**

*This document serves as the definitive guide for API standardization and architecture improvement for the Smart TV Digital Signage system. For questions or clarifications, please contact the system architecture team.*