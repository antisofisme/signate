# Infrastructure Action Plan: 90-Day Implementation

**Target**: Move from 7.1/10 to 7.8/10 (Production-Ready) in 8 weeks

---

## PHASE 1: CRITICAL FOUNDATION (Weeks 1-2)

### 1.1 Disaster Recovery Implementation

**Objective**: Automate backups, establish RTO/RPO, enable fast recovery

**Tasks:**

```yaml
Week 1 - Backup Automation:

  [ ] Task 1.1.1: Implement Daily Database Backups
      Owner: DevOps
      Time: 4 hours
      Steps:
        1. Create backup directory: /mnt/backups/
        2. Write backup script: backup_database.sh
        3. Schedule with cron (daily 2:00 AM UTC)
        4. Test: Verify backup file created
        5. Test: Verify backup can be restored
        6. Monitor: Cron logs for failures

      Script outline:
      ```bash
      #!/bin/bash
      # Daily PostgreSQL backup to local + remote
      BACKUP_DIR="/mnt/backups"
      DATE=$(date +%Y%m%d_%H%M%S)

      # Full backup
      pg_dump -U signage_user -d signage_db > $BACKUP_DIR/full_$DATE.sql
      gzip $BACKUP_DIR/full_$DATE.sql

      # Upload to S3
      aws s3 cp $BACKUP_DIR/full_$DATE.sql.gz s3://signage-backups/

      # Cleanup old backups (keep 30 days)
      find $BACKUP_DIR -name "full_*.sql.gz" -mtime +30 -delete

      # Alert on success/failure
      curl -X POST https://hooks.slack.com/... \
        -d "{\"text\":\"Backup completed\"}"
      ```

  [ ] Task 1.1.2: Enable PostgreSQL WAL Archiving
      Owner: Database Admin
      Time: 2 hours
      Steps:
        1. Enable WAL archiving in postgresql.conf
        2. Set archive_command to S3 upload
        3. Verify archiving is working
        4. Test point-in-time recovery

      Config:
      ```
      archive_mode = on
      archive_timeout = 300
      archive_command = 'aws s3 cp %p s3://signage-backups/wal/%f'
      ```

  [ ] Task 1.1.3: Test Backup Restoration
      Owner: DevOps
      Time: 3 hours
      Steps:
        1. Create test database instance
        2. Restore latest full backup
        3. Verify table counts match
        4. Query recent data
        5. Verify no corruption
        6. Document time taken
        7. Destroy test instance

      Commands:
      ```bash
      # Restore test
      createdb signage_test
      psql -d signage_test < /backups/full_backup.sql
      psql -d signage_test -c "SELECT COUNT(*) FROM users;"
      ```

Week 2 - RTO/RPO Targets & Procedures:

  [ ] Task 1.1.4: Define RTO/RPO Targets
      Owner: CTO + DevOps
      Time: 2 hours
      Output:
        - Critical services (PMS, Payment): RTO 1h, RPO 5m
        - Important services (HRM, Accounting): RTO 4h, RPO 15m
        - Analytics: RTO 24h, RPO 1h

      Document: DISASTER_RECOVERY_PLAN.md

  [ ] Task 1.1.5: Create Disaster Recovery Runbooks
      Owner: DevOps + Engineering
      Time: 6 hours
      Runbooks needed:
        1. Database Recovery (full backup + incremental)
        2. Application Server Recovery (Docker Swarm restart)
        3. Multi-server Failover
        4. DNS Cutover (if multi-region later)
        5. Incident Communication

      Each runbook should have:
        - Prerequisites
        - Step-by-step procedures
        - Estimated time
        - Rollback instructions
        - Contact list

  [ ] Task 1.1.6: Monthly Backup Restoration Test
      Owner: DevOps
      Time: 2 hours (monthly)
      Procedure:
        1. First Saturday of each month at 3:00 AM UTC
        2. Pick latest backup
        3. Restore to test instance
        4. Run integrity checks
        5. Report results to team
        6. GitHub issue if problems found
```

