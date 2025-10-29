# Digital Signage System - Microservices Architecture Design

## Executive Summary

This document outlines the transformation of the current monolithic digital signage system into a scalable microservices architecture designed to support 1,000-10,000 devices with clear service boundaries, optimal performance, and maintainable codebase.

## Current System Analysis

### Pain Points in Monolithic Architecture
- **Tight Coupling**: All functionalities (auth, content, devices, playlists) in single FastAPI service
- **Scalability Bottleneck**: Cannot scale individual components independently
- **Long-Running Tasks**: Video transcoding (10-60 min) blocks resources
- **Database Contention**: Single PostgreSQL instance for all operations
- **Deployment Risk**: Any change requires full system deployment
- **Testing Complexity**: Integration testing requires entire system

## Proposed Microservices Architecture

### System Architecture Diagram (Text-Based)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Load Balancer / CDN                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API Gateway (Kong/Traefik)                        │
│                    • Rate Limiting • Auth • Routing • CORS                   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │   Auth   │    │ Device   │    │ Content  │    │ Playlist │
    │ Service  │    │ Service  │    │ Service  │    │ Service  │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Auth    │    │  Device  │    │ Content  │    │ Playlist │
    │    DB    │    │    DB    │    │    DB    │    │    DB    │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Async Communication Layer                            │
│                    RabbitMQ / Kafka Event Bus                               │
└─────────────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │Transcode │    │Websocket │    │Analytics │    │Notifica- │
    │ Service  │    │ Service  │    │ Service  │    │   tion   │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘
          │                │                │                │
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Celery  │    │  Redis   │    │ TimeSer. │    │  Redis   │
    │  Redis   │    │  PubSub  │    │    DB    │    │  Queue   │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         External Services Layer                              │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────────┤
