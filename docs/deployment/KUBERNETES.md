# Kubernetes Deployment Guide

## Overview

This guide covers deploying SCM Platform on Kubernetes for enterprise production environments with high availability, scalability, and security.

## Prerequisites

- Kubernetes cluster 1.24+
- Helm 3.8+
- kubectl configured
- Storage class for persistent volumes
- External PostgreSQL (recommended) or in-cluster
- External Redis (recommended) or in-cluster
- Object storage (S3, MinIO, GCS, Azure Blob)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Ingress Controller                       │  │
│  │              (NGINX/Traefik/ALB)                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Control Plane (StatefulSet/Deployment)     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │   API    │  │   API    │  │   API    │          │  │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Runner Pools (Deployment + HPA)            │  │
│  │  ┌──────────┐  ┌──────────┐        ┌──────────┐    │  │
│  │  │ Runner 1 │  │ Runner 2 │  ...   │ Runner N │    │  │
│  │  └──────────┘  └──────────┘        └──────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────────┐          ┌─────────┐         ┌──────────┐
    │Postgres│          │  Redis  │         │ S3/Minio │
    │   DB   │          │ (Queue) │         │(Artifacts)│
    └────────┘          └─────────┘         └──────────┘
```

## Quick Start

### 1. Add Helm Repository

```bash
helm repo add scm https://charts.scm.dev
helm repo update
```

### 2. Create Namespace

```bash
kubectl create namespace scm-platform
```

### 3. Install with Default Values

```bash
helm install scm scm/scm-platform \
  --namespace scm-platform \
  --create-namespace
```

### 4. Verify Installation

```bash
kubectl get pods -n scm-platform
kubectl get svc -n scm-platform
```

## Production Configuration

### Helm Values File

Create `values-production.yaml`:

```yaml
# Global Settings
global:
  domain: scm.example.com
  environment: production

# Control Plane
controlPlane:
  replicas: 3
  image:
    repository: ghcr.io/scm/platform
    tag: v2.0.0
    pullPolicy: IfNotPresent
  
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
  
  podDisruptionBudget:
    enabled: true
    minAvailable: 2
  
  # OIDC Configuration
  auth:
    oidc:
      enabled: true
      issuerURL: https://auth.example.com/
      clientID: scm-platform
      clientSecret:
        existingSecret: oidc-credentials
        key: client-secret
      groupsClaim: groups
      scopes: [openid, profile, email, groups]
  
  # RBAC
  rbac:
    enabled: true
    roles:
      - name: admin
        permissions: ["*"]
      - name: developer
        permissions: ["workflows:read", "workflows:execute", "plugins:read"]
      - name: viewer
        permissions: ["workflows:read", "runs:read"]

# Runner Pools
runners:
  pools:
    - name: default
      replicas: 5
      resources:
        requests:
          cpu: 1000m
          memory: 2Gi
        limits:
          cpu: 2000m
          memory: 4Gi
      autoscaling:
        enabled: true
        minReplicas: 5
        maxReplicas: 20
        targetCPUUtilizationPercentage: 75
    
    - name: high-memory
      replicas: 2
      resources:
        requests:
          cpu: 2000m
          memory: 8Gi
        limits:
          cpu: 4000m
          memory: 16Gi
      nodeSelector:
        workload-type: high-memory
      tolerations:
        - key: high-memory
          operator: Equal
          value: "true"
          effect: NoSchedule

# PostgreSQL (External)
postgresql:
  enabled: false  # Using external DB
  external:
    host: postgres.example.com
    port: 5432
    database: scm_platform
    username: scm_user
    password:
      existingSecret: postgres-credentials
      key: password
    sslMode: require
    maxConnections: 100

# Redis (External)
redis:
  enabled: false  # Using external Redis
  external:
    host: redis.example.com
    port: 6379
    password:
      existingSecret: redis-credentials
      key: password
    tls: true
    sentinels:
      enabled: true
      master: mymaster
      nodes:
        - redis-sentinel-1.example.com:26379
        - redis-sentinel-2.example.com:26379
        - redis-sentinel-3.example.com:26379

# Object Storage (S3)
objectStorage:
  type: s3  # s3, gcs, azure, minio
  s3:
    region: us-west-2
    bucket: scm-platform-artifacts
    endpoint: https://s3.us-west-2.amazonaws.com
    credentials:
      accessKeyId:
        existingSecret: s3-credentials
        key: access-key-id
      secretAccessKey:
        existingSecret: s3-credentials
        key: secret-access-key
  encryption:
    enabled: true
    kmsKeyId: arn:aws:kms:us-west-2:123456789:key/abc-123