**Deliverables:**
- Automated daily backups (local + remote)
- WAL archiving to S3
- Restoration procedures documented
- Monthly test scheduled
- RTO/RPO SLAs defined

**Success Criteria:**
- Backup completes daily without errors
- Restoration takes < 30 minutes
- Team can follow runbook without help

---

### 1.2 Incident Response Planning

**Objective**: Define severity levels, escalation, procedures

**Tasks:**

```yaml
Week 1 - Incident Response Plan:

  [ ] Task 1.2.1: Define Incident Severity Levels
      Owner: CTO
      Time: 1 hour
      Output: INCIDENT_SEVERITY_LEVELS.md
      Content:
        - Level 1 (Degradation): API slow but functional
        - Level 2 (Outage): One component down
        - Level 3 (Critical): Multiple components down
        - Level 4 (Disaster): Data center failure

  [ ] Task 1.2.2: Create Escalation Path
      Owner: CTO + Engineering Lead
      Time: 1.5 hours
      Output: ESCALATION_POLICY.md

      Example:
      ```
      Level 1 (Degradation):
        ├─ Alert on-call engineer (Slack)
        ├─ 15 min investigation
        ├─ If not resolved: Page engineering lead
        └─ Communicate via status page

      Level 2 (Outage):
        ├─ Page on-call + lead (immediate)
        ├─ Activate war room (Slack channel)
        ├─ CTO joins within 10 min
        ├─ Communicate to affected tenants (5 min)
        └─ Status update every 15 min

      Level 3 (Critical):
        ├─ Page entire engineering team
        ├─ Activate incident commander role
        ├─ Engage CEO/Product (awareness)
        ├─ Public status page (every 5 min)
        └─ Potential: Offer service credits

      Level 4 (Disaster):
        ├─ CEO approval required
        ├─ Contact legal team (potential GDPR implications)
        ├─ Media/PR coordination
        ├─ Customer calls (personal outreach)
        └─ Deep post-mortem (external audit)
      ```

  [ ] Task 1.2.3: Write Common Incident Runbooks
      Owner: DevOps + Engineering
      Time: 4 hours
      Runbooks:
        1. API Server Down
        2. Database Connection Pool Exhausted
        3. Disk Space Critical
        4. Memory Pressure
        5. Network Latency High
        6. Payment Gateway Failure

      Template for each:
      ```markdown
      # Runbook: [Issue Name]

      **Severity**: Level X
      **RTO**: X minutes

      ## Prerequisites
      - [ ] Access to monitoring dashboard
      - [ ] SSH to production servers
      - [ ] Slack notification permissions

      ## Symptoms
      - API returns 503 errors
      - Monitoring alert: "API error rate > 1%"

      ## Investigation (5 min)
      1. Check API service status
      2. Check error logs
      3. Check resource utilization
      4. Determine root cause

      ## Resolution (varies)
      - If OOM: Restart service
      - If disk full: Clean logs / upgrade storage
      - If CPU high: Check slow queries

      ## Verification
      - [ ] API responding to requests
      - [ ] Error rate < 0.1%
      - [ ] No customer complaints

      ## Post-Incident
      - [ ] Create GitHub issue
      - [ ] Root cause analysis
      - [ ] Preventive measures
      ```

Week 2 - Communication & Drills:

  [ ] Task 1.2.4: Set Up Incident Communication
      Owner: CTO + DevOps
      Time: 2 hours
      Setup:
        - Slack channel: #incidents
        - On-call rotation: PagerDuty or Opsgenie
        - Status page: Use Statuspage.io (free tier) or similar
        - Email template: For customer notification

      Notification Rules:
        - Level 1: Slack #incidents
        - Level 2: Slack + PagerDuty alert
        - Level 3: Slack + PagerDuty + SMS
        - Level 4: All above + CTO call + legal email

  [ ] Task 1.2.5: Schedule Monthly Incident Drill
      Owner: CTO
      Time: 2 hours/month
      Procedure:
        - Simulate service failure
        - Team follows escalation procedures
        - Measure response times
        - Identify gaps in runbooks
        - Update based on learnings

      Drill cadence:
        1st drill (4 weeks): Simulate API outage
        2nd drill (8 weeks): Simulate database failure
        3rd drill (12 weeks): Simulate multi-component failure
```

