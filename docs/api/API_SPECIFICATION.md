# API Specification

## Overview

SCM Platform exposes multiple API surfaces for different use cases:
- **REST API**: Human-friendly, CRUD operations, webhooks
- **gRPC API**: High-performance, internal services, plugin communication
- **GraphQL API**: Flexible queries, UI integration (optional)

## REST API (OpenAPI 3.0)

### Base URL

```
https://api.scm.example.com/api/v1
```

### Authentication

All requests require authentication via one of:

**Bearer Token** (recommended):
```http
Authorization: Bearer <token>
```

**API Key** (legacy):
```http
X-API-Key: <api_key>
```

### Common Headers

```http
Accept: application/json
Content-Type: application/json
X-Request-ID: <uuid>  # Optional, for tracing
X-Organization: <org>  # Optional, for multi-tenant contexts
```

### Resources

#### Workflows

**Create Workflow**
```http
POST /api/v1/workflows

{
  "name": "deploy-production",
  "description": "Deploy to production environment",
  "spec": {
    "triggers": [...],
    "steps": [...]
  }
}

Response: 201 Created
{
  "id": "wf-abc123",
  "name": "deploy-production",
  "version": 1,
  "created_at": "2025-10-14T10:30:00Z"
}
```

**List Workflows**
```http
GET /api/v1/workflows?org=acme&project=platform&page=1&per_page=50

Response: 200 OK
{
  "workflows": [
    {
      "id": "wf-abc123",
      "name": "deploy-production",
      "version": 3,
      "updated_at": "2025-10-14T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 127
  }
}
```

**Get Workflow**
```http
GET /api/v1/workflows/{id}

Response: 200 OK
{
  "id": "wf-abc123",
  "name": "deploy-production",
  "version": 3,
  "spec": { ... },
  "metadata": { ... }
}
```

**Update Workflow**
```http
PUT /api/v1/workflows/{id}

{
  "spec": { ... }
}

Response: 200 OK
```

**Delete Workflow**
```http
DELETE /api/v1/workflows/{id}

Response: 204 No Content
```

**Validate Workflow**
```http
POST /api/v1/workflows:validate

{
  "spec": { ... }
}

Response: 200 OK
{
  "valid": true,
  "errors": [],
  "warnings": ["Step 'deploy' has no retry configured"]
}
```

**Plan Workflow** (Dry-run)
```http
POST /api/v1/workflows/{id}:plan

{
  "inputs": {
    "environment": "staging"
  }
}

Response: 200 OK
{
  "plan_id": "plan-xyz789",
  "changes": [
    {
      "step": "deploy-app",
      "action": "kubernetes.deploy:apply",
      "resources": [
        {
          "type": "Deployment",
          "name": "api-server",
          "operation": "update"
        }
      ]
    }
  ]
}
```

**Execute Workflow**
```http
POST /api/v1/workflows/{id}:execute

{
  "inputs": {
    "environment": "staging"
  },
  "plan_id": "plan-xyz789"  # Optional, from plan step
}

Response: 202 Accepted
{
  "run_id": "run-def456",
  "status": "pending",
  "created_at": "2025-10-14T10:30:00Z"
}
```

#### Runs

**Get Run**
```http
GET /api/v1/runs/{id}

Response: 200 OK
{
  "id": "run-def456",
  "workflow_id": "wf-abc123",
  "status": "running",
  "progress": {
    "total_steps": 5,
    "completed_steps": 2,
    "current_step": "deploy-app"
  },
  "started_at": "2025-10-14T10:30:00Z",
  "estimated_completion": "2025-10-14T10:35:00Z"
}
```

**List Runs**
```http
GET /api/v1/runs?workflow_id=wf-abc123&status=running&page=1

Response: 200 OK
{
  "runs": [...],
  "pagination": { ... }
}
```

**Cancel Run**
```http
POST /api/v1/runs/{id}:cancel

Response: 200 OK
{
  "id": "run-def456",
  "status": "cancelled"
}
```

**Get Run Logs**
```http
GET /api/v1/runs/{id}/logs?step=deploy-app&tail=100

Response: 200 OK
{
  "logs": [
    {
      "timestamp": "2025-10-14T10:30:00Z",
      "level": "info",
      "message": "Deploying application...",
      "step": "deploy-app"
    }
  ]
}
```

**Stream Run Logs** (WebSocket)
```
ws://api.scm.example.com/api/v1/runs/{id}/logs/stream

Messages:
{
  "timestamp": "2025-10-14T10:30:00Z",
  "level": "info",
  "message": "Deployment complete"
}
```

#### Plugins

**List Plugins**
```http
GET /api/v1/plugins?category=scm&verified=true

Response: 200 OK
{
  "plugins": [
    {
      "name": "github",
      "version": "1.0.0",
      "description": "GitHub connector",
      "verified": true,
      "downloads": 12543,
      "rating": 4.8
    }
  ]
}
```

**Get Plugin**
```http
GET /api/v1/plugins/{name}?version=1.0.0

Response: 200 OK
{
  "name": "github",
  "version": "1.0.0",
  "manifest": { ... },
  "downloads": 12543,
  "published_at": "2025-01-15T00:00:00Z"
}
```

