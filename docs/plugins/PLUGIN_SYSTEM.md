# Plugin System Design

## Overview

The SCM Plugin System enables extensibility through a modular, secure, and standards-based architecture. It supports 100+ integrations while maintaining isolation, versioning, and backward compatibility.

## Plugin Types

### 1. Connectors
**Purpose**: CRUD operations and webhooks for external systems

**Examples**:
- GitHub (repos, PRs, issues)
- GitLab (projects, pipelines, merge requests)
- AWS (services like CodeCommit, ECR)
- Jenkins (jobs, builds)

**Capabilities**:
- Create, read, update, delete resources
- Subscribe to webhooks/events
- State reconciliation
- Idempotent operations

### 2. Actions
**Purpose**: Executable units used in workflow steps

**Examples**:
- `create_repo`: Create a new repository
- `open_pr`: Open a pull request
- `trigger_pipeline`: Start a CI/CD pipeline
- `send_notification`: Post to Slack/Teams

**Characteristics**:
- Composable and reusable
- Well-defined input/output contracts
- Error handling with retries
- Progress reporting

### 3. Triggers
**Purpose**: Event sources that initiate workflows

**Examples**:
- Webhook receivers (GitHub push, PR events)
- Cron schedules
- Message queue consumers (Kafka, NATS, SQS)
- Manual triggers (API, UI)

**Features**:
- Event filtering and routing
- Payload transformation
- Deduplication
- Rate limiting

### 4. Transformers
**Purpose**: Data manipulation and formatting

**Examples**:
- Template engines (Go templates, Jinja2)
- JQ-like JSON filters
- Schema validation (JSON Schema)
- Data enrichment

**Use Cases**:
- Format messages for notifications
- Extract values from API responses
- Validate webhook payloads
- Transform between different data formats

### 5. Policies
**Purpose**: Admission control and validation

**Examples**:
- PR approval rules
- Branch protection enforcement
- Security scanning gates
- Compliance checks

**Integration**:
- OPA/Rego policies
- Custom validators
- Pre/post-execution hooks
- Deny/allow decisions with rationale

### 6. Notifiers
**Purpose**: Send alerts and notifications

**Examples**:
- Slack
- Microsoft Teams
- Email (SMTP)
- PagerDuty
- Webhooks

**Features**:
- Template-based messages
- Priority levels
- Delivery confirmation
- Retry logic

### 7. UI Extensions (Optional)
**Purpose**: Custom frontend panels and visualizations

**Examples**:
- Repository dashboard
- Pipeline status viewer
- Custom configuration forms
- Analytics widgets

**Characteristics**:
- iframe isolation for security
- Content Security Policy (CSP)
- Standardized communication API
- Theme-aware styling

## Packaging & Distribution

### OCI-Packaged Plugins

Plugins are distributed as OCI (Open Container Initiative) images for standardization and tooling compatibility.

**Example**:
```
ghcr.io/scm/plugins/github:v1.2.3
ghcr.io/acme-corp/plugins/custom-validator:v2.0.0
```

**Structure**:
```
plugin-image/
├── manifest.yaml          # Plugin metadata
├── bin/
│   └── plugin            # Executable (or WASM module)
├── schemas/
│   ├── config.json       # Configuration schema
│   └── actions.json      # Action definitions
├── sbom.json             # Software Bill of Materials
└── signatures/
    └── cosign.sig        # Signature for verification
```

### Signing & Verification

**Signing** (using cosign):
```bash
cosign sign ghcr.io/scm/plugins/github:v1.2.3
```

**Verification** (by platform):
```bash
cosign verify --key cosign.pub ghcr.io/scm/plugins/github:v1.2.3
```

**Requirements**:
- All official plugins MUST be signed
- Community plugins SHOULD be signed
- Platform verifies signatures before loading
- Unsigned plugins require explicit allowlist

### SBOM (Software Bill of Materials)

Generated using Syft:
```bash
syft packages dir:. -o spdx-json > sbom.json
```

**Contents**:
- All dependencies and versions
- License information
- Known vulnerabilities (via Grype)
- Build provenance

### Provenance Attestations

Following SLSA (Supply chain Levels for Software Artifacts):
```yaml
predicateType: https://slsa.dev/provenance/v0.2
predicate:
  builder:
    id: https://github.com/scm/plugin-builder/v1
  buildType: https://github.com/scm/plugin-build/v1
  materials:
    - uri: git+https://github.com/scm/plugins/github
      digest:
        sha256: abc123...
```

