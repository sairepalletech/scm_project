# SCM Project - Enterprise Architecture

## Executive Summary

**Vision**: Transform scm_project from a simple configuration management tool into a scalable, secure, extensible enterprise platform that orchestrates and reconciles state across SCM and adjacent tools through a declarative workflow DSL and modular plugin system.

**Positioning**: A control plane + agents platform (similar to Ansible/Chef) that integrates with 100+ external systems across SCM, CI/CD, cloud, security, observability, and ITSM domains.

**North Star**: Enterprise-grade reliability (HA, DR, RBAC), easy to extend (stable plugin SPI/SDK), and delightful developer experience (CLI + UI + well-documented APIs).

## Key Tenets

1. **Idempotency**: All operations produce consistent results regardless of how many times they're executed
2. **Auditability**: Complete audit trail of all operations and changes
3. **Backwards Compatibility**: Evolutionary architecture that maintains compatibility
4. **Supply Chain Security**: Signed artifacts, SBOM, provenance attestations
5. **Vendor Neutrality**: Integration packaging via OCI/WASM standards

## Reference Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Control Plane                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ API Gateway  │  │ Orchestrator │  │    Policy    │          │
│  │ GraphQL+REST │  │  & Scheduler │  │   Engine     │          │
│  └──────────────┘  └──────────────┘  │   (OPA)      │          │
│  ┌──────────────┐  ┌──────────────┐  └──────────────┘          │
│  │  SSO/OIDC    │  │     RBAC     │  ┌──────────────┐          │
│  │   + SAML     │  │   / ABAC     │  │    Plugin    │          │
│  └──────────────┘  └──────────────┘  │   Registry   │          │
│  ┌──────────────┐  ┌──────────────┐  └──────────────┘          │
│  │    Audit     │  │    Web UI    │                             │
│  │   / Events   │  │              │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Event Fabric                             │
│                    NATS / Kafka Message Bus                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Data Plane                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Runner Pool  │  │ Runner Pool  │  │    Plugin    │          │
│  │      A       │  │      B       │  │     Host     │          │
│  │              │  │              │  │  (gRPC/WASM) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Shared Infrastructure                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Postgres   │  │    Redis     │  │  S3/OCI Reg  │          │
│  │  (metadata)  │  │   (queues)   │  │  (artifacts) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                    ┌──────────────┐                              │
│                    │  ClickHouse  │                              │
│                    │ (analytics)  │                              │
│                    └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Models

#### 1. Kubernetes (Production - HA)
- Multi-replica API/Orchestrator with HPA
- PodDisruptionBudgets for high availability
- Horizontal pod autoscaling
- Multi-AZ deployment

#### 2. Single-Node / Air-Gapped
- Docker Compose setup
- Built-in OCI cache/mirror
- Offline plugin bundles
- Suitable for edge/development

#### 3. Multi-Tenant
- Organization → Project → Environment hierarchy
- Per-tenant RBAC and resource quotas
- Namespace isolation in Kubernetes
- Separate encryption keys per tenant

## Domain Model

### Core Entities

**Organization** → **Project** → **Environment** (dev/stage/prod)

**Workflow**: Declarative specification (YAML/JSON) describing desired operations
- Triggers (manual, cron, webhook, SCM events)
- Steps (sequence of actions)
- Conditionals and loops
- Handlers and notifications

**Run/Job/Step**: Execution instances
- Retry policies with exponential backoff
- Idempotency keys
- Artifact links
- Status tracking

**Integration**: Registered connector
- Name (e.g., GitHub, GitLab, Jenkins, AWS)
- Version (semantic versioning)
- Capabilities (list of supported actions)
- Configuration schema

**Credential**: External secret reference
- Vault/KMS/Secrets Manager integration
- Never stored in plain text
- Automatic rotation support

**Policy**: OPA/Rego policies
- Attached to org/project/workflow
- Admission control
- Validation rules

**Audit Event**: Immutable log entries
- Append-only storage
- Exportable to SIEM systems
- Tamper-evident

## Security Architecture

### Authentication
- OIDC/SAML SSO integration
- Service accounts with short-lived tokens
- SPIFFE/SPIRE for workload identity

### Authorization
- Hierarchical RBAC/ABAC
- Fine-grained resource scopes
- Least-privilege defaults
- Policy-based access control

