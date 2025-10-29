# Microservices Cloud Deployment Strategy for Digital Signage System

## Executive Summary

This document outlines a comprehensive cloud deployment strategy for scaling a digital signage system from a single server to support 10,000+ devices. The strategy emphasizes cost optimization, high availability, and gradual migration from the current infrastructure.

## Table of Contents
1. [Current State Analysis](#current-state-analysis)
2. [Deployment Strategy](#deployment-strategy)
3. [Infrastructure Architecture](#infrastructure-architecture)
4. [Service-Specific Requirements](#service-specific-requirements)
5. [Scaling Strategy](#scaling-strategy)
6. [Cost Analysis](#cost-analysis)
7. [Network Architecture](#network-architecture)
8. [High Availability & Disaster Recovery](#high-availability--disaster-recovery)
9. [Monitoring & Observability](#monitoring--observability)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Migration Roadmap](#migration-roadmap)

---

## 1. Current State Analysis

### Existing Infrastructure
- **Single Server**: 192.168.5.12
- **Services**: All services running on one machine
- **Database**: PostgreSQL on port 5433
- **API**: FastAPI on port 8001
- **Viewer**: Static HTML on port 8080
- **Limitations**: No redundancy, limited scalability, single point of failure

### Pain Points
- CPU bottleneck during video transcoding
- No horizontal scaling capability
- Limited bandwidth for content delivery
- No disaster recovery plan
- Manual deployment process

---

## 2. Deployment Strategy

### Recommended Approach: Hybrid Cloud Architecture

```yaml
Strategy: Hybrid Cloud with Edge Computing
├── On-Premise: Critical services & data sovereignty
├── Public Cloud: Scalable compute & CDN
└── Edge Locations: Content caching & low latency
```

### Why Hybrid?
1. **Data Sovereignty**: Keep sensitive data on-premise
2. **Cost Optimization**: Use cloud for burst capacity
3. **Low Latency**: Edge servers near device clusters
4. **Flexibility**: Mix of CapEx and OpEx

### Cloud Provider Recommendation: AWS + On-Premise

**Primary Cloud**: AWS
- Best CDN integration (CloudFront)
- Mature container services (EKS)
- Cost-effective for media workloads
- Strong presence in target regions

**Alternative**: Azure (if Microsoft ecosystem integration needed)

---

## 3. Infrastructure Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└─────────────┬───────────────────┬───────────────────────────┘
              │                   │
              ▼                   ▼
┌─────────────────────┐  ┌──────────────────┐
│   CloudFront CDN    │  │  Route 53 DNS    │
└─────────┬───────────┘  └──────┬───────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────┐
│         AWS Application Load Balancer        │
└────────────────┬─────────────────────────────┘
                 │
    ┌────────────┼────────────┬───────────────┐
    ▼            ▼            ▼               ▼
┌─────────┐ ┌─────────┐ ┌─────────┐   ┌─────────────┐
│ API     │ │ Auth    │ │WebSocket│   │ Web Admin   │
│ Gateway │ │ Service │ │ Service │   │  (React)    │
└────┬────┘ └────┬────┘ └────┬────┘   └─────────────┘
     │           │            │
     └───────────┼────────────┘
                 ▼
    ┌────────────────────────────────┐
    │     Service Mesh (Istio)       │
    └────────────┬────────────────────┘
                 │
    ┌────────────┼───────────┬────────────────┐
    ▼            ▼           ▼                ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Content  │ │ Device   │ │ Playlist │ │Transcode │
│ Service  │ │ Service  │ │ Service  │ │ Workers  │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │             │             │
     └────────────┼─────────────┼─────────────┘
                  ▼             ▼
         ┌──────────────┐ ┌──────────────┐
         │  PostgreSQL  │ │    Redis     │
         │   (RDS)      │ │  (ElastiCache)│
         └──────────────┘ └──────────────┘
                  │
                  ▼
         ┌──────────────┐
         │      S3       │
         │   Storage     │
         └──────────────┘
```

### 3.2 Container Orchestration: Kubernetes (EKS)

**Why Kubernetes over Docker Compose?**
- Auto-scaling capabilities
- Self-healing containers
- Service discovery
- Rolling updates
- Multi-cloud portability

### 3.3 Deployment Configuration

```yaml
# kubernetes/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: signage-system

---
# kubernetes/services/api-gateway/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: signage-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: signage/api-gateway:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
```

---

## 4. Service-Specific Requirements

### 4.1 Infrastructure Requirements Matrix

| Service | Min Replicas | Max Replicas | CPU (per pod) | Memory (per pod) | Storage | Auto-scaling Metric |
|---------|-------------|--------------|---------------|------------------|---------|-------------------|
| API Gateway | 3 | 10 | 500m | 512Mi | - | CPU > 70% |
| Auth Service | 2 | 5 | 250m | 256Mi | - | CPU > 60% |
| Content Service | 3 | 15 | 1000m | 1Gi | 100Gi | Request rate |
| Device Service | 3 | 20 | 500m | 512Mi | - | Connections |
| Playlist Service | 2 | 8 | 500m | 512Mi | - | CPU > 70% |
| WebSocket Service | 5 | 30 | 750m | 768Mi | - | Connections |
| Transcode Workers | 5 | 50 | 4000m | 8Gi | 500Gi | Queue length |
| Web Admin | 2 | 4 | 250m | 256Mi | - | CPU > 60% |

### 4.2 Service Deployment Strategies

#### API Gateway
```yaml
Deployment:
  Type: Rolling Update
  Strategy: Blue-Green for major updates
  Health Checks: HTTP /health endpoint
  Rate Limiting: 1000 req/min per IP
  Circuit Breaker: Enabled
```

#### Auth Service
```yaml
Deployment:
  Type: Rolling Update
  Session Management: Redis-backed
  Token Rotation: JWT with 1h expiry
  Backup Auth: Failover to secondary region
```

#### Content Service
```yaml
Deployment:
  Type: Canary (10% → 50% → 100%)
  Storage: S3 with lifecycle policies
  Cache: CloudFront + Redis
  Optimization: Image resizing on-the-fly
```

#### Transcode Workers
```yaml
Deployment:
  Type: Batch processing
  Queue: SQS with DLQ
  Processing: Spot instances for cost savings
  Priority Queues: Premium vs Standard
  GPU Support: Optional for H.265 encoding
```

#### WebSocket Service
```yaml
Deployment:
  Type: Stateful Set
  Sticky Sessions: Required
  Scaling: Based on connection count
  Failover: Connection migration on pod death
```

---

## 5. Scaling Strategy

### 5.1 Horizontal vs Vertical Scaling Decision Matrix

| Service | Primary Scaling | Secondary Scaling | Rationale |
|---------|----------------|-------------------|-----------|
| API Gateway | Horizontal | - | Stateless, easy to scale |
| Auth Service | Horizontal | - | Stateless with Redis sessions |
| Content Service | Horizontal | Vertical for cache | I/O bound, benefits from parallelism |
| Device Service | Horizontal | - | Connection-based scaling |
| Playlist Service | Horizontal | - | Lightweight, stateless |
| WebSocket | Horizontal | Vertical for connections | Connection limits per pod |
| Transcode | Both | - | CPU intensive, parallel processing |
| Database | Vertical | Read replicas | ACID requirements |
| Redis | Horizontal | Cluster mode | Memory and throughput |

### 5.2 Auto-scaling Configuration

```yaml
# Horizontal Pod Autoscaler for Content Service
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: content-service-hpa
  namespace: signage-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: content-service
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### 5.3 Cluster Auto-scaling

```yaml
# AWS EKS Node Group Configuration
NodeGroups:
  - name: general-purpose
    instanceTypes:
      - t3.large
      - t3.xlarge
    minSize: 3
    maxSize: 20
    desiredCapacity: 5
    volumeSize: 100
    labels:
      workload: general

  - name: transcode-workers
    instanceTypes:
      - c5.4xlarge  # CPU optimized
      - g4dn.xlarge # GPU for premium encoding
    minSize: 0
    maxSize: 50
    desiredCapacity: 5
    volumeSize: 500
    labels:
      workload: transcode
    taints:
      - key: transcode
        value: "true"
        effect: NoSchedule
    spot: true  # Use spot instances for cost savings
```

---

## 6. Cost Analysis

### 6.1 Infrastructure Cost Estimation (AWS)

#### 100 Devices Scale
```yaml
Monthly Cost Breakdown:
├── EKS Cluster: $73
├── EC2 Instances (5x t3.large): $304
├── RDS PostgreSQL (db.t3.medium): $70
├── ElastiCache Redis (cache.t3.micro): $25
├── S3 Storage (1TB): $23
├── CloudFront CDN (100GB transfer): $8
├── ALB: $20
├── Data Transfer: $50
└── Total: ~$573/month
```

#### 1,000 Devices Scale
```yaml
Monthly Cost Breakdown:
├── EKS Cluster: $73
├── EC2 Instances:
│   ├── General (8x t3.large): $486
│   └── Transcode (5x c5.xlarge spot): $340
├── RDS PostgreSQL (db.r5.large + read replica): $420
├── ElastiCache Redis (cache.m5.large cluster): $200
├── S3 Storage (10TB): $230
├── CloudFront CDN (1TB transfer): $85
├── ALB: $20
├── Data Transfer: $200
└── Total: ~$2,054/month
```

#### 10,000 Devices Scale
```yaml
Monthly Cost Breakdown:
├── EKS Cluster (multi-region): $146
├── EC2 Instances:
│   ├── General (20x t3.xlarge): $2,432
│   └── Transcode (20x c5.4xlarge spot): $2,720
├── RDS PostgreSQL (db.r5.2xlarge + 3 read replicas): $2,100
├── ElastiCache Redis (cache.r5.xlarge cluster): $800
├── S3 Storage (100TB): $2,300
├── CloudFront CDN (10TB transfer): $850
├── ALB (multi-region): $40
├── Data Transfer: $1,000
└── Total: ~$12,388/month
```

### 6.2 Cost Optimization Strategies

#### Reserved Instances & Savings Plans
```yaml
Optimization:
  Reserved Instances: 40% savings on predictable workloads
  Savings Plans: 30% savings with 1-year commitment
  Spot Instances: 70% savings for transcode workers

Estimated Savings:
  100 devices: $573 → $401 (30% reduction)
  1,000 devices: $2,054 → $1,438 (30% reduction)
  10,000 devices: $12,388 → $8,672 (30% reduction)
```

#### Resource Optimization
```yaml
Strategies:
  1. Right-sizing:
     - Monitor actual usage
     - Downsize overprovisioned resources
     - Use AWS Compute Optimizer

  2. Auto-scaling:
     - Scale down during off-peak hours
     - Use predictive scaling
     - Implement request coalescing

  3. Storage Optimization:
     - S3 Intelligent-Tiering
     - Lifecycle policies for old content
     - Compress videos efficiently

  4. CDN Optimization:
     - Cache everything possible
     - Set appropriate TTLs
     - Use origin shield

  5. Database Optimization:
     - Use read replicas effectively
     - Implement connection pooling
     - Archive old data to S3
```

#### FinOps Implementation
```yaml
Cost Management:
  Tagging Strategy:
    - Environment: dev/staging/prod
    - Service: content/device/transcode
    - Team: backend/frontend/devops
    - Customer: for multi-tenant scenarios

  Budget Alerts:
    - 50% threshold: Information
    - 80% threshold: Warning
    - 100% threshold: Critical
    - 120% threshold: Auto-scale down

  Cost Allocation:
    - Per service breakdown
    - Per environment costs
    - Per customer (if multi-tenant)

  Regular Reviews:
    - Weekly: Spot instance savings
    - Monthly: Resource utilization
    - Quarterly: Reserved instance planning
```

---

## 7. Network Architecture

### 7.1 VPC Design

```yaml
VPC Configuration:
  CIDR: 10.0.0.0/16

  Availability Zones: 3 (for HA)

  Subnets:
    Public:
      - 10.0.1.0/24 (AZ-1) - NAT Gateway, ALB
      - 10.0.2.0/24 (AZ-2) - NAT Gateway, ALB
      - 10.0.3.0/24 (AZ-3) - NAT Gateway, ALB

    Private:
      - 10.0.11.0/24 (AZ-1) - Application tier
      - 10.0.12.0/24 (AZ-2) - Application tier
      - 10.0.13.0/24 (AZ-3) - Application tier

    Database:
      - 10.0.21.0/24 (AZ-1) - RDS primary
      - 10.0.22.0/24 (AZ-2) - RDS standby
      - 10.0.23.0/24 (AZ-3) - Read replicas
```

### 7.2 Security Architecture

```yaml
Security Layers:
  1. Edge Security:
     - CloudFront with AWS WAF
     - DDoS protection (AWS Shield)
     - Rate limiting at CDN level

  2. Network Security:
     - Security Groups (micro-segmentation)
     - NACLs for subnet-level control
     - VPC Flow Logs for monitoring
     - AWS GuardDuty for threat detection

  3. Application Security:
     - TLS 1.3 everywhere
     - mTLS between services (Istio)
     - API Gateway authentication
     - OAuth 2.0 / JWT tokens

  4. Data Security:
     - Encryption at rest (AES-256)
     - Encryption in transit (TLS)
     - Database encryption (RDS)
     - S3 bucket encryption

  5. Access Control:
     - IAM roles for services
     - RBAC in Kubernetes
     - Secrets management (AWS Secrets Manager)
     - Audit logging (CloudTrail)
```

### 7.3 Network Segmentation

```yaml
Network Zones:
  DMZ:
    - Load Balancers
    - API Gateway
    - Web Admin frontend

  Application Zone:
    - Microservices
    - WebSocket servers
    - Background workers

  Data Zone:
    - PostgreSQL (RDS)
    - Redis (ElastiCache)
    - S3 endpoints

  Management Zone:
    - Bastion hosts
    - CI/CD agents
    - Monitoring collectors
```

---

## 8. High Availability & Disaster Recovery

### 8.1 High Availability Design

```yaml
HA Strategy:
  Multi-AZ Deployment:
    - All services across 3 AZs
    - Auto-failover for databases
    - Cross-AZ load balancing

  Service Redundancy:
    - Minimum 2 replicas per service
    - Anti-affinity rules
    - Pod disruption budgets

  Database HA:
    - RDS Multi-AZ with auto-failover
    - Read replicas for load distribution
    - Point-in-time recovery

  Cache HA:
    - Redis cluster mode
    - Automatic failover
    - Persistence enabled
```

### 8.2 Disaster Recovery Plan

```yaml
DR Strategy:
  RPO: 1 hour (data loss tolerance)
  RTO: 4 hours (recovery time)

  Backup Strategy:
    Databases:
      - Automated daily backups
      - 30-day retention
      - Cross-region replication

    Object Storage:
      - S3 cross-region replication
      - Versioning enabled
      - MFA delete protection

    Configuration:
      - GitOps (all config in Git)
      - Automated backup to S3
      - Terraform state in S3

  Recovery Procedures:
    1. Region Failure:
       - Failover to secondary region
       - Update Route 53 DNS
       - Restore from backups if needed

    2. Service Failure:
       - Kubernetes auto-recovery
       - Circuit breaker activation
       - Fallback to cache

    3. Data Corruption:
       - Point-in-time recovery
       - Restore from snapshots
       - Replay from event store
```

### 8.3 Multi-Region Architecture (10,000+ devices)

```yaml
Primary Region: us-east-1
  - Full application stack
  - Master database
  - Primary S3 bucket

Secondary Region: us-west-2
  - Standby application stack
  - Read replica database
  - S3 replication target

Edge Locations:
  - CloudFront POPs worldwide
  - Cached content delivery
  - Reduced latency

Failover Strategy:
  - Route 53 health checks
  - Automated DNS failover
  - <5 minute detection
  - <15 minute failover
```

---

## 9. Monitoring & Observability

### 9.1 Observability Stack

```yaml
Metrics:
  Platform: Prometheus + Grafana

  Key Metrics:
    - Request rate, error rate, duration (RED)
    - CPU, memory, disk, network (USE)
    - Business metrics (devices online, content served)
    - Custom application metrics

  Dashboards:
    - Service health overview
    - Resource utilization
    - Cost tracking
    - Business KPIs

Logging:
  Platform: ELK Stack (Elasticsearch, Logstash, Kibana)

  Log Sources:
    - Application logs
    - Access logs
    - Error logs
    - Audit logs

  Retention:
    - Hot: 7 days (SSD)
    - Warm: 30 days (HDD)
    - Cold: 1 year (S3)

Tracing:
  Platform: Jaeger or AWS X-Ray

  Features:
    - Distributed tracing
    - Latency analysis
    - Dependency mapping
    - Error tracking

Alerting:
  Platform: AlertManager + PagerDuty

  Alert Levels:
    - P1: Service down (immediate page)
    - P2: Degraded performance (15 min)
    - P3: Warning threshold (1 hour)
    - P4: Informational (daily digest)
```

### 9.2 Monitoring Configuration

```yaml
# prometheus/config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)

  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
```

### 9.3 SLI/SLO/SLA Definition

```yaml
Service Level Indicators (SLIs):
  API Gateway:
    - Availability: HTTP 200 responses / total requests
    - Latency: 95th percentile < 200ms
    - Error rate: 5xx errors / total requests

  WebSocket Service:
    - Connection success rate
    - Message delivery latency < 100ms
    - Concurrent connections

  Transcode Service:
    - Job completion rate
    - Processing time per GB
    - Queue depth

Service Level Objectives (SLOs):
  - API Availability: 99.9% (43.2 min downtime/month)
  - WebSocket Availability: 99.5%
  - Content Delivery: 99.99% from CDN
  - Transcode SLA: 95% within 2x estimated time

Error Budgets:
  - Monthly error budget: 0.1% of requests
  - Automated rollback on budget breach
  - Quarterly review and adjustment
```

---

## 10. CI/CD Pipeline

### 10.1 Pipeline Architecture

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-gateway, auth, content, device, playlist, websocket, transcode]
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ secrets.ECR_REGISTRY }}
        run: |
          docker build -t $ECR_REGISTRY/${{ matrix.service }}:${{ github.sha }} ./services/${{ matrix.service }}
          docker push $ECR_REGISTRY/${{ matrix.service }}:${{ github.sha }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/*=*:${{ github.sha }} -n signage-staging
          kubectl rollout status deployment -n signage-staging

  integration-tests:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - name: Run integration tests
        run: |
          npm run test:integration -- --env=staging

  deploy-production:
    needs: integration-tests
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/*=*:${{ github.sha }} -n signage-production --record
          kubectl rollout status deployment -n signage-production
```

### 10.2 Deployment Strategies

```yaml
Strategies by Service:
  Critical Services (Auth, API Gateway):
    Strategy: Blue-Green
    Rollback: Instant switch to previous version
    Testing: Full integration test suite

  Stateful Services (WebSocket):
    Strategy: Rolling update with session draining
    Rollback: Gradual with connection migration
    Testing: Connection persistence tests

  Heavy Processing (Transcode):
    Strategy: Canary (10% → 50% → 100%)
    Rollback: Immediate on error rate spike
    Testing: Performance benchmarks

  Frontend (Web Admin):
    Strategy: Progressive rollout with feature flags
    Rollback: Feature flag toggle
    Testing: E2E tests with Cypress
```

### 10.3 GitOps with ArgoCD

```yaml
# argocd/applications/production.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: signage-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/signage-config
    targetRevision: HEAD
    path: environments/production
  destination:
    server: https://kubernetes.default.svc
    namespace: signage-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - Validate=true
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

---

## 11. Migration Roadmap

### Phase 1: Preparation (Week 1-2)
```yaml
Tasks:
  1. Containerization:
     - Dockerize all services
     - Create Docker Compose for local testing
     - Set up container registry (ECR)

  2. Configuration Management:
     - Extract all hardcoded configs
     - Set up secrets management
     - Create environment-specific configs

  3. Database Preparation:
     - Database schema migration scripts
     - Data backup procedures
     - Test restore procedures

  4. Monitoring Setup:
     - Install Prometheus/Grafana locally
     - Define key metrics
     - Create initial dashboards
```

### Phase 2: Staging Environment (Week 3-4)
```yaml
Tasks:
  1. Infrastructure:
     - Create AWS account structure
     - Set up VPC and networking
     - Deploy EKS cluster (small)

  2. Core Services:
     - Deploy database (RDS)
     - Deploy Redis cache
     - Set up S3 buckets

  3. Application Deployment:
     - Deploy all microservices to staging
     - Configure service mesh
     - Set up ingress/load balancer

  4. Testing:
     - Load testing with 100 simulated devices
     - Performance benchmarking
     - Security scanning
```

### Phase 3: Production Pilot (Week 5-6)
```yaml
Tasks:
  1. Production Setup:
     - Clone staging to production
     - Enable auto-scaling
     - Configure CDN

  2. Migration Strategy:
     - Migrate 10 devices as pilot
     - Monitor performance
     - Gather feedback

  3. Data Migration:
     - Sync content to S3
     - Replicate database
     - Test failover procedures

  4. Documentation:
     - Operational runbooks
     - Troubleshooting guides
     - Training materials
```

### Phase 4: Gradual Migration (Week 7-8)
```yaml
Migration Waves:
  Wave 1 (10% - 100 devices):
    - Low-priority devices
    - Monitor for 48 hours
    - Rollback plan ready

  Wave 2 (25% - 250 devices):
    - Mix of device types
    - Include some critical devices
    - 72-hour monitoring

  Wave 3 (50% - 500 devices):
    - Half of all devices
    - Full load testing
    - Performance optimization

  Wave 4 (100% - All devices):
    - Complete migration
    - Decommission old infrastructure
    - Post-migration review
```

### Phase 5: Optimization (Week 9-10)
```yaml
Post-Migration Tasks:
  1. Performance Tuning:
     - Right-size resources
     - Optimize auto-scaling rules
     - Fine-tune caching

  2. Cost Optimization:
     - Purchase reserved instances
     - Enable spot instances for workers
     - Implement cost alerts

  3. Security Hardening:
     - Security audit
     - Penetration testing
     - Compliance validation

  4. Documentation Update:
     - Architecture diagrams
     - Updated procedures
     - Lessons learned
```

---

## 12. Quick Reference

### Key Commands

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/

# Scale deployment
kubectl scale deployment content-service --replicas=10 -n signage-system

# View logs
kubectl logs -f deployment/api-gateway -n signage-system

# Port forward for debugging
kubectl port-forward svc/api-gateway 8000:8000 -n signage-system

# Get cluster status
kubectl get nodes
kubectl get pods -n signage-system
kubectl top nodes
kubectl top pods -n signage-system

# Terraform commands
terraform init
terraform plan -out=tfplan
terraform apply tfplan
terraform destroy

# AWS CLI commands
aws eks update-kubeconfig --region us-east-1 --name signage-cluster
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
```

### Important URLs

```yaml
Production:
  API Gateway: https://api.signage.example.com
  Web Admin: https://admin.signage.example.com
  Grafana: https://monitoring.signage.example.com
  ArgoCD: https://argocd.signage.example.com

Staging:
  API Gateway: https://api-staging.signage.example.com
  Web Admin: https://admin-staging.signage.example.com

Documentation:
  Runbook: https://wiki.signage.example.com/runbook
  API Docs: https://api.signage.example.com/docs
```

### Support Contacts

```yaml
On-Call:
  Primary: DevOps Team
  Secondary: Backend Team
  Escalation: CTO

Vendors:
  AWS Support: Premium support tier
  CDN Support: CloudFront team
  Database: RDS support

Communication:
  Slack: #signage-incidents
  Email: devops@signage.example.com
  War Room: https://meet.signage.example.com/incident
```

---

## Conclusion

This comprehensive deployment strategy provides a clear path from your current single-server setup to a scalable, highly available microservices architecture capable of supporting 10,000+ devices. The hybrid cloud approach balances cost, performance, and operational complexity while maintaining flexibility for future growth.

### Key Success Factors
1. **Gradual Migration**: Phased approach minimizes risk
2. **Cost Optimization**: 30-40% savings through smart resource management
3. **High Availability**: 99.9% uptime with multi-region failover
4. **Scalability**: Auto-scaling from 100 to 10,000 devices
5. **Observability**: Complete visibility into system health
6. **Security**: Defense in depth with multiple security layers

### Next Steps
1. Review and approve the architecture
2. Set up AWS accounts and initial infrastructure
3. Begin containerization of services
4. Start with Phase 1 of the migration roadmap
5. Establish monitoring and alerting early

### Estimated Timeline
- **Total Duration**: 10 weeks
- **Initial Production**: Week 5
- **Full Migration**: Week 8
- **Optimization Complete**: Week 10

This living document should be updated as the system evolves and new requirements emerge.