## Runtime Isolation

### Option 1: Out-of-Process (gRPC)

**Based on**: HashiCorp go-plugin pattern

**Architecture**:
```
┌─────────────────┐         gRPC          ┌─────────────────┐
│   SCM Host      │ ←──────────────────→  │  Plugin Process │
│   (Orchestrator)│    Unix Socket/TCP    │  (Isolated)     │
└─────────────────┘                       └─────────────────┘
```

**Benefits**:
- Language agnostic (any language with gRPC)
- Crash isolation (plugin crash doesn't affect host)
- Resource limits via cgroups
- Network policies for security

**Drawbacks**:
- Higher overhead (process creation, IPC)
- More complex deployment
- Resource consumption (memory per plugin process)

**Use Case**: Long-running plugins, untrusted code, language diversity

### Option 2: WASM Sandbox

**Architecture**:
```
┌─────────────────────────────────────────┐
│   SCM Host                              │
│   ┌───────────────────────────────┐    │
│   │  WASM Runtime (wasmtime/wazero)│   │
│   │  ┌─────────────────────────┐  │    │
│   │  │  Plugin WASM Module     │  │    │
│   │  │  (Capability-limited)   │  │    │
│   │  └─────────────────────────┘  │    │
│   └───────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Benefits**:
- Near-native performance
- True sandboxing (WASI capabilities)
- Minimal overhead
- Portable across architectures

**Drawbacks**:
- Limited language support (Rust, Go, C/C++ compile to WASM)
- No direct system calls (WASI only)
- Smaller ecosystem

**Use Case**: Performance-critical, constrained environments, edge deployments

### Hybrid Approach

- **Core plugins**: Compiled into host (trusted, performance-critical)
- **Official plugins**: gRPC (full-featured, multi-language)
- **Community plugins**: WASM (sandboxed, safe)
- **Untrusted plugins**: WASM only (maximum isolation)

## Service Provider Interface (SPI)

### Transport

**Protocol**: gRPC over HTTP/2
**Serialization**: Protocol Buffers (Protobuf)
**Versioning**: Major version in package name

**Example**:
```protobuf
syntax = "proto3";

package scm.plugins.v1;

service Connector {
  rpc ListCapabilities(Empty) returns (Capabilities);
  rpc Validate(Config) returns (ValidationResult);
  rpc Plan(PlanRequest) returns (PlanResult);
  rpc Apply(PlanResult) returns (ApplyResult);
  rpc Health(Empty) returns (Healthz);
}
```

### Discovery & Registration

**Plugin Registry** stores:
- Plugin manifest
- Supported versions
- Capabilities
- Configuration schema
- Download URLs
- Signatures

**Discovery Flow**:
1. Host queries registry for plugin
2. Registry returns metadata and download URL
3. Host downloads and verifies plugin
4. Host loads plugin (gRPC or WASM)
5. Host calls ListCapabilities for negotiation

### API Contracts

#### ListCapabilities()
```protobuf
message Capabilities {
  repeated string actions = 1;
  map<string, string> metadata = 2;
  string api_version = 3;
  repeated string required_permissions = 4;
}
```

**Purpose**: Advertise what the plugin can do

**Example Response**:
```json
{
  "actions": [
    "repos:create",
    "repos:delete",
    "repos:branch_protection",
    "prs:open",
    "prs:merge"
  ],
  "metadata": {
    "rate_limit": "5000/hour",
    "supports_webhooks": "true"
  },
  "api_version": "1.2.0",
  "required_permissions": ["repo", "admin:repo_hook"]
}
```

#### Validate(config)
```protobuf
message Config {
  map<string, string> settings = 1;
  map<string, Secret> secrets = 2;
}

message ValidationResult {
  bool valid = 1;
  repeated ValidationError errors = 2;
  repeated string warnings = 3;
}

message ValidationError {
  string field = 1;
  string message = 2;
  string code = 3;
}
```

**Purpose**: Validate configuration before execution

**Example**:
```json
{
  "valid": false,
  "errors": [
    {
      "field": "token",
      "message": "GitHub token is invalid or expired",
      "code": "AUTH_FAILED"
    }
  ],
  "warnings": [
    "Rate limit is low (100 remaining)"
  ]
}
```

#### Plan(input)
```protobuf
message PlanRequest {
  string action = 1;
  map<string, Value> inputs = 2;
  Config config = 3;
}

message PlanResult {
  repeated Change changes = 1;
  bool has_changes = 2;
  string plan_id = 3;
}

message Change {
  string resource = 1;
  string operation = 2;  // create, update, delete
  Value before = 3;
  Value after = 4;
}
```

**Purpose**: Preview changes (dry-run, what-if analysis)

**Example**:
```json
{
  "changes": [
    {
      "resource": "github.com/org/repo",
      "operation": "create",
      "after": {
        "name": "new-repo",
        "visibility": "private"
      }
    }
  ],
  "has_changes": true,
  "plan_id": "plan-abc123"
}
```

#### Apply(plan)
```protobuf
message ApplyResult {
  bool success = 1;
  repeated Output outputs = 2;
  repeated AuditEvent events = 3;
  string error = 4;
}

message Output {
  string key = 1;
  Value value = 2;
}

message AuditEvent {
  string timestamp = 1;
  string action = 2;
  string resource = 3;
  string actor = 4;
  string result = 5;
}
```

**Purpose**: Execute the planned changes

**Example**:
```json
{
  "success": true,
  "outputs": [
    {
      "key": "repo_url",
      "value": "https://github.com/org/new-repo"
    }
  ],
  "events": [
    {
      "timestamp": "2025-10-14T10:30:00Z",
      "action": "repos:create",
      "resource": "org/new-repo",
      "actor": "system:orchestrator",
      "result": "success"
    }
  ]
}
```

#### Health()
```protobuf
message Healthz {
  string status = 1;  // "healthy", "degraded", "unhealthy"
  map<string, string> details = 2;
  string version = 3;
}
```

**Purpose**: Liveness and readiness checks

**Example**:
```json
{
  "status": "healthy",
  "details": {
    "api_reachable": "true",
    "rate_limit_remaining": "4500",
    "last_successful_call": "2025-10-14T10:29:55Z"
  },
  "version": "1.2.3"
}
```

## Developer Experience

### SDKs

#### Go SDK (First-Class)
```bash
# Scaffold new plugin
scm plugin init github --type connector --lang go

# Generated structure:
github-plugin/
├── main.go
├── connector.go
├── proto/
│   └── generated/
├── manifest.yaml
└── go.mod
```

**Example Code**:
```go
package main

import (
    "context"
    sdk "github.com/scm/plugin-sdk-go/v1"
)

type GitHubConnector struct {
    client *github.Client
}

func (g *GitHubConnector) ListCapabilities(ctx context.Context) (*sdk.Capabilities, error) {
    return &sdk.Capabilities{
        Actions: []string{"repos:create", "repos:delete", "prs:open"},
        Metadata: map[string]string{
            "provider": "github",
            "version": "v1.2.3",
        },
    }, nil
}

func (g *GitHubConnector) Apply(ctx context.Context, plan *sdk.PlanResult) (*sdk.ApplyResult, error) {
    // Implementation
}

func main() {
    plugin := &GitHubConnector{}
    sdk.ServeConnector(plugin)
}
```

#### Python SDK
```python
from scm_plugin_sdk import Connector, Capabilities, ApplyResult

class GitHubConnector(Connector):
    def list_capabilities(self) -> Capabilities:
        return Capabilities(
            actions=["repos:create", "repos:delete"],
            metadata={"provider": "github"}
        )
    
    def apply(self, plan: PlanResult) -> ApplyResult:
        # Implementation
        pass

if __name__ == "__main__":
    GitHubConnector().serve()
```

#### Node.js SDK
```javascript
const { Connector, Capabilities } = require('@scm/plugin-sdk');

class GitHubConnector extends Connector {
  listCapabilities() {
    return new Capabilities({
      actions: ['repos:create', 'repos:delete'],
      metadata: { provider: 'github' }
    });
  }

  async apply(plan) {
    // Implementation
  }
}

new GitHubConnector().serve();
```

### CLI Tools

```bash
# Initialize new plugin
scm plugin init <name> --type <connector|action|trigger> --lang <go|python|node>

# Test plugin locally
scm plugin test --manifest manifest.yaml

# Run conformance tests
scm plugin conformance --plugin ./dist/plugin

# Package plugin as OCI image
scm plugin package --output ghcr.io/org/plugin:v1.0.0

# Sign plugin
scm plugin sign ghcr.io/org/plugin:v1.0.0 --key cosign.key

# Publish to registry
scm plugin publish ghcr.io/org/plugin:v1.0.0
```

### Testing

#### Unit Tests
```go
func TestGitHubConnector_Apply(t *testing.T) {
    connector := &GitHubConnector{
        client: mockClient(),
    }
    
    plan := &sdk.PlanResult{
        Changes: []sdk.Change{
            {Resource: "org/repo", Operation: "create"},
        },
    }
    
    result, err := connector.Apply(context.Background(), plan)
    assert.NoError(t, err)
    assert.True(t, result.Success)
}
```

#### Conformance Tests
Provided by SDK, automatically run:
- API contract compliance
- Error handling
- Idempotency checks
- Performance benchmarks
- Security scans

## Plugin Manifest

### Schema
```yaml
apiVersion: plugins.scm.dev/v1
kind: Connector
metadata:
  name: github
  version: 1.3.0
  description: GitHub SCM connector
  maintainers:
    - name: Jane Doe
      email: jane@example.com
  license: Apache-2.0
  homepage: https://github.com/scm/plugins/github

spec:
  capabilities:
    - repos:create
    - repos:delete
    - repos:branch_protection
    - prs:open
    - prs:merge
  
  compatibility:
    engine:
      min: 1.2.0
      max: 2.0.0
      tested: [1.2.3, 1.3.0]
  
  artifacts:
    image: ghcr.io/scm/plugins/github:1.3.0
    signatures:
      cosign: sha256:abc123...
    sbom: sha256:def456...
  
  config:
    schema: schemas/config.json
    secrets:
      - name: token
        description: GitHub personal access token or app credentials
        required: true
        vault_path: vault:kv/data/github/token
    settings:
      - name: base_url
        description: GitHub API base URL (for GitHub Enterprise)
        default: https://api.github.com
        required: false
  
  permissions:
    scopes:
      - repo
      - admin:repo_hook
    rate_limits:
      requests_per_hour: 5000
  
  runtime:
    isolation: grpc  # or "wasm" or "native"
    resources:
      memory: 256Mi
      cpu: 100m
    health_check:
      interval: 30s
      timeout: 5s
```

### Versioning

**Semantic Versioning (SemVer)**:
- `MAJOR.MINOR.PATCH`
- MAJOR: Breaking API changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

**Compatibility Matrix**:
```yaml
compatibility:
  engine:
    min: 1.2.0      # Minimum engine version
    max: 2.0.0      # Maximum tested (exclusive)
    tested: [1.2.3, 1.3.0, 1.4.0]
```

**Deprecation Policy**:
- Mark deprecated in MINOR version
- Remove in next MAJOR version
- Minimum 6 months deprecation period
- Migration guide provided

## Security Considerations

### Permission Model

**Capability-Based**:
```yaml
permissions:
  scopes:
    - repo          # Repository access
    - admin:org     # Organization admin
  resources:
    - github.com/org/*  # Wildcard allowed repos
```

**Least Privilege**:
- Request only needed scopes
- Platform enforces permissions
- Audit all permission usage

### Secrets Management

**Never Store Secrets in Plugin Code**:
```yaml
config:
  secrets:
    - name: token
      vault_path: vault:kv/data/github/token
      rotation: 90d
```

**Injection at Runtime**:
- Platform fetches from Vault/KMS
- Injected as environment variables or config
- Automatic rotation support
- Redacted in logs

### Network Policies

**Restrict Plugin Network Access**:
```yaml
runtime:
  network:
    egress:
      - api.github.com
      - github.com
    deny:
      - internal-services  # Block internal network
```

### Resource Limits

**Prevent Resource Exhaustion**:
```yaml
runtime:
  resources:
    memory: 256Mi
    cpu: 100m
    timeout: 300s
    max_concurrent_requests: 10
```

## Plugin Registry

### Public Registry
- Hosted at `registry.scm.dev`
- Searchable catalog
- Version history
- Download statistics
- User ratings and reviews

### Private Registry
- Self-hosted (Harbor, GitLab Container Registry)
- Air-gapped environments
- Corporate proxies
- Custom allowlists

### Discovery
```bash
# Search plugins
scm plugin search github

# Show plugin details
scm plugin info github --version 1.3.0

# Install plugin
scm plugin install github:1.3.0
```

## Example: GitHub Connector (Complete)

See [examples/github-plugin/](../../examples/github-plugin/) for a complete reference implementation.

## Next Steps

1. Review [ARCHITECTURE.md](../../ARCHITECTURE.md) for overall platform design
2. See [ROADMAP.md](../../ROADMAP.md) for implementation timeline
3. Explore [API_SPECIFICATION.md](../api/API_SPECIFICATION.md) for API details