**Deliverables:**
- Incident severity levels (4 levels)
- Escalation policy with names/numbers
- 6+ common incident runbooks
- Communication templates
- Incident drill schedule

**Success Criteria:**
- Team can recite escalation path
- Runbooks clear enough for quick reference
- First incident response < 5 minutes
- Drill completed monthly

---

## PHASE 2: CI/CD AUTOMATION (Weeks 3-4)

### 2.1 GitHub Actions CI/CD Pipeline

**Objective**: Automate testing, security scanning, deployment

**Tasks:**

```yaml
Week 3 - Build & Test Pipeline:

  [ ] Task 2.1.1: Create GitHub Actions Workflow
      Owner: DevOps + Backend Lead
      Time: 8 hours

      File: .github/workflows/ci-cd.yml

      Stages:
        1. Trigger: On push to main, PR to main
        2. Build: Checkout code
        3. Test: Run tests (backend + frontend)
        4. Scan: Security scanning (SCA, SAST)
        5. Build images: Docker images
        6. Push: To registry
        7. Deploy staging: Deploy to staging environment
        8. Integration tests: Run E2E tests
        9. Deploy production: Manual approval required

      Minimal structure:
      ```yaml
      name: CI/CD Pipeline

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

            - name: Backend Tests
              run: |
                cd backend-python
                pip install -r requirements.txt
                pytest --cov=app tests/
                coverage report --fail-under=75

            - name: Frontend Tests
              run: |
                cd cms-vite
                npm install
                npm run test

        build:
          needs: test
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3

            - name: Build images
              run: |
                docker build -t backend:${{ github.sha }} backend-python/
                docker build -t cms-vite:${{ github.sha }} cms-vite/

            - name: Push to registry
              run: |
                docker login -u ${{ secrets.DOCKER_USER }} -p ${{ secrets.DOCKER_PASS }}
                docker push backend:${{ github.sha }}
                docker push cms-vite:${{ github.sha }}

        deploy:
          needs: build
          runs-on: ubuntu-latest
          environment: production
          steps:
            - name: Deploy
              run: |
                # SSH to VPS and update
                ssh -i ${{ secrets.SSH_KEY }} deploy@${{ secrets.PROD_HOST }} \
                  "cd /app && docker-compose pull && docker-compose up -d"
      ```

  [ ] Task 2.1.2: Set Up Automated Testing
      Owner: Backend Lead + Frontend Lead
      Time: 6 hours

      Backend (pytest):
        - Unit tests: app/tests/unit/
        - Integration tests: app/tests/integration/
        - Target coverage: 75%+
        - Command: pytest --cov=app tests/

      Frontend (Vitest):
        - Component tests: src/__tests__/
        - Hook tests: src/__tests__/hooks/
        - Target coverage: 70%+
        - Command: npm run test

      Create test structure:
      ```
      backend-python/
      ├── tests/
      │   ├── conftest.py (fixtures)
      │   ├── unit/
      │   │   ├── test_auth.py
      │   │   ├── test_devices.py
      │   │   └── test_content.py
      │   └── integration/
      │       ├── test_api_endpoints.py
      │       └── test_database.py

      cms-vite/
      ├── src/__tests__/
      │   ├── components/
      │   │   └── LoginForm.test.tsx
      │   ├── hooks/
      │   │   └── useAuth.test.ts
      │   └── api/
      │       └── authApi.test.ts
      ```

  [ ] Task 2.1.3: Dependency Security Scanning
      Owner: DevOps
      Time: 3 hours

      Tools:
        - Dependabot (GitHub native)
        - Snyk (free tier for OSS)
        - OWASP Dependency Check

      Setup:
        1. Enable Dependabot in GitHub
        2. Configure to auto-update minor versions
        3. Manual approval for major versions
        4. Weekly schedule

      Add to CI:
      ```yaml
      - name: Run Snyk
        run: |
          npm install -g snyk
          snyk test --file=package.json --severity-threshold=high
      ```

Week 4 - Deployment & Security:

  [ ] Task 2.1.4: Container Image Scanning
      Owner: DevOps + Security
      Time: 3 hours

      Add Trivy scanning:
      ```yaml
      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: backend:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload to GitHub
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      ```

      Fail if:
        - CRITICAL vulnerabilities found
        - Alert on HIGH (with review option)

  [ ] Task 2.1.5: Blue-Green Deployment
      Owner: DevOps
      Time: 4 hours

      Concept:
        - Blue: Current production (v1.0)
        - Green: New production (v1.1)
        - Load balancer routes traffic

      Implementation (Docker Swarm):
      ```bash
      # Deploy to service with rolling update
      docker service update \
        --image backend:SHA \
        --update-delay 30s \
        --update-parallelism 1 \
        --update-failure-action rollback \
        signage_backend

      # Automatic rollback if health check fails
      ```

  [ ] Task 2.1.6: Secrets Management
      Owner: DevOps + Security
      Time: 3 hours

      GitHub Actions secrets:
        - DOCKER_USER
        - DOCKER_PASS
        - SSH_KEY (private key)
        - PROD_HOST
        - SLACK_WEBHOOK

      Store in: Settings → Secrets → Actions

      Use in workflow:
      ```yaml
      - name: Deploy
        env:
          SSH_KEY: ${{ secrets.SSH_KEY }}
        run: |
          mkdir -p ~/.ssh
          echo "$SSH_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
      ```

  [ ] Task 2.1.7: Approval Gates
      Owner: CTO
      Time: 2 hours

      Add manual approval before prod deployment:
      ```yaml
      deploy-production:
        needs: integration-tests
        environment:
          name: production
          # Add deployment protection rules in Settings
        runs-on: ubuntu-latest
      ```

      In GitHub: Settings → Environments → production
        - Add required reviewers
        - Require status checks to pass
        - Restrict deployment branches

  [ ] Task 2.1.8: Documentation & Runbook
      Owner: DevOps
      Time: 2 hours

      Create: DEPLOYMENT_RUNBOOK.md
      Content:
        - How to manually deploy if automation fails
        - How to rollback
        - How to view deployment logs
        - How to verify deployment success
        - Troubleshooting common issues
```