│   Anthias    │     S3/      │   Elastic   │   Grafana/   │   Sentry/     │
│   Storage    │   MinIO      │   Search    │  Prometheus  │   Logging     │
└──────────────┴──────────────┴──────────────┴──────────────┴────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────────┤
│  Web Admin   │   Viewer     │  Mobile App  │   API SDK    │  WebOS App    │
└──────────────┴──────────────┴──────────────┴──────────────┴────────────────┘
```

## Service Breakdown & Responsibilities

### 1. Authentication Service
**Responsibilities:**
- User authentication (login, logout, refresh tokens)
- User management (CRUD operations)
- Role-based access control (RBAC)
- JWT token generation and validation
- Session management
- Password reset and account recovery
- OAuth2/SSO integration

**Technology Stack:**
- FastAPI with async support
- PostgreSQL (dedicated auth DB)
- Redis for session cache
- bcrypt for password hashing

**API Endpoints:**
```
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
GET    /auth/verify
POST   /auth/register
POST   /auth/password/reset
GET    /auth/users
PUT    /auth/users/{id}
DELETE /auth/users/{id}
```

### 2. Device Management Service
**Responsibilities:**
- Device registration and activation (6-digit code)
- Device status tracking (online/offline)
- Device configuration management
- Heartbeat processing
- Device grouping and tagging
- Command execution (restart, update, etc.)
- Device telemetry collection

**Technology Stack:**
- FastAPI with WebSocket support
- PostgreSQL (dedicated device DB)
- Redis for real-time status cache
- Time-series DB for telemetry

**API Endpoints:**
```
POST   /devices/register
POST   /devices/activate
GET    /devices
GET    /devices/{id}
PUT    /devices/{id}
DELETE /devices/{id}
POST   /devices/{id}/command
GET    /devices/{id}/status
POST   /devices/{id}/heartbeat
GET    /devices/{id}/logs
```

### 3. Content Management Service
**Responsibilities:**
- Content CRUD operations
- Metadata management
- Content versioning
- Content categorization and tagging
- Thumbnail generation
- Content validation
- Integration with storage service (Anthias)

**Technology Stack:**
- FastAPI
- PostgreSQL (dedicated content DB)
- Redis for caching
- MinIO/S3 for object storage

**API Endpoints:**
```
POST   /content/upload
GET    /content
GET    /content/{id}
PUT    /content/{id}
DELETE /content/{id}
GET    /content/{id}/metadata
POST   /content/{id}/thumbnail
GET    /content/{id}/versions
POST   /content/bulk/update
GET    /content/search
```

### 4. Playlist Management Service
**Responsibilities:**
- Playlist CRUD operations
- Playlist scheduling
- Playlist assignment to devices/groups
- Playlist validation
- Playlist versioning
- Playlist preview generation

**Technology Stack:**
- FastAPI
- PostgreSQL (dedicated playlist DB)
- Redis for caching active playlists

**API Endpoints:**
```
POST   /playlists
GET    /playlists
GET    /playlists/{id}
PUT    /playlists/{id}
DELETE /playlists/{id}
POST   /playlists/{id}/assign
GET    /playlists/{id}/devices
POST   /playlists/{id}/schedule
GET    /playlists/{id}/preview
POST   /playlists/{id}/duplicate
```

### 5. Transcoding Service (Async)
**Responsibilities:**
- Video transcoding to multiple resolutions
- Format conversion
- Thumbnail extraction
- Video optimization
- Progress tracking
- Queue management

**Technology Stack:**
- Python with Celery
- FFmpeg for transcoding
- Redis as message broker
- PostgreSQL for job tracking
- S3/MinIO for storage

**Processing Flow:**
```
1. Receive transcoding job via message queue
2. Download original from storage
3. Process with FFmpeg (multiple resolutions)
4. Generate thumbnails
5. Upload processed files
6. Update content metadata
7. Publish completion event
```

### 6. WebSocket Service
**Responsibilities:**
- Real-time device status updates
- Live content updates
- Command delivery to devices
- Heartbeat management
- Connection pooling
- Message broadcasting

**Technology Stack:**
- FastAPI with WebSocket
- Redis Pub/Sub for message distribution
- Connection pool management

**WebSocket Channels:**
```
/ws/devices/{device_id}     - Device-specific updates
/ws/dashboard               - Dashboard real-time stats
/ws/admin                   - Admin notifications
/ws/broadcast               - System-wide broadcasts
```

### 7. Analytics Service
**Responsibilities:**
- Device usage analytics
- Content performance metrics
- System health metrics
- Report generation
- Data aggregation
- Trend analysis

**Technology Stack:**
- FastAPI
- TimescaleDB for time-series data
- Redis for real-time counters
- Elasticsearch for log analysis

**API Endpoints:**
```
GET    /analytics/devices/usage
GET    /analytics/content/performance
GET    /analytics/system/health
GET    /analytics/reports/generate
GET    /analytics/dashboard/stats
```

### 8. Notification Service
**Responsibilities:**
- Email notifications
- Push notifications
- SMS alerts
- In-app notifications
- Notification templates
- Delivery tracking

**Technology Stack:**
- FastAPI
- Redis for queue
- PostgreSQL for templates
- SMTP/SendGrid for email
- FCM for push notifications

## Inter-Service Communication Patterns

### Synchronous Communication (REST/gRPC)
Used for real-time, request-response operations:

```yaml
Auth Service → All Services:
  - Token validation
  - Permission checks

Content Service → Storage Service:
  - File upload/download
  - Metadata retrieval

Playlist Service → Content Service:
  - Content validation
  - Metadata fetching

Device Service → Playlist Service:
  - Active playlist retrieval
  - Schedule checking
```

### Asynchronous Communication (Message Queue)
Used for decoupled, event-driven operations:

```yaml
Event Bus (RabbitMQ/Kafka):

Content Events:
  - content.uploaded
  - content.transcoded
  - content.deleted
  - content.updated

Device Events:
  - device.registered
  - device.activated
  - device.online
  - device.offline
  - device.command.executed

Playlist Events:
  - playlist.created
  - playlist.assigned
  - playlist.scheduled
  - playlist.updated

System Events:
  - system.alert
  - system.maintenance
  - system.update
```

### Message Flow Examples

#### Video Upload Flow:
```
1. Client → API Gateway → Content Service: Upload video
2. Content Service → Storage: Store original file
3. Content Service → Event Bus: Publish 'content.uploaded'
4. Transcoding Service: Subscribe to 'content.uploaded'
5. Transcoding Service → Storage: Retrieve and process
6. Transcoding Service → Event Bus: Publish 'content.transcoded'
7. Content Service: Update metadata with transcoded versions
8. Notification Service: Notify user of completion
```

#### Device Activation Flow:
```
1. Device → API Gateway → Device Service: Register with code
2. Device Service → Auth Service: Validate permissions
3. Device Service → Event Bus: Publish 'device.registered'
4. WebSocket Service: Notify admin dashboard
5. Analytics Service: Record new device
6. Device Service → Playlist Service: Get assigned playlist
7. Device Service → Device: Return activation success
```

## Database Strategy

### Database per Service Pattern

Each microservice owns its data and database:

```yaml
Authentication Service:
  Database: auth_db
  Tables:
    - users
    - roles
    - permissions
    - sessions
    - audit_log