### Secrets Management
- Externalized via Vault/AWS Secrets Manager/Azure Key Vault/GCP Secret Manager
- Never log secrets
- Automatic redaction in logs and audit trails
- Rotation hooks

### Supply Chain Security
- Signed releases with cosign
- SBOM (Software Bill of Materials) for core + plugins
- Provenance attestations
- SLSA compliance (Level 3+)

### Runtime Security
- Pod security policies / AppArmor
- Seccomp profiles
- WASM sandbox for untrusted plugins
- Network policies

### Threat Model (STRIDE)

| Threat | Mitigation |
|--------|-----------|
| **Spoofing** | mTLS with SPIRE; JWT validation; webhook signatures |
| **Tampering** | Immutability in audit store; signed artifacts |
| **Repudiation** | End-to-end request IDs; non-repudiation via signatures |
| **Information Disclosure** | Field-level encryption; secret redaction; scoped logs |
| **Denial of Service** | Backpressure, quotas, rate limits, circuit breakers |
| **Elevation of Privilege** | Privilege separation, capability-scoped plugins |

## Reliability & Performance

### Workload Model
- Millions of small API operations
- High fan-out scenarios
- At-least-once semantics with idempotency keys

### Scheduler
- Fair-share scheduling
- Per-tenant quotas
- Priority classes
- Work-stealing runners

### Backpressure & Rate Limiting
- Token buckets per integration
- Adaptive concurrency control
- Circuit-breaker patterns
- External API quota management

### Caching
- Read-through cache (Redis) for metadata
- ETags/If-None-Match for third-party APIs
- Intelligent cache invalidation

### High Availability / Disaster Recovery
- Multi-AZ deployment
- Optional multi-region (active-passive)
- Point-in-time recovery for Postgres
- Object store replication
- Automated backups

### Initial Sizing Guidelines

For **10k workflows/day** and **1M API calls**:
- 3 API pods (4 vCPU/8GB each)
- 5 runner pods (8 vCPU/16GB each)
- Redis 2-node cluster
- Postgres HA (3 replicas)

## Observability

### Metrics
- OpenTelemetry → Prometheus/Grafana
- SLOs for latency and success rates
- Custom business metrics

### Tracing
- Distributed tracing to plugin calls
- Baggage for tenant/project context
- Integration with Jaeger/Zipkin

### Logging
- Structured JSON logs
- Automatic secret redaction
- Correlation IDs
- Centralized aggregation

### Dashboards
- Workflow health metrics
- Plugin error rates
- Queue depth monitoring
- External API quota usage

## API Surface

### REST API (OpenAPI)
```
POST   /api/v1/workflows:plan      # Preview workflow changes
POST   /api/v1/workflows:apply     # Execute workflow
GET    /api/v1/runs/{id}           # Get run status
POST   /api/v1/integrations        # Register/configure integration
GET    /api/v1/plugins             # Browse plugin catalog
POST   /api/v1/tokens              # Manage service accounts
GET    /api/v1/audit               # Query audit logs
```

### gRPC API
- High-performance internal communication
- Plugin communication protocol
- Streaming for logs and events

### GraphQL API (Optional)
- Flexible queries for UI
- Real-time subscriptions
- Optimized data fetching

### Event Topics
```
runs.created
runs.completed
runs.failed
plugins.health
quota.warn
policy.violation
```

## Migration Path from Current State

### Current Capabilities (v1.0.0)
- Simple CLI tool
- Ubuntu-focused configuration management
- Resources: SERVICE, FILE, DIRECTORY, FIREWALL
- TOML-based recipe format
- Local execution model

### Evolution Strategy
1. **Maintain backward compatibility** with existing TOML recipes
2. **Introduce plugin system** as extension, not replacement
3. **Gradual migration** of core resources to plugin model
4. **Deprecation policy** with long support windows
5. **Bridge mode** allowing mixed old/new style configurations

### Compatibility Layer
```python
# Old style (continue to work)
[service.setup]
name = ["apache2"]
action = ["install", "enable"]

# New style (introduced gradually)
apiVersion: workflows.scm.dev/v1
kind: Workflow
steps:
  - uses: service.package:install
    with:
      name: apache2
```

## Next Steps

See [ROADMAP.md](ROADMAP.md) for detailed implementation phases and timelines.
See [docs/plugins/PLUGIN_SYSTEM.md](docs/plugins/PLUGIN_SYSTEM.md) for plugin architecture details.