**Deliverables:**
- GitHub Actions CI/CD pipeline (complete)
- Automated testing (unit + integration)
- Security scanning (dependencies + containers)
- Blue-green deployment
- Approval gates for production

**Success Criteria:**
- First commit triggers pipeline automatically
- Tests run and pass/fail correctly
- Security scan blocks vulnerable code
- Deployment to staging automatic
- Production requires manual approval
- Can rollback with single command

---

## PHASE 3: MONITORING & OBSERVABILITY (Weeks 5-6)

### 3.1 Prometheus + Grafana Setup

**Objective**: Visibility into system health, per-tenant metrics, alerting

**Tasks:**

```yaml
Week 5 - Metrics Collection:

  [ ] Task 3.1.1: Deploy Prometheus
      Owner: DevOps
      Time: 2 hours

      Add to docker-compose:
      ```yaml
      prometheus:
        image: prom/prometheus
        ports:
          - "9090:9090"
        volumes:
          - ./prometheus.yml:/etc/prometheus/prometheus.yml
          - prometheus_data:/prometheus
        command:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus'
          - '--storage.tsdb.retention.time=30d'
      ```

      prometheus.yml:
      ```yaml
      global:
        scrape_interval: 15s

      scrape_configs:
        - job_name: 'fastapi'
          static_configs:
            - targets: ['api:8000']

        - job_name: 'postgres'
          static_configs:
            - targets: ['postgres:5432']

        - job_name: 'redis'
          static_configs:
            - targets: ['redis:6379']

        - job_name: 'docker'
          static_configs:
            - targets: ['localhost:9323']
      ```

  [ ] Task 3.1.2: Add Prometheus Metrics to FastAPI
      Owner: Backend Lead
      Time: 3 hours

      Install: pip install prometheus-client

      Implement:
      ```python
      from prometheus_client import Counter, Histogram, Gauge
      from fastapi import Request
      import time

      # Define metrics
      request_count = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status', 'tenant_id']
      )

      request_duration = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration',
        ['method', 'endpoint', 'tenant_id']
      )

      active_requests = Gauge(
        'http_active_requests',
        'Active HTTP requests',
        ['endpoint']
      )

      # Middleware
      @app.middleware("http")
      async def metrics_middleware(request: Request, call_next):
        method = request.method
        path = request.url.path
        tenant_id = request.headers.get("x-tenant-id", "unknown")

        active_requests.labels(endpoint=path).inc()

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        request_count.labels(
          method=method,
          endpoint=path,
          status=response.status_code,
          tenant_id=tenant_id
        ).inc()

        request_duration.labels(
          method=method,
          endpoint=path,
          tenant_id=tenant_id
        ).observe(duration)

        active_requests.labels(endpoint=path).dec()

        return response

      # Expose metrics
      @app.get("/metrics")
      async def metrics():
        from prometheus_client import generate_latest
        return generate_latest()
      ```

  [ ] Task 3.1.3: Deploy Grafana
      Owner: DevOps
      Time: 2 hours

      Add to docker-compose:
      ```yaml
      grafana:
        image: grafana/grafana
        ports:
          - "3000:3000"
        environment:
          - GF_SECURITY_ADMIN_PASSWORD=admin
          - GF_INSTALL_PLUGINS=grafana-piechart-panel
        volumes:
          - grafana_data:/var/lib/grafana
        depends_on:
          - prometheus
      ```

      Initial setup:
        1. Access http://localhost:3000
        2. Login: admin / admin
        3. Change password
        4. Add Prometheus data source

  [ ] Task 3.1.4: Create Platform Overview Dashboard
      Owner: DevOps + SRE
      Time: 3 hours

      Panels:
        - API availability (uptime %)
        - Request rate (req/sec)
        - Error rate (%)
        - p95 latency
        - Active tenants
        - Database connections
        - Cache hit ratio
        - Top error types

      Queries (PromQL):
      ```
      # Availability
      100 * (count(up == 1) / count(up))

      # Request rate
      rate(http_requests_total[5m])

      # Error rate
      rate(http_requests_total{status=~"5.."}[5m]) /
      rate(http_requests_total[5m])

      # p95 latency
      histogram_quantile(0.95,
        rate(http_request_duration_seconds_bucket[5m]))
      ```

Week 6 - Per-Tenant Metrics & Alerting:

  [ ] Task 3.1.5: Create Per-Tenant Dashboard
      Owner: DevOps
      Time: 2 hours

      Dashboard shows:
        - My tenant ID (dropdown select)
        - API calls used this month
        - Error rate for my tenant
        - Average latency
        - Data usage
        - Estimated bill

      Filtering:
      ```
      # Filter metrics by tenant_id
      http_requests_total{tenant_id="hotel_001"}
      http_request_duration_seconds{tenant_id="hotel_001"}
      ```

  [ ] Task 3.1.6: Configure Alerting Rules
      Owner: DevOps
      Time: 3 hours

      Create: prometheus-alert-rules.yml

      Rules:
      ```yaml
      groups:
        - name: api_health
          rules:
            - alert: HighErrorRate
              expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
              for: 5m
              annotations:
                summary: "High error rate detected"

            - alert: HighLatency
              expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5
              for: 5m
              annotations:
                summary: "p99 latency > 500ms"

            - alert: DatabaseConnectionPoolExhaustion
              expr: pg_stat_activity_count / 100 > 0.8
              annotations:
                summary: "Database connections > 80%"
      ```

  [ ] Task 3.1.7: Set Up Alert Routing
      Owner: DevOps
      Time: 2 hours

      Use Alertmanager:
      ```yaml
      # alertmanager.yml
      route:
        receiver: default
        group_by: ['alertname']

      receivers:
        - name: 'default'
          slack_configs:
            - api_url: $SLACK_WEBHOOK
              channel: '#alerts'
              title: '{{ .GroupLabels.alertname }}'
              text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
      ```

  [ ] Task 3.1.8: Documentation
      Owner: DevOps
      Time: 2 hours

      Create: MONITORING_GUIDE.md
      Content:
        - How to access Grafana
        - How to create custom dashboards
        - How to interpret metrics
        - How to add alerts
        - Common queries reference
```