Device Service:
  Database: device_db
  Tables:
    - devices
    - device_groups
    - device_tags
    - device_status
    - device_commands
    - heartbeats

Content Service:
  Database: content_db
  Tables:
    - content
    - content_metadata
    - content_versions
    - content_tags
    - thumbnails

Playlist Service:
  Database: playlist_db
  Tables:
    - playlists
    - playlist_items
    - playlist_schedules
    - playlist_assignments
    - playlist_versions

Analytics Service:
  Database: analytics_db (TimescaleDB)
  Tables:
    - device_metrics
    - content_metrics
    - system_metrics
    - aggregated_stats
```

### Data Consistency Patterns

#### Eventual Consistency
- Used for non-critical updates
- Event-driven synchronization
- Acceptable delay: 1-5 seconds

#### Strong Consistency
- Used for financial transactions
- User authentication
- Device commands

#### Saga Pattern for Distributed Transactions
Example: Content deletion saga
```
1. Start saga
2. Delete from Content Service
3. Delete from Storage Service
4. Update Playlist Service
5. Update Analytics Service
6. Complete saga or compensate
```

## API Gateway Design

### Kong/Traefik Configuration

```yaml
Features:
  Rate Limiting:
    - 1000 req/min per device
    - 10000 req/min per admin

  Authentication:
    - JWT validation
    - API key management
    - OAuth2 proxy

  Routing:
    - Path-based routing
    - Header-based routing
    - Load balancing

  Security:
    - CORS management
    - SSL termination
    - IP whitelisting
    - DDoS protection

  Monitoring:
    - Request logging
    - Metrics collection
    - Health checks
    - Circuit breaking
