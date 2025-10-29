# Kubernetes Orchestration Design for Digital Signage System

## Executive Summary

### Current State Analysis
- **Current Setup**: Single server (192.168.5.12) running Docker Compose
- **Scale**: 1000-10000 devices with WebSocket connections
- **Workload Types**:
  - Stateless APIs (FastAPI backend)
  - Stateful services (PostgreSQL, Redis)
  - CPU-intensive batch jobs (video transcoding)
  - Long-lived connections (WebSocket service)
  - Large file storage (500MB-2GB videos)

### Migration Recommendation: **STAGED APPROACH**

**Phase 1 (Current - 6 months)**: Continue with Docker Compose
- Current scale doesn't justify Kubernetes complexity
- Single server is handling the load
- Focus on optimizing current architecture

**Phase 2 (6-12 months)**: Kubernetes-ready Architecture
- Refactor services for cloud-native patterns
- Implement proper health checks and graceful shutdowns
- Externalize all configuration
- Prepare stateless services

**Phase 3 (12+ months)**: Migrate to Kubernetes when:
- Device count exceeds 5000 active connections
- Need multi-node scaling
- Require zero-downtime deployments
- Need geographic distribution

## 1. Kubernetes Architecture Overview

### Proposed Cluster Architecture

```yaml
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Control Plane                        │  │
│  │  (3 master nodes for HA)                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Worker Node Pool 1 (General)            │  │
│  │  - API Services (3-5 nodes)                          │  │
│  │  - WebSocket Service                                 │  │
│  │  - Web Admin                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Worker Node Pool 2 (Transcoding)             │  │
│  │  - Celery Workers (2-4 nodes, high CPU)              │  │
│  │  - Auto-scaling based on queue depth                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Worker Node Pool 3 (Stateful)               │  │
│  │  - PostgreSQL (3 nodes - 1 primary, 2 replicas)      │  │
│  │  - Redis Cluster (3 nodes minimum)                   │  │
│  │  - File Storage (MinIO/NFS)                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Namespace Strategy

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: signage-prod
  labels:
    environment: production
    team: platform
---
apiVersion: v1
kind: Namespace
metadata:
  name: signage-staging
  labels:
    environment: staging
    team: platform
---
apiVersion: v1
kind: Namespace
metadata:
  name: signage-monitoring
  labels:
    environment: production
    team: platform
```

## 2. Service Manifests

### 2.1 Backend API Service (Deployment)

```yaml
# backend-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
  namespace: signage-prod
  labels:
    app: backend-api
    tier: backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
        tier: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8001"
        prometheus.io/path: "/metrics"
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - backend-api
              topologyKey: kubernetes.io/hostname
      containers:
      - name: backend-api
        image: signage/backend-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8001
          name: http
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: connection-string
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: connection-string
        - name: AWS_S3_BUCKET
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: s3-bucket
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: backend-api
  namespace: signage-prod
  labels:
    app: backend-api
spec:
  type: ClusterIP
  ports:
  - port: 8001
    targetPort: 8001
    protocol: TCP
    name: http
  selector:
    app: backend-api
```

### 2.2 WebSocket Service (Deployment with Session Affinity)

```yaml
# websocket-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: websocket-service
  namespace: signage-prod
  labels:
    app: websocket
    tier: realtime
spec:
  replicas: 5  # Start with 5 for 10,000 devices (2000 per pod)
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: websocket
  template:
    metadata:
      labels:
        app: websocket
        tier: realtime
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8002"
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - websocket
            topologyKey: kubernetes.io/hostname
      containers:
      - name: websocket
        image: signage/websocket:latest
        ports:
        - containerPort: 8002
          name: ws
          protocol: TCP
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: connection-string
        - name: MAX_CONNECTIONS_PER_POD
          value: "2000"
        - name: ENABLE_STICKY_SESSIONS
          value: "true"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8002
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: websocket
  namespace: signage-prod
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  sessionAffinity: ClientIP  # Important for WebSocket
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 86400  # 24 hours
  ports:
  - port: 8002
    targetPort: 8002
    protocol: TCP
    name: websocket
  selector:
    app: websocket
```