**Deliverables:**
- Prometheus metrics collection (all services)
- Grafana dashboards (Platform + Per-Tenant)
- Alert rules (critical metrics)
- Alert routing to Slack
- Monitoring documentation

**Success Criteria:**
- Metrics visible in Grafana
- Dashboards load in < 2 seconds
- Alerts fire correctly
- Alert goes to Slack within 5 seconds
- Team can interpret dashboard

---

## PHASE 4: SECURITY HARDENING (Weeks 7-8)

### 4.1 Secrets Management & Image Signing

**Objective**: Secure credential storage, image integrity verification

**Tasks:**

```yaml
Week 7 - Secrets Management:

  [ ] Task 4.1.1: Implement HashiCorp Vault
      Owner: Security + DevOps
      Time: 4 hours

      Deploy Vault (Docker):
      ```yaml
      vault:
        image: vault:latest
        ports:
          - "8200:8200"
        environment:
          VAULT_DEV_ROOT_TOKEN_ID: "dev-token"
          VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
        volumes:
          - vault_data:/vault/data
      ```

      Initialize:
      ```bash
      # Unseal vault (dev mode)
      vault operator init
      vault operator unseal

      # Create secret
      vault kv put secret/database/prod \
        username="signage_user" \
        password="secure_password"

      # Retrieve secret
      vault kv get secret/database/prod
      ```

      FastAPI integration:
      ```python
      import hvac

      vault_client = hvac.Client(
        url='http://vault:8200',
        token='dev-token'
      )

      db_creds = vault_client.secrets.kv.read_secret_version(
        path='database/prod'
      )

      # Use credentials
      DB_USER = db_creds['data']['data']['username']
      DB_PASS = db_creds['data']['data']['password']
      ```

  [ ] Task 4.1.2: Remove Hardcoded Secrets
      Owner: Backend Lead
      Time: 3 hours

      Find and replace:
      ```bash
      # Find env vars in code
      grep -r "\.env" backend-python/ --include="*.py"
      grep -r "SECRET" backend-python/ --include="*.py"
      ```

      Replace with Vault:
      ```python
      # Before
      API_KEY = os.getenv("PAYMENT_API_KEY")

      # After
      api_creds = vault_client.secrets.kv.read_secret_version(
        path='payment/api'
      )
      API_KEY = api_creds['data']['data']['key']
      ```

  [ ] Task 4.1.3: Enable Image Signing with Cosign
      Owner: DevOps + Security
      Time: 3 hours

      Install Cosign:
      ```bash
      # Install
      curl https://github.com/sigstore/cosign/releases/download/v1.13.0/cosign-linux-amd64 -o /usr/local/bin/cosign
      chmod +x /usr/local/bin/cosign
      ```

      Generate signing key:
      ```bash
      cosign generate-key-pair
      # Generates: cosign.key (private), cosign.pub (public)
      ```

      Sign images (in CI):
      ```yaml
      - name: Sign image
        run: |
          cosign sign --key cosign.key \
            docker.io/myregistry/backend:${{ github.sha }}
      ```

      Verify image (at deployment):
      ```bash
      cosign verify --key cosign.pub \
        docker.io/myregistry/backend:${{ github.sha }}
      ```

      Store keys in Vault:
      ```bash
      vault kv put secret/signing/cosign \
        private_key="@cosign.key" \
        public_key="@cosign.pub"
      ```

Week 8 - Security Audit & Hardening:

  [ ] Task 4.1.4: Enable Audit Logging
      Owner: Backend + DevOps
      Time: 2 hours

      Add audit middleware:
      ```python
      import logging
      import json
      from datetime import datetime

      audit_logger = logging.getLogger("audit")

      @app.middleware("http")
      async def audit_middleware(request: Request, call_next):
        user_id = request.headers.get("x-user-id")
        tenant_id = request.headers.get("x-tenant-id")

        response = await call_next(request)

        audit_log = {
          "timestamp": datetime.utcnow().isoformat(),
          "user_id": user_id,
          "tenant_id": tenant_id,
          "method": request.method,
          "path": request.url.path,
          "status": response.status_code,
          "ip_address": request.client.host
        }

        # Log sensitive actions
        if request.method in ["POST", "DELETE", "PUT"]:
          audit_logger.info(json.dumps(audit_log))
      ```

  [ ] Task 4.1.5: Document Security Controls
      Owner: Security
      Time: 2 hours

      Create: SECURITY_CONTROLS.md
      Content:
        - Authentication (JWT + httpOnly)
        - Authorization (RBAC)
        - Encryption (at rest + in transit)
        - Audit logging
        - Rate limiting
        - Input validation
        - CORS policy
        - Security headers

  [ ] Task 4.1.6: Schedule Security Review
      Owner: CTO
      Time: 1 hour

      Plan:
        - Quarterly security review
        - Annual penetration test
        - Bug bounty program (if feasible)
        - Dependency updates (weekly)
        - Security patches (as available)

  [ ] Task 4.1.7: Create Security Incident Response
      Owner: Security + CTO
      Time: 2 hours

      Create: SECURITY_INCIDENT_RESPONSE.md
      Content:
        - Detection methods
        - Containment procedures
        - Investigation steps
        - Customer notification
        - Post-incident analysis
```