**Register Plugin**
```http
POST /api/v1/plugins

{
  "manifest_url": "https://ghcr.io/scm/plugins/github:1.0.0/manifest.yaml",
  "signature": "..."
}

Response: 201 Created
```

**Install Plugin**
```http
POST /api/v1/plugins/{name}/install

{
  "version": "1.0.0",
  "config": { ... }
}

Response: 200 OK
```

#### Integrations

**Configure Integration**
```http
POST /api/v1/integrations

{
  "plugin": "github",
  "name": "github-prod",
  "config": {
    "base_url": "https://api.github.com",
    "token": { "vault": "vault:kv/github/token" }
  }
}

Response: 201 Created
{
  "id": "int-ghi789",
  "name": "github-prod",
  "status": "active"
}
```

**List Integrations**
```http
GET /api/v1/integrations

Response: 200 OK
{
  "integrations": [...]
}
```

**Test Integration**
```http
POST /api/v1/integrations/{id}:test

Response: 200 OK
{
  "status": "healthy",
  "details": {
    "api_reachable": true,
    "rate_limit_remaining": 4500
  }
}
```

#### Audit

**Query Audit Logs**
```http
GET /api/v1/audit?actor=user-123&action=workflows:execute&from=2025-10-01&to=2025-10-14

Response: 200 OK
{
  "events": [
    {
      "id": "evt-abc123",
      "timestamp": "2025-10-14T10:30:00Z",
      "actor": {
        "type": "user",
        "id": "user-123",
        "email": "jane@example.com"
      },
      "action": "workflows:execute",
      "resource": {
        "type": "workflow",
        "id": "wf-abc123"
      },
      "result": "success"
    }
  ]
}
```

**Export Audit Logs**
```http
POST /api/v1/audit:export

{
  "format": "json",  # json, csv, parquet
  "from": "2025-10-01T00:00:00Z",
  "to": "2025-10-14T23:59:59Z",
  "destination": "s3://audit-exports/2025-10.json"
}

Response: 202 Accepted
{
  "export_id": "exp-xyz789",
  "status": "pending"
}
```

#### Authentication

**Create Service Account**
```http
POST /api/v1/auth/service-accounts

{
  "name": "ci-pipeline",
  "roles": ["automation"],
  "ttl": "24h"
}

Response: 201 Created
{
  "id": "sa-jkl012",
  "name": "ci-pipeline",
  "token": "scm_xxxxxxxxxx",
  "expires_at": "2025-10-15T10:30:00Z"
}
```

**Create API Key**
```http
POST /api/v1/auth/api-keys

{
  "name": "legacy-integration",
  "scopes": ["workflows:read", "workflows:execute"]
}

Response: 201 Created
{
  "id": "key-mno345",
  "key": "sk_live_xxxxxxxxxx"
}
```

**Revoke Token**
```http
DELETE /api/v1/auth/tokens/{id}

Response: 204 No Content
```

### Error Responses

**Standard Error Format**:
```json
{
  "error": {
    "code": "invalid_input",
    "message": "Workflow name is required",
    "details": {
      "field": "name",
      "reason": "missing_required_field"
    },
    "request_id": "req-abc123"
  }
}
```

**Common Error Codes**:
- `400` Bad Request - Invalid input
- `401` Unauthorized - Missing or invalid authentication
- `403` Forbidden - Insufficient permissions
- `404` Not Found - Resource not found
- `409` Conflict - Resource already exists
- `422` Unprocessable Entity - Validation failed
- `429` Too Many Requests - Rate limit exceeded
- `500` Internal Server Error - Server error
- `503` Service Unavailable - Temporary unavailability

### Rate Limiting

**Headers**:
```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4500
X-RateLimit-Reset: 1634216400
```

**Limits**:
- Authenticated: 5000 requests/hour
- Service Accounts: 10000 requests/hour
- Anonymous: 60 requests/hour

### Pagination

**Query Parameters**:
```http
GET /api/v1/resources?page=2&per_page=50&sort=created_at&order=desc
```

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total": 127,
    "total_pages": 3,
    "has_next": true,
    "has_prev": true
  },
  "links": {
    "first": "/api/v1/resources?page=1&per_page=50",
    "prev": "/api/v1/resources?page=1&per_page=50",
    "next": "/api/v1/resources?page=3&per_page=50",
    "last": "/api/v1/resources?page=3&per_page=50"
  }
}
```

## gRPC API

### Service Definition

```protobuf
syntax = "proto3";

package scm.api.v1;

service WorkflowService {
  rpc CreateWorkflow(CreateWorkflowRequest) returns (Workflow);
  rpc GetWorkflow(GetWorkflowRequest) returns (Workflow);
  rpc ListWorkflows(ListWorkflowsRequest) returns (ListWorkflowsResponse);
  rpc UpdateWorkflow(UpdateWorkflowRequest) returns (Workflow);
  rpc DeleteWorkflow(DeleteWorkflowRequest) returns (google.protobuf.Empty);
  rpc ExecuteWorkflow(ExecuteWorkflowRequest) returns (WorkflowRun);
}