### 2.3 Celery Workers (Deployment with KEDA Autoscaling)

```yaml
# celery-workers-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-transcoding-workers
  namespace: signage-prod
  labels:
    app: celery-transcoding
    tier: workers
spec:
  replicas: 2  # Base replicas, KEDA will scale
  selector:
    matchLabels:
      app: celery-transcoding
  template:
    metadata:
      labels:
        app: celery-transcoding
        tier: workers
    spec:
      nodeSelector:
        workload: transcoding  # Use dedicated high-CPU nodes
      tolerations:
      - key: "workload"
        operator: "Equal"
        value: "transcoding"
        effect: "NoSchedule"
      containers:
      - name: celery-worker
        image: signage/celery-worker:latest
        command: ["celery", "-A", "app.tasks", "worker", "--loglevel=info", "--concurrency=2"]
        env:
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: celery-broker-url
        - name: CELERY_RESULT_BACKEND
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: celery-result-backend
        - name: S3_BUCKET
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: s3-bucket
        - name: TRANSCODING_PRESET
          value: "hls-1080p"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"  # 2 full cores for transcoding
          limits:
            memory: "8Gi"
            cpu: "4000m"  # 4 cores max
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp/transcoding
        - name: shared-storage
          mountPath: /mnt/videos
      volumes:
      - name: temp-storage
        emptyDir:
          sizeLimit: 20Gi  # Local SSD for transcoding
      - name: shared-storage
        persistentVolumeClaim:
          claimName: video-storage-pvc
---
# KEDA ScaledObject for queue-based autoscaling
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-transcoding-scaler
  namespace: signage-prod
spec:
  scaleTargetRef:
    name: celery-transcoding-workers
  minReplicaCount: 1
  maxReplicaCount: 10
  pollingInterval: 30
  cooldownPeriod: 300
  triggers:
  - type: redis
    metadata:
      address: redis-cluster:6379
      listName: celery:transcoding:queue
      listLength: "2"  # Scale up when > 2 jobs in queue
      enableTLS: "false"
    authenticationRef:
      name: redis-auth
```

### 2.4 PostgreSQL (StatefulSet with Replication)

```yaml
# postgresql-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: signage-prod
spec:
  serviceName: postgresql
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_REPLICATION_MODE
          value: "master"
        - name: POSTGRES_REPLICATION_USER
          value: "replicator"
        - name: POSTGRES_REPLICATION_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: replication-password
        - name: POSTGRES_USER
          value: "signage"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: POSTGRES_DB
          value: "signage"
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: postgres-config
          mountPath: /etc/postgresql
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U signage
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U signage
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: signage-prod
spec:
  type: ClusterIP
  clusterIP: None  # Headless service for StatefulSet
  ports:
  - port: 5432
    targetPort: 5432
    protocol: TCP
  selector:
    app: postgresql
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql-primary
  namespace: signage-prod
spec:
  type: ClusterIP
  ports:
  - port: 5432
    targetPort: 5432
    protocol: TCP
  selector:
    app: postgresql
    role: master
```

### 2.5 Redis Cluster (StatefulSet)

```yaml
# redis-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: signage-prod
spec:
  serviceName: redis-cluster
  replicas: 6  # 3 masters + 3 replicas
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server"]
        args:
        - "/etc/redis/redis.conf"
        - "--protected-mode"
        - "no"
        - "--cluster-enabled"
        - "yes"
        - "--cluster-config-file"
        - "/data/nodes.conf"
        - "--cluster-node-timeout"
        - "5000"
        - "--appendonly"
        - "yes"
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
        - name: redis-config
          mountPath: /etc/redis
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 10Gi
```

## 3. Horizontal Pod Autoscaling (HPA) Configuration

### 3.1 Backend API HPA