**Deliverables:**
- Vault for secrets management
- Image signing with Cosign
- Audit logging enabled
- Security controls documented
- Incident response plan

**Success Criteria:**
- No hardcoded secrets in code
- All images signed before deployment
- Audit logs capture sensitive actions
- Team knows security controls
- Incident response tested

---

## Success Metrics (Week 8)

```yaml
Goal: Move from 7.1/10 → 7.8/10

Criteria:

Phase 1: Disaster Recovery (✓ Complete)
  ├─ Daily automated backups: YES
  ├─ Tested restoration: YES
  ├─ RTO/RPO defined: YES (1-4 hours)
  ├─ Runbooks written: YES (6+)
  └─ Impact: 🟢 Data loss eliminated

Phase 2: CI/CD Automation (✓ Complete)
  ├─ Automated tests run: YES
  ├─ Security scanning: YES
  ├─ Automated deployments: YES (staging)
  ├─ Manual approval (prod): YES
  └─ Impact: 🟢 Deployment errors reduced 90%

Phase 3: Monitoring (✓ Complete)
  ├─ Prometheus metrics: YES
  ├─ Grafana dashboards: YES
  ├─ Alert rules: YES (10+)
  ├─ Per-tenant visibility: YES
  └─ Impact: 🟢 MTTR reduced 50%

Phase 4: Security (✓ Complete)
  ├─ Secrets management: YES
  ├─ Image signing: YES
  ├─ Audit logging: YES
  ├─ Documentation: YES
  └─ Impact: 🟢 Security posture improved

Infrastructure Score Before: 7.1/10
Infrastructure Score After: 7.8/10
Improvement: +0.7 points (+10%)
```