service RunService {
  rpc GetRun(GetRunRequest) returns (WorkflowRun);
  rpc ListRuns(ListRunsRequest) returns (ListRunsResponse);
  rpc CancelRun(CancelRunRequest) returns (WorkflowRun);
  rpc StreamLogs(StreamLogsRequest) returns (stream LogEntry);
}

service PluginService {
  rpc RegisterPlugin(RegisterPluginRequest) returns (Plugin);
  rpc ListPlugins(ListPluginsRequest) returns (ListPluginsResponse);
  rpc InstallPlugin(InstallPluginRequest) returns (PluginInstallation);
}

message Workflow {
  string id = 1;
  string name = 2;
  int32 version = 3;
  WorkflowSpec spec = 4;
  google.protobuf.Timestamp created_at = 5;
  google.protobuf.Timestamp updated_at = 6;
}

message WorkflowSpec {
  repeated Trigger triggers = 1;
  map<string, Input> inputs = 2;
  repeated Step steps = 3;
  map<string, Output> outputs = 4;
}
```

## GraphQL API (Optional)

### Schema

```graphql
type Query {
  workflow(id: ID!): Workflow
  workflows(filter: WorkflowFilter, page: Int, perPage: Int): WorkflowConnection!
  run(id: ID!): WorkflowRun
  runs(filter: RunFilter, page: Int, perPage: Int): RunConnection!
  plugins(filter: PluginFilter): [Plugin!]!
}

type Mutation {
  createWorkflow(input: CreateWorkflowInput!): Workflow!
  updateWorkflow(id: ID!, input: UpdateWorkflowInput!): Workflow!
  deleteWorkflow(id: ID!): Boolean!
  executeWorkflow(id: ID!, inputs: JSON): WorkflowRun!
  cancelRun(id: ID!): WorkflowRun!
}

type Subscription {
  runUpdated(id: ID!): WorkflowRun!
  runLogs(id: ID!): LogEntry!
}

type Workflow {
  id: ID!
  name: String!
  version: Int!
  spec: WorkflowSpec!
  runs(page: Int, perPage: Int): RunConnection!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type WorkflowRun {
  id: ID!
  workflow: Workflow!
  status: RunStatus!
  progress: Progress!
  logs: [LogEntry!]!
  startedAt: DateTime
  completedAt: DateTime
}

enum RunStatus {
  PENDING
  RUNNING
  SUCCESS
  FAILED
  CANCELLED
}
```

### Example Query

```graphql
query GetWorkflowWithRuns {
  workflow(id: "wf-abc123") {
    id
    name
    version
    runs(page: 1, perPage: 10) {
      edges {
        node {
          id
          status
          startedAt
          completedAt
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
```

## Webhooks

### Register Webhook

```http
POST /api/v1/webhooks

{
  "url": "https://example.com/webhooks/scm",
  "events": ["workflow.completed", "run.failed"],
  "secret": "webhook-secret-key"
}

Response: 201 Created
{
  "id": "wh-pqr678",
  "url": "https://example.com/webhooks/scm",
  "events": ["workflow.completed", "run.failed"]
}
```

### Webhook Payload

```json
{
  "event": "workflow.completed",
  "timestamp": "2025-10-14T10:30:00Z",
  "data": {
    "run_id": "run-def456",
    "workflow_id": "wf-abc123",
    "status": "success",
    "duration_ms": 45000
  },
  "organization": "acme",
  "project": "platform"
}
```

### Webhook Signature

**Header**:
```http
X-SCM-Signature: sha256=abc123def456...
```

**Verification** (HMAC SHA256):
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## SDKs

### Official SDKs

- **Go**: `github.com/scm/go-sdk`
- **Python**: `scm-sdk` (pip)
- **Node.js**: `@scm/sdk` (npm)
- **Java**: `com.scm:sdk` (Maven)

### Usage Example (Python)

```python
from scm_sdk import Client

# Initialize client
client = Client(
    base_url="https://api.scm.example.com",
    token="scm_xxxxxxxxxx"
)

# Create workflow
workflow = client.workflows.create(
    name="deploy-app",
    spec={
        "triggers": [...],
        "steps": [...]
    }
)

# Execute workflow
run = client.workflows.execute(
    workflow_id=workflow.id,
    inputs={"environment": "staging"}
)

# Wait for completion
run.wait(timeout=300)
print(f"Status: {run.status}")
```

## API Versioning

**URL Versioning**: `/api/v1`, `/api/v2`

**Version Support**:
- Current: Full support, all features
- Previous: Maintenance mode, bug fixes only
- Legacy: Deprecated, 6 months until removal

**Deprecation Headers**:
```http
X-API-Deprecated: true
X-API-Sunset: 2026-04-14T00:00:00Z
Link: <https://docs.scm.dev/api/v2>; rel="successor-version"
```

## Next Steps

- See [ARCHITECTURE.md](../../ARCHITECTURE.md) for overall design
- See [WORKFLOW_DSL.md](../architecture/WORKFLOW_DSL.md) for workflow specification
- See [PLUGIN_SYSTEM.md](../plugins/PLUGIN_SYSTEM.md) for plugin APIs