```yaml
# backend-api-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
  namespace: signage-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
```

### 3.2 WebSocket Service HPA

```yaml
# websocket-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: websocket-hpa
  namespace: signage-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: websocket-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Pods
    pods:
      metric:
        name: websocket_connections
      target:
        type: AverageValue
        averageValue: "1500"  # Scale when avg connections > 1500 per pod
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 600  # Slower scale down for persistent connections
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

## 4. Storage Strategy

### 4.1 Storage Classes

```yaml
# storage-classes.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "10000"
  throughput: "250"
  encrypted: "true"
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: bulk-storage
provisioner: kubernetes.io/aws-efs
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-xxxxxx
  directoryPerms: "700"
mountOptions:
- hard
- nfsvers=4.1
- rsize=1048576
- wsize=1048576
allowVolumeExpansion: true
volumeBindingMode: Immediate
```

### 4.2 Persistent Volume Claims

```yaml
# video-storage-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: video-storage-pvc
  namespace: signage-prod
spec:
  accessModes:
    - ReadWriteMany  # Multiple pods need access
  storageClassName: bulk-storage
  resources:
    requests:
      storage: 5Ti  # 5TB for video storage
---
# Database backup PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-backup-pvc
  namespace: signage-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 200Gi
```

## 5. Network Policies

### 5.1 Service Isolation

```yaml
# network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-api-netpol
  namespace: signage-prod
spec:
  podSelector:
    matchLabels:
      app: backend-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: signage-prod
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8001
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis-cluster
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-isolation
  namespace: signage-prod
spec:
  podSelector:
    matchLabels:
      app: postgresql
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    - podSelector:
        matchLabels:
          tier: workers
    ports:
    - protocol: TCP
      port: 5432
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: redis-isolation
  namespace: signage-prod
spec:
  podSelector:
    matchLabels:
      app: redis-cluster
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    - podSelector:
        matchLabels:
          tier: workers
    - podSelector:
        matchLabels:
          tier: realtime
    ports:
    - protocol: TCP
      port: 6379
  - from:
    - podSelector:
        matchLabels:
          app: redis-cluster
    ports:
    - protocol: TCP
      port: 16379  # Cluster gossip
```

## 6. Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: signage-ingress
  namespace: signage-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "2048m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
spec:
  tls:
  - hosts:
    - api.signage.example.com
    - ws.signage.example.com
    - admin.signage.example.com
    secretName: signage-tls
  rules:
  - host: api.signage.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-api
            port:
              number: 8001
  - host: ws.signage.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: websocket
            port:
              number: 8002
  - host: admin.signage.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-admin
            port:
              number: 3000
```

## 7. Secrets Management

### 7.1 Using External Secrets Operator

```yaml
# external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: signage-prod
spec:
  provider:
    vault:
      server: "https://vault.example.com:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "signage-prod"
          serviceAccountRef:
            name: "external-secrets"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: signage-prod
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: signage/database
      property: password
  - secretKey: connection-string
    remoteRef:
      key: signage/database
      property: connection_string
```

### 7.2 Sealed Secrets Alternative

```yaml
# sealed-secret.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: database-secret
  namespace: signage-prod
spec:
  encryptedData:
    password: AgBy8BFY3I...  # Encrypted value
    connection-string: AgXY9ZKL2M...  # Encrypted value
  template:
    metadata:
      name: database-secret
      namespace: signage-prod
    type: Opaque
```

## 8. Service Mesh Configuration (Optional - Istio)

```yaml
# istio-service-mesh.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: backend-api-vs
  namespace: signage-prod
spec:
  hosts:
  - backend-api
  http:
  - match:
    - headers:
        x-version:
          exact: v2
    route:
    - destination:
        host: backend-api
        subset: v2
      weight: 100
  - route:
    - destination:
        host: backend-api
        subset: v1
      weight: 90
    - destination:
        host: backend-api
        subset: v2
      weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: backend-api-dr
  namespace: signage-prod
spec:
  host: backend-api
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 100
    loadBalancer:
      simple: LEAST_REQUEST
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
---
# Circuit breaker
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: backend-api-circuit-breaker
  namespace: signage-prod
spec:
  host: backend-api
  trafficPolicy:
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
```