---

## Resource Requirements

```yaml
Team:
  ├─ DevOps Engineer: 50% (3+ weeks)
  ├─ Backend Lead: 30% (2 weeks)
  ├─ Frontend Lead: 10% (1 week)
  ├─ Security Engineer: 25% (1 week)
  └─ CTO/Engineering Lead: 20% (oversight)

Total Effort: ~240 hours

Timeline: 8 weeks (20 hours/week average)

Cost (assuming $75/hour):
  ├─ Labor: 240 hours × $75 = $18,000
  ├─ Tools: $0-500/month (mostly free)
  └─ Total Investment: $18,000-20,000

ROI:
  ├─ Reduced downtime: -$5K/month
  ├─ Faster deployments: -2 hours/week ($1.5K/month)
  ├─ Better security: Risk reduction
  └─ Payback period: 2-3 months
```

---

## Risk Management

```yaml
Risks & Mitigation:

Risk 1: CI/CD breaks deployments
  Mitigation:
    ├─ Test on staging first
    ├─ Slow rollout (10% → 50% → 100%)
    ├─ Quick rollback (< 5 min)
    └─ Keep Swarm available

Risk 2: Backup restoration fails
  Mitigation:
    ├─ Test every month
    ├─ Keep 30 days of backups
    ├─ Multiple backup locations
    └─ Document procedures

Risk 3: Monitoring becomes noise (alert fatigue)
  Mitigation:
    ├─ Tune alerts aggressively
    ├─ Start with critical only
    ├─ Weekly review of alert quality
    └─ Disable low-signal alerts

Risk 4: Secrets leak from Vault
  Mitigation:
    ├─ RBAC on Vault access
    ├─ Audit all secret access
    ├─ Rotate secrets monthly
    ├─ Enable encryption at rest
    └─ MFA for production access

Risk 5: Implementation takes longer
  Mitigation:
    ├─ Start with MVP (monitoring alone)
    ├─ Parallel implementation (DR + CI/CD)
    ├─ Use third-party services (StatusPage, Vault Cloud)
    └─ Adjust timeline as needed
```