# Plugin Registry
plugins:
  registry:
    type: oci  # oci, harbor, gitlab
    url: ghcr.io
    credentials:
      existingSecret: registry-credentials
  
  allowList:
    - ghcr.io/scm/plugins/*
    - ghcr.io/my-org/plugins/*
  
  verification:
    enabled: true
    publicKeys:
      - name: scm-official
        key: |
          -----BEGIN PUBLIC KEY-----
          MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
          -----END PUBLIC KEY-----

# Policy Engine (OPA)
policy:
  enabled: true
  opa:
    replicas: 2
    bundles:
      - url: s3://scm-policies/compliance.tar.gz
        polling:
          interval: 30s
    decision_logs:
      enabled: true
      plugin: s3
      config:
        bucket: scm-audit-logs
        region: us-west-2

# Observability
observability:
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
      interval: 30s
  
  tracing:
    enabled: true
    exporter: otlp
    endpoint: otel-collector.observability.svc:4317
  
  logging:
    level: info
    format: json
    outputs:
      - stdout
      - file: /var/log/scm/app.log

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: scm.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: scm-tls
      hosts:
        - scm.example.com

# Security
security:
  podSecurityPolicy:
    enabled: true
  
  networkPolicy:
    enabled: true
    ingress:
      - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
    egress:
      - to:
        - namespaceSelector: {}
        ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 5432  # PostgreSQL
        - protocol: TCP
          port: 6379  # Redis
  
  secretsManagement:
    provider: vault  # vault, aws-secrets-manager, azure-keyvault
    vault:
      address: https://vault.example.com
      role: scm-platform
      authMethod: kubernetes
      mountPath: /v1/secret/data/scm

# Backup & Restore
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention: 30d
  storage:
    s3:
      bucket: scm-platform-backups
      region: us-west-2
```

### Install with Production Values

```bash
helm install scm scm/scm-platform \
  --namespace scm-platform \
  --values values-production.yaml \
  --wait --timeout 10m
```

## High Availability Setup

### Multi-AZ Deployment

```yaml
controlPlane:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values:
                  - scm-control-plane
          topologyKey: topology.kubernetes.io/zone

runners:
  pools:
    - name: default
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: pool
                      operator: In
                      values:
                        - default
                topologyKey: topology.kubernetes.io/zone
```

### Pod Disruption Budgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: scm-control-plane-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: scm-control-plane
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: scm-runners-pdb
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: scm-runner
```

## Security Hardening

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: scm-control-plane-netpol
spec:
  podSelector:
    matchLabels:
      app: scm-control-plane
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
      - podSelector:
          matchLabels:
            app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
      - podSelector:
          matchLabels:
            app: redis
      ports:
        - protocol: TCP
          port: 6379
```

### Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: scm-platform
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### RBAC

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: scm-runner
  namespace: scm-platform
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["create", "get", "list", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: scm-runner-binding
  namespace: scm-platform
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: scm-runner
subjects:
  - kind: ServiceAccount
    name: scm-runner
    namespace: scm-platform
```

## Monitoring & Observability

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: scm-platform
  namespace: scm-platform
spec:
  selector:
    matchLabels:
      app: scm-control-plane
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

### Grafana Dashboards

Import pre-built dashboards:
- Platform Overview: `dashboards/platform-overview.json`
- Workflow Metrics: `dashboards/workflow-metrics.json`
- Plugin Performance: `dashboards/plugin-performance.json`

## Backup & Restore

### Manual Backup

```bash
kubectl exec -n scm-platform scm-control-plane-0 -- \
  /usr/local/bin/scm backup create \
  --output s3://scm-backups/manual-$(date +%Y%m%d-%H%M%S).tar.gz
```

### Restore from Backup

```bash
helm install scm scm/scm-platform \
  --namespace scm-platform \
  --values values-production.yaml \
  --set restore.enabled=true \
  --set restore.source=s3://scm-backups/backup-20251014.tar.gz
```

## Upgrades

### Rolling Update

```bash
# Update to new version
helm upgrade scm scm/scm-platform \
  --namespace scm-platform \
  --values values-production.yaml \
  --set controlPlane.image.tag=v2.1.0 \
  --wait

# Monitor rollout
kubectl rollout status deployment/scm-control-plane -n scm-platform
```

### Rollback

```bash
helm rollback scm -n scm-platform
```

## Troubleshooting

### Check Logs

```bash
# Control Plane logs
kubectl logs -n scm-platform -l app=scm-control-plane --tail=100

# Runner logs
kubectl logs -n scm-platform -l app=scm-runner --tail=100

# Follow logs
kubectl logs -n scm-platform -f deployment/scm-control-plane
```

### Debug Pod

```bash
kubectl debug -n scm-platform scm-control-plane-0 -it --image=busybox
```

### Check Resource Usage

```bash
kubectl top pods -n scm-platform
kubectl top nodes
```

## Scaling

### Manual Scaling

```bash
# Scale control plane
kubectl scale deployment scm-control-plane -n scm-platform --replicas=5

# Scale runners
kubectl scale deployment scm-runner-default -n scm-platform --replicas=10
```

### HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: scm-runner-default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: scm-runner-default
  minReplicas: 5
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## Cost Optimization

### Resource Requests/Limits Tuning

```yaml
# Right-size based on actual usage
resources:
  requests:
    cpu: 500m    # P50 usage
    memory: 1Gi  # P50 usage
  limits:
    cpu: 2000m   # P99 usage
    memory: 4Gi  # P99 usage
```

### Cluster Autoscaler

Enable cluster autoscaler for dynamic node provisioning based on pod resource requests.

### Spot/Preemptible Instances

```yaml
runners:
  pools:
    - name: batch
      replicas: 10
      tolerations:
        - key: cloud.google.com/gke-preemptible
          operator: Equal
          value: "true"
          effect: NoSchedule
      nodeSelector:
        cloud.google.com/gke-preemptible: "true"
```

## Next Steps

- Review [ARCHITECTURE.md](../../ARCHITECTURE.md) for design details
- See [SECURITY.md](../security/SECURITY.md) for security best practices
- Explore [MONITORING.md](./MONITORING.md) for observability setup