## 9. Monitoring Stack

### 9.1 Prometheus Configuration

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: signage-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - signage-prod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

    - job_name: 'celery-workers'
      static_configs:
      - targets: ['celery-exporter:9540']

    - job_name: 'postgresql'
      static_configs:
      - targets: ['postgres-exporter:9187']

    - job_name: 'redis'
      static_configs:
      - targets: ['redis-exporter:9121']
```

### 9.2 Grafana Dashboards

```yaml
# grafana-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: signage-monitoring
data:
  signage-overview.json: |
    {
      "dashboard": {
        "title": "Digital Signage Overview",
        "panels": [
          {
            "title": "Active Devices",
            "targets": [{
              "expr": "sum(websocket_active_connections)"
            }]
          },
          {
            "title": "Transcoding Queue Depth",
            "targets": [{
              "expr": "celery_queue_length{queue='transcoding'}"
            }]
          },
          {
            "title": "API Request Rate",
            "targets": [{
              "expr": "rate(http_requests_total[5m])"
            }]
          },
          {
            "title": "Database Connections",
            "targets": [{
              "expr": "pg_stat_database_numbackends"
            }]
          }
        ]
      }
    }
```

## 10. Migration Strategy from Docker Compose

### Phase 1: Preparation (Current State)
```yaml
# Current docker-compose.yml analysis
services:
  backend-api:
    complexity: LOW
    stateless: YES
    migration_difficulty: EASY

  postgres:
    complexity: HIGH
    stateless: NO
    migration_difficulty: HARD
    considerations:
      - Data migration required
      - Backup strategy needed
      - Replication setup

  redis:
    complexity: MEDIUM
    stateless: SEMI
    migration_difficulty: MEDIUM
    considerations:
      - Session data migration
      - Cluster setup required
```

### Phase 2: Migration Plan

```bash
# Step 1: Set up Kubernetes cluster
eksctl create cluster \
  --name signage-cluster \
  --region us-west-2 \
  --nodes 3 \
  --node-type t3.xlarge \
  --nodes-min 3 \
  --nodes-max 10

# Step 2: Install required operators
helm repo add jetstack https://charts.jetstack.io
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace
helm install ingress-nginx ingress-nginx/ingress-nginx
helm install keda bitnami/keda --namespace keda --create-namespace

# Step 3: Create namespaces
kubectl create namespace signage-prod
kubectl create namespace signage-staging
kubectl create namespace signage-monitoring

# Step 4: Deploy monitoring first
kubectl apply -f monitoring/

# Step 5: Deploy stateful services
kubectl apply -f storage-classes.yaml
kubectl apply -f postgresql/
kubectl apply -f redis/

# Step 6: Migrate data
# Run migration job
kubectl apply -f migration-job.yaml

# Step 7: Deploy stateless services
kubectl apply -f backend-api/
kubectl apply -f websocket/
kubectl apply -f celery-workers/

# Step 8: Configure ingress
kubectl apply -f ingress.yaml

# Step 9: Test and validate
kubectl get pods -n signage-prod
kubectl logs -n signage-prod -l app=backend-api
```

## 11. Cost Analysis

### Docker Compose (Current)
```
Single Server (192.168.5.12):
- Server: $200-500/month
- Bandwidth: $50-100/month
- Storage: $50/month
- Total: ~$300-650/month

Pros:
✅ Simple management
✅ Low cost
✅ Easy debugging
✅ Fast deployment

Cons:
❌ Single point of failure
❌ No auto-scaling
❌ Manual updates
❌ Limited monitoring
```

### Kubernetes (Proposed)
```
AWS EKS Cluster:
- Control Plane: $72/month
- Worker Nodes (3x t3.xlarge): $375/month
- Load Balancers: $50/month
- Storage (EBS + EFS): $200/month
- Data Transfer: $100/month
- Monitoring (CloudWatch): $50/month
- Total: ~$850-1000/month