---

## Sign-Off Checklist

**By end of Week 8:**

```
PHASE 1 - DISASTER RECOVERY
  [ ] Daily automated backups running
  [ ] Restoration tested monthly
  [ ] RTO/RPO targets documented
  [ ] 6+ runbooks available
  [ ] Team trained on procedures
  [ ] Monthly drill scheduled

PHASE 2 - CI/CD AUTOMATION
  [ ] GitHub Actions workflow live
  [ ] All tests passing
  [ ] Security scanning enabled
  [ ] Blue-green deployment working
  [ ] Manual approval for prod
  [ ] Rollback tested

PHASE 3 - MONITORING
  [ ] Prometheus collecting metrics
  [ ] Grafana dashboards visible
  [ ] Alert rules firing correctly
  [ ] Slack integration working
  [ ] Per-tenant metrics available
  [ ] SLA targets documented

PHASE 4 - SECURITY
  [ ] Vault deployed and tested
  [ ] No hardcoded secrets in code
  [ ] Images signed and verified
  [ ] Audit logging enabled
  [ ] Security documentation complete
  [ ] Incident response plan written

INFRASTRUCTURE SCORE
  Before: 7.1/10
  After: 7.8/10
  Improvement: +10%
  Status: ✅ PRODUCTION READY

Sign-Off:
  ├─ CTO: ______________
  ├─ DevOps Lead: ______________
  ├─ Security Lead: ______________
  └─ Product Lead: ______________
```

---

*This action plan ensures your platform meets enterprise requirements before scaling to 100+ tenants.*

*Prepared: 2025-12-07*
*Target Completion: 2026-01-31*