```

### API Gateway Routes

```nginx
# Authentication routes
/api/v1/auth/* → auth-service:8001

# Device management routes
/api/v1/devices/* → device-service:8002

# Content management routes
/api/v1/content/* → content-service:8003

# Playlist management routes
/api/v1/playlists/* → playlist-service:8004

# Analytics routes
/api/v1/analytics/* → analytics-service:8005

# WebSocket routes
/ws/* → websocket-service:8006
```

## Authentication & Authorization

### JWT-Based Authentication Flow

```yaml
1. Login:
   Client → API Gateway → Auth Service
   Response: Access Token (15 min) + Refresh Token (7 days)

2. Request with Token:
   Client → API Gateway (validate JWT) → Target Service

3. Service-to-Service:
   Service A → Auth Service: Validate token
   Auth Service → Service A: User permissions
   Service A → Service B: Internal API call with service token

4. Token Refresh:
   Client → Auth Service: Refresh token
   Auth Service → Client: New access token
```

### RBAC Implementation

```yaml
Roles:
  super_admin:
    - All permissions

  admin:
    - Manage devices
    - Manage content
    - Manage playlists
    - View analytics

  operator:
    - View devices
    - Upload content
    - Create playlists

  viewer:
    - View dashboards
    - View reports
```

## Scalability Considerations

### Horizontal Scaling Strategy

```yaml
Service Replicas (Kubernetes):
  auth-service: 2-5 pods
  device-service: 5-20 pods (high load)
  content-service: 3-10 pods
  playlist-service: 2-5 pods
  transcode-service: 10-50 workers
  websocket-service: 5-15 pods
  analytics-service: 3-8 pods
  notification-service: 2-5 pods
```

### Caching Strategy

```yaml
Redis Caching Layers:

  L1 - Application Cache:
    - User sessions (15 min TTL)
    - Device status (30 sec TTL)
    - Active playlists (5 min TTL)

  L2 - CDN Cache:
    - Static content
    - Thumbnails
    - Transcoded videos

  L3 - Database Query Cache:
    - Frequently accessed data
    - Aggregated statistics
    - Report data
```

### Load Balancing

```yaml
Strategies by Service:

  Stateless Services (REST APIs):
    - Round-robin
    - Least connections

  WebSocket Service:
    - Sticky sessions (IP hash)
    - Connection affinity

  Transcoding Service:
    - Queue-based distribution
    - Priority queues
```

## Deployment Architecture

### Kubernetes Deployment

```yaml
Namespaces:
  - signage-prod
  - signage-staging
  - signage-monitoring

Deployments:
  - Each microservice as deployment
  - HPA for auto-scaling
  - PDB for high availability

Services:
  - ClusterIP for internal
  - LoadBalancer for gateway

ConfigMaps & Secrets:
  - Environment configs
  - Database credentials
  - API keys

Ingress:
  - NGINX Ingress Controller
  - SSL/TLS termination
  - Path-based routing
```

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  # API Gateway
  kong:
    image: kong:latest
    ports:
      - "8000:8000"
    depends_on:
      - kong-db

  # Microservices
  auth-service:
    build: ./services/auth
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...

  device-service:
    build: ./services/device
    ports:
      - "8002:8002"
    depends_on:
      - device-db
      - redis

  # ... other services

  # Databases
  auth-db:
    image: postgres:14
    environment:
      - POSTGRES_DB=auth_db

  device-db:
    image: postgres:14
    environment:
      - POSTGRES_DB=device_db

  # Message Queue
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "15672:15672"

  # Caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Migration Strategy

### Phase 1: Strangler Fig Pattern (Months 1-2)
```
1. Deploy API Gateway
2. Route all traffic through gateway
3. Keep monolith running
4. Implement authentication service
5. Gradually route auth calls to new service
```

### Phase 2: Core Services (Months 2-4)
```
1. Extract Device Management Service
2. Extract Content Management Service
3. Implement event bus
4. Migrate WebSocket to dedicated service
```

### Phase 3: Advanced Services (Months 4-6)
```
1. Extract Playlist Service
2. Implement Transcoding Service
3. Add Analytics Service
4. Implement Notification Service
```

### Phase 4: Optimization (Months 6-7)
```
1. Implement caching layers
2. Optimize database queries
3. Add monitoring and alerting
4. Performance tuning
```

## Monitoring & Observability

### Metrics Collection

```yaml
Prometheus Metrics:
  - Request rate
  - Error rate
  - Response time (P50, P95, P99)
  - Service availability
  - Resource utilization

Custom Metrics:
  - Active devices
  - Content upload rate
  - Transcoding queue length
  - WebSocket connections
```

### Distributed Tracing

```yaml
OpenTelemetry Integration:
  - Request tracing across services
  - Performance bottleneck identification
  - Error tracking
  - Dependency mapping

Jaeger UI:
  - Visual trace analysis
  - Service dependency graph
  - Performance insights
```

### Logging Strategy

```yaml
Centralized Logging (ELK Stack):

  Log Levels:
    - ERROR: System errors, failures
    - WARN: Degraded performance, retries
    - INFO: Business events, state changes
    - DEBUG: Detailed execution flow

  Structured Logging:
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "service": "device-service",
      "trace_id": "abc123",
      "user_id": "usr_456",
      "event": "device.activated",
      "device_id": "dev_789",
      "duration_ms": 45
    }
```

## Security Considerations

### Network Security

```yaml
Network Policies:
  - Service mesh (Istio) for mTLS
  - Network segmentation
  - Ingress/egress rules
  - Pod security policies
```

### Data Security

```yaml
Encryption:
  - At rest: AES-256
  - In transit: TLS 1.3
  - Database: Transparent encryption

Secrets Management:
  - HashiCorp Vault
  - Kubernetes Secrets
  - Environment variable encryption
```

### API Security

```yaml
Security Headers:
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - X-XSS-Protection: 1; mode=block
  - Content-Security-Policy: default-src 'self'

Rate Limiting:
  - Per user: 1000 req/hour
  - Per IP: 10000 req/hour
  - Per device: 500 req/hour
```

## Trade-offs Analysis: Monolith vs Microservices

### Monolithic Architecture

**Pros:**
- ✅ Simpler deployment and operations
- ✅ Lower operational overhead
- ✅ Easier debugging and tracing
- ✅ No network latency between components
- ✅ Simpler transaction management
- ✅ Lower initial development cost
- ✅ Suitable for small teams (1-5 developers)

**Cons:**
- ❌ Cannot scale components independently
- ❌ Single point of failure
- ❌ Technology lock-in
- ❌ Difficult to maintain as codebase grows
- ❌ Longer deployment cycles
- ❌ Resource inefficiency (transcoding blocks other operations)
- ❌ Team bottlenecks (everyone works on same codebase)

**Best for:**
- Early-stage startup (< 100 devices)
- Proof of concept
- Small team with limited resources
- Rapid prototyping

### Microservices Architecture

**Pros:**
- ✅ Independent scalability (scale transcoding separately)
- ✅ Fault isolation (transcoding failure doesn't affect devices)
- ✅ Technology diversity (use best tool for each job)
- ✅ Independent deployment cycles
- ✅ Better resource utilization
- ✅ Team autonomy (teams own services)
- ✅ Easier to maintain and evolve
- ✅ Better suited for 1000-10000 devices

**Cons:**
- ❌ Increased operational complexity
- ❌ Network latency between services
- ❌ Distributed system challenges (CAP theorem)
- ❌ Complex debugging and tracing
- ❌ Higher infrastructure cost
- ❌ Requires experienced team
- ❌ Complex transaction management
- ❌ Service versioning challenges

**Best for:**
- Production system with 1000+ devices
- Need for independent scaling
- Multiple development teams
- Long-term maintainability
- Complex business requirements

## Recommendation for Your Use Case

### Why Microservices is Recommended

Given your requirements of supporting **1000-10000 devices**, the microservices architecture is strongly recommended because:

1. **Scalability Requirements:**
   - Device management needs to scale independently (10000 concurrent connections)
   - Transcoding is resource-intensive and should not block other operations
   - WebSocket connections need dedicated scaling

2. **Long-Running Operations:**
   - Video transcoding (10-60 minutes) requires isolated processing
   - Queue-based architecture prevents system blockage
   - Can scale transcoding workers based on queue depth

3. **Fault Tolerance:**
   - Transcoding failures won't affect device operations
   - Individual service failures are isolated
   - System remains partially operational during failures

4. **Performance Optimization:**
   - Each service can be optimized independently
   - Different caching strategies per service
   - Database optimization per domain

5. **Team Growth:**
   - As system grows, teams can own specific services
   - Parallel development without conflicts
   - Clear ownership and responsibilities

### Hybrid Approach (Recommended Starting Point)

Start with a **Modular Monolith** and gradually migrate to microservices:

```
Phase 1 (Months 0-3): Modular Monolith
- Keep FastAPI monolith but refactor into modules
- Separate concerns within monolith
- Implement domain boundaries
- Add message queue for transcoding

Phase 2 (Months 3-6): Extract Critical Services
- Extract Transcoding Service first (biggest pain point)
- Extract WebSocket Service (scaling requirement)
- Keep core CRUD in monolith

Phase 3 (Months 6-12): Full Microservices
- Extract remaining services based on need
- Implement full event-driven architecture
- Add advanced features (analytics, notifications)
```

## Cost-Benefit Analysis

### Development Costs

```yaml
Monolith:
  Initial Development: $50,000
  Maintenance (yearly): $30,000
  Scaling Issues: Start at 500 devices
  Total 3-year cost: $140,000

Microservices:
  Initial Development: $150,000
  Maintenance (yearly): $50,000
  Scaling: Handles 10000+ devices
  Total 3-year cost: $300,000

ROI Break-even: At 2000 devices (avoided downtime and performance issues)
```

### Operational Costs (Monthly)

```yaml
Monolith (1000 devices):
  - Single large server: $500
  - Database: $200
  - Storage: $100
  - CDN: $100
  Total: $900/month

Microservices (1000 devices):
  - Kubernetes cluster: $800
  - Multiple databases: $400
  - Message queue: $150
  - Monitoring: $200
  - Storage: $100
  - CDN: $100
  Total: $1750/month

Microservices (10000 devices):
  - Kubernetes cluster: $3000
  - Databases: $1000
  - Message queue: $500
  - Monitoring: $500
  - Storage: $1000
  - CDN: $500
  Total: $6500/month

Note: Monolith would require major re-architecture at this scale
```

## Implementation Priorities

### Critical Path (Must Have)
1. **API Gateway** - Single entry point, security, routing
2. **Authentication Service** - Security foundation
3. **Device Service** - Core business function
4. **Transcoding Service** - Biggest performance bottleneck
5. **WebSocket Service** - Real-time requirements

### Important (Should Have)
6. **Content Service** - Separate content management
7. **Playlist Service** - Business logic separation
8. **Monitoring** - Observability is crucial

### Nice to Have (Could Have)
9. **Analytics Service** - Business insights
10. **Notification Service** - User engagement

## Success Metrics

### Technical KPIs
- API response time < 200ms (P95)
- Device heartbeat processing < 100ms
- Video transcoding queue time < 5 minutes
- System uptime > 99.9%
- Zero-downtime deployments

### Business KPIs
- Support 10000 concurrent devices
- Handle 1000 video uploads/day
- Process 10000 playlist updates/day
- < 1% device disconnection rate
- < 5 second content update propagation

## Conclusion

The microservices architecture is the recommended approach for your digital signage system given the scale requirements (1000-10000 devices) and the need for handling long-running video transcoding operations. The architecture provides:

1. **Independent scalability** for each component
2. **Fault isolation** preventing cascading failures
3. **Optimal resource utilization** for transcoding
4. **Technology flexibility** per service
5. **Long-term maintainability** and evolution

Start with a modular monolith approach and gradually migrate to microservices using the Strangler Fig pattern. This reduces risk and allows learning while maintaining system stability.

The investment in microservices architecture will pay off as the system scales beyond 2000 devices, where monolithic architecture would face significant performance and maintenance challenges.

---

## Appendix A: Technology Stack Summary

| Component | Technology | Justification |
|-----------|------------|---------------|
| API Gateway | Kong/Traefik | Rate limiting, routing, security |
| Microservices | FastAPI (Python) | Async support, performance, ecosystem |
| Message Queue | RabbitMQ/Kafka | Reliability, scalability, ecosystem |
| Databases | PostgreSQL | ACID compliance, JSON support |
| Time-series DB | TimescaleDB | Device metrics, analytics |
| Cache | Redis | Performance, pub/sub, sessions |
| Search | Elasticsearch | Log analysis, full-text search |
| Container | Docker | Standardization, portability |
| Orchestration | Kubernetes | Scaling, resilience, deployment |
| Monitoring | Prometheus/Grafana | Metrics, alerting, visualization |
| Tracing | Jaeger | Distributed tracing, performance |
| Logging | ELK Stack | Centralized logging, analysis |
| Storage | MinIO/S3 | Object storage, CDN integration |

## Appendix B: Service Communication Matrix

| From Service | To Service | Protocol | Pattern | Purpose |
|--------------|------------|----------|---------|---------|
| All Services | Auth Service | REST | Sync | Token validation |
| Device Service | Playlist Service | REST | Sync | Get active playlist |
| Content Service | Transcode Service | Event | Async | Trigger transcoding |
| Transcode Service | Storage | REST | Sync | File operations |
| All Services | Analytics Service | Event | Async | Metrics collection |
| WebSocket Service | All Services | Event | Async | Real-time updates |
| API Gateway | All Services | REST/gRPC | Sync | Request routing |

## Appendix C: Database Schemas

### Device Service Database

```sql
-- devices table
CREATE TABLE devices (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    activation_code VARCHAR(6),
    status VARCHAR(50),
    last_seen TIMESTAMP,
    ip_address INET,
    location JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- device_heartbeats table (partitioned by day)
CREATE TABLE device_heartbeats (
    device_id UUID REFERENCES devices(id),
    timestamp TIMESTAMP NOT NULL,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    network_status JSONB,
    PRIMARY KEY (device_id, timestamp)
) PARTITION BY RANGE (timestamp);
```

### Content Service Database

```sql
-- content table
CREATE TABLE content (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    original_url TEXT,
    transcoded_urls JSONB,
    metadata JSONB,
    tags TEXT[],
    duration INTEGER,
    file_size BIGINT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- content_versions table
CREATE TABLE content_versions (
    id UUID PRIMARY KEY,
    content_id UUID REFERENCES content(id),
    version_number INTEGER,
    changes JSONB,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Appendix D: Event Schemas

### Device Registration Event

```json
{
  "event_type": "device.registered",
  "timestamp": "2024-01-15T10:30:00Z",
  "correlation_id": "abc-123-def",
  "data": {
    "device_id": "dev_789",
    "name": "Lobby Display",
    "activation_code": "ABC123",
    "ip_address": "192.168.1.100",
    "registered_by": "usr_456"
  }
}
```

### Content Transcoded Event

```json
{
  "event_type": "content.transcoded",
  "timestamp": "2024-01-15T10:45:00Z",
  "correlation_id": "xyz-456-ghi",
  "data": {
    "content_id": "cnt_123",
    "original_url": "s3://bucket/original/video.mp4",
    "transcoded_urls": {
      "1080p": "s3://bucket/1080p/video.mp4",
      "720p": "s3://bucket/720p/video.mp4",
      "480p": "s3://bucket/480p/video.mp4"
    },
    "duration_seconds": 300,
    "processing_time_ms": 45000
  }
}
```

---

**Document Version:** 1.0
**Last Updated:** January 2025
**Author:** Backend System Architect
**Review Status:** Final