Pros:
✅ High availability
✅ Auto-scaling
✅ Zero-downtime deployments
✅ Advanced monitoring
✅ Geographic distribution
✅ Enterprise features

Cons:
❌ Higher complexity
❌ Higher cost (2-3x)
❌ Steeper learning curve
❌ More components to manage
```

## 12. Decision Matrix

| Factor | Docker Compose | Kubernetes | Winner |
|--------|---------------|------------|---------|
| **Cost** | $300-650/mo | $850-1000/mo | Docker Compose |
| **Complexity** | Low | High | Docker Compose |
| **Scalability** | Manual | Automatic | Kubernetes |
| **Availability** | 99% | 99.95% | Kubernetes |
| **Deployment Speed** | Fast | Moderate | Docker Compose |
| **Monitoring** | Basic | Advanced | Kubernetes |
| **Team Skills Required** | Low | High | Docker Compose |
| **Geographic Distribution** | No | Yes | Kubernetes |
| **Zero-downtime Updates** | Manual | Automatic | Kubernetes |
| **Disaster Recovery** | Manual | Automated | Kubernetes |

## 13. Final Recommendation

### Stay with Docker Compose IF:
- ✅ Current load < 5000 devices
- ✅ Single region operation
- ✅ 99% uptime is acceptable
- ✅ Budget conscious
- ✅ Small team (1-3 people)
- ✅ Simple deployment needs

### Migrate to Kubernetes WHEN:
- 📈 Load > 5000 concurrent devices
- 🌍 Multi-region requirements
- ⚡ Need 99.95%+ uptime
- 🚀 Auto-scaling critical
- 👥 Team > 3 engineers
- 🔄 Complex deployment patterns
- 📊 Advanced monitoring required

## 14. Optimization for Current Docker Compose

If staying with Docker Compose, implement these improvements:

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  backend-api:
    image: signage/backend-api:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend-api
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 256M

  postgres:
    image: postgres:14-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres-backup:/backup
    environment:
      POSTGRES_REPLICATION_MODE: master
      POSTGRES_REPLICATION_USER: replicator
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    restart: unless-stopped

  postgres-replica:
    image: postgres:14-alpine
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_HOST: postgres
    depends_on:
      - postgres
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    restart: unless-stopped

  celery-worker:
    image: signage/celery-worker:latest
    command: celery -A app.tasks worker --concurrency=2
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
    volumes:
      - video_storage:/mnt/videos
    restart: unless-stopped

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  video_storage:
  prometheus_data:
  grafana_data:
```

## 15. Monitoring Setup for Docker Compose

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend-api:8001']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

## Conclusion

For your current scale (1000-10000 devices on a single server), **Docker Compose remains the optimal choice**. The complexity and cost of Kubernetes aren't justified until you need:

1. **True multi-node scaling** (beyond single server capacity)
2. **Geographic distribution** (multiple regions)
3. **99.95%+ uptime requirements**
4. **Complex traffic management** (canary, blue-green)
5. **Team growth** requiring standardized platform

### Recommended Action Plan:

1. **Short term (0-6 months)**:
   - Optimize current Docker Compose setup
   - Add monitoring with Prometheus/Grafana
   - Implement backup strategies
   - Add nginx load balancing

2. **Medium term (6-12 months)**:
   - Prepare services for Kubernetes (12-factor app)
   - Implement proper health checks
   - Externalize configuration
   - Build CI/CD pipelines

3. **Long term (12+ months)**:
   - Evaluate actual growth metrics
   - If exceeding single server capacity, begin Kubernetes migration
   - Start with stateless services
   - Gradually migrate stateful services

The key is to **avoid premature optimization**. Kubernetes is powerful but adds significant operational overhead that's not justified for your current scale.