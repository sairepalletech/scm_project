# GitHub Plugin - Reference Implementation

This is a reference implementation of a GitHub connector plugin for SCM Platform, demonstrating best practices for plugin development.

## Overview

The GitHub plugin provides integration with GitHub's REST and GraphQL APIs, enabling:
- Repository management (create, update, delete)
- Branch protection rules
- Pull request operations
- Issue management
- Webhook configuration

## Structure

```
github-plugin/
├── README.md              # This file
├── manifest.yaml          # Plugin manifest
├── main.go               # Entry point
├── connector.go          # Connector implementation
├── config.go             # Configuration handling
├── schemas/
│   └── config.json       # Configuration schema
├── proto/
│   └── github.proto      # Custom protobuf definitions (if needed)
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── Dockerfile            # OCI image build
├── go.mod                # Go dependencies
└── go.sum
```

## Getting Started

### Prerequisites

- Go 1.21+
- SCM Plugin SDK for Go
- GitHub personal access token or GitHub App credentials

### Installation

```bash
# Install SCM CLI
go install github.com/scm/cli@latest

# Initialize plugin
scm plugin init github --type connector --lang go

# Install dependencies
go mod download
```

### Configuration

Create `config.yaml`:

```yaml
github:
  # Option 1: Personal Access Token
  token:
    value: ghp_xxxxxxxxxxxxx  # For development only
    # vault: vault:kv/github/token  # For production

  # Option 2: GitHub App (recommended)
  app:
    id: 123456
    installationID: 7891011
    privateKey:
      vault: vault:kv/github/app-key

  # Optional: GitHub Enterprise
  baseURL: https://api.github.com
  # baseURL: https://github.example.com/api/v3  # For GHE

  # Rate limiting
  rateLimits:
    requestsPerHour: 5000
    burstSize: 100
```

## Development

### Run Locally

```bash
# Set environment variables
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
export SCM_PLUGIN_MODE=dev

# Run plugin
go run main.go
```

### Test

```bash
# Unit tests
go test ./... -v

# Integration tests (requires GitHub credentials)
go test ./tests/integration -v -tags=integration

# Conformance tests
scm plugin conformance --manifest manifest.yaml
```

### Build

```bash
# Build binary
go build -o dist/github-plugin

# Build OCI image
docker build -t ghcr.io/scm/plugins/github:v1.0.0 .

# Sign image
cosign sign ghcr.io/scm/plugins/github:v1.0.0
```

## Usage

### In Workflows

```yaml
apiVersion: workflows.scm.dev/v1
kind: Workflow
metadata:
  name: create-repository
spec:
  steps:
    - name: create-repo
      uses: github.repos:create
      with:
        org: acme
        name: new-service
        visibility: private
        description: "New service repository"
        autoInit: true
        gitignoreTemplate: Go

    - name: protect-main
      uses: github.repos:branch_protection
      with:
        org: acme
        repo: new-service
        branch: main
        rules:
          requirePullRequest: true
          requiredReviews: 2
          requireCodeOwnerReviews: true
          dismissStaleReviews: true
          requireStatusChecks: true
          requiredStatusChecks:
            - ci/tests
            - ci/lint
          restrictPushAccess: true
          allowedPushers:
            - platform-team

    - name: create-initial-pr
      uses: github.prs:open
      with:
        org: acme
        repo: new-service
        title: "Initial setup"
        body: "Setting up repository structure"
        head: setup
        base: main
```

### CLI

```bash
# Test connectivity
scm plugin test github --action health

# Create repository
scm plugin exec github repos:create \
  --org acme \
  --name test-repo \
  --visibility private

# List repositories
scm plugin exec github repos:list \
  --org acme \
  --type private

# Get branch protection
scm plugin exec github repos:get_branch_protection \
  --org acme \
  --repo test-repo \
  --branch main
```

## Capabilities

The GitHub plugin implements the following capabilities:

### Repository Management
- `repos:create` - Create a new repository
- `repos:get` - Get repository details
- `repos:update` - Update repository settings
- `repos:delete` - Delete a repository
- `repos:list` - List organization repositories
- `repos:archive` - Archive a repository

### Branch Protection
- `repos:branch_protection` - Set branch protection rules
- `repos:get_branch_protection` - Get current protection rules
- `repos:delete_branch_protection` - Remove protection rules

### Pull Requests
- `prs:open` - Create a pull request
- `prs:get` - Get PR details
- `prs:list` - List pull requests
- `prs:update` - Update PR (title, body, etc.)
- `prs:merge` - Merge a pull request
- `prs:close` - Close a pull request
- `prs:review` - Submit a review
- `prs:request_review` - Request reviewers

### Issues
- `issues:create` - Create an issue
- `issues:get` - Get issue details
- `issues:list` - List issues
- `issues:update` - Update issue
- `issues:close` - Close an issue
- `issues:comment` - Add comment

### Webhooks
- `webhooks:create` - Create webhook
- `webhooks:list` - List webhooks
- `webhooks:update` - Update webhook
- `webhooks:delete` - Delete webhook

## Implementation Notes

### Rate Limiting

The plugin implements smart rate limiting:

```go
// Adaptive rate limiting based on remaining quota
func (c *Connector) executeWithRateLimit(fn func() error) error {
    remaining := c.getRateLimitRemaining()
    
    if remaining < 100 {
        // Slow down when approaching limit
        time.Sleep(time.Second * 5)
    }
    
    return fn()
}
```

### Idempotency

All operations are idempotent:

```go
func (c *Connector) CreateRepository(ctx context.Context, input *RepoInput) error {
    // Check if repository already exists
    existing, err := c.client.GetRepo(ctx, input.Org, input.Name)
    if err == nil {
        // Repository exists, update instead
        return c.UpdateRepository(ctx, existing.ID, input)
    }
    
    // Create new repository
    return c.client.CreateRepo(ctx, input)
}
```

### Error Handling

Comprehensive error handling with retries:

```go
func (c *Connector) withRetry(fn func() error) error {
    var lastErr error
    
    for attempt := 0; attempt < 3; attempt++ {
        err := fn()
        if err == nil {
            return nil
        }
        
        // Retry on transient errors
        if isTransientError(err) {
            time.Sleep(backoff(attempt))
            continue
        }
        
        // Don't retry on permanent errors
        return err
    }
    
    return lastErr
}
```

### Audit Logging

Every operation generates audit events:

```go
func (c *Connector) CreateRepository(ctx context.Context, input *RepoInput) error {
    start := time.Now()
    
    err := c.client.CreateRepo(ctx, input)
    
    // Log audit event
    c.audit.Log(AuditEvent{
        Timestamp: time.Now(),
        Action:    "repos:create",
        Resource:  fmt.Sprintf("%s/%s", input.Org, input.Name),
        Result:    errorToStatus(err),
        Duration:  time.Since(start),
        Actor:     ctx.Value("actor").(string),
    })
    
    return err
}
```

## Testing

### Unit Tests

```go
func TestCreateRepository(t *testing.T) {
    mock := &MockGitHubClient{}
    connector := &Connector{client: mock}
    
    mock.On("CreateRepo", mock.Anything, mock.Anything).
        Return(&Repository{ID: 123, Name: "test-repo"}, nil)
    
    err := connector.CreateRepository(context.Background(), &RepoInput{
        Org:  "acme",
        Name: "test-repo",
    })
    
    assert.NoError(t, err)
    mock.AssertExpectations(t)
}
```

### Integration Tests

```go
// +build integration

func TestCreateRepository_Integration(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test")
    }
    
    token := os.Getenv("GITHUB_TOKEN")
    require.NotEmpty(t, token)
    
    connector := NewConnector(Config{Token: token})
    
    // Create test repository
    err := connector.CreateRepository(context.Background(), &RepoInput{
        Org:  "test-org",
        Name: "integration-test-" + uuid.New().String(),
    })
    assert.NoError(t, err)
    
    // Cleanup
    defer connector.DeleteRepository(...)
}
```

### Conformance Tests

Run SCM conformance suite:

```bash
scm plugin conformance --manifest manifest.yaml \
  --test-all \
  --github-token $GITHUB_TOKEN
```

## Security

### Secrets Handling

Never log or expose secrets:

```go
func (c *Connector) logConfig() {
    // ❌ Bad: Logs token
    log.Printf("Config: %+v", c.config)
    
    // ✅ Good: Redacts token
    log.Printf("Config: BaseURL=%s, Token=%s", 
        c.config.BaseURL, 
        redact(c.config.Token))
}

func redact(s string) string {
    if len(s) < 8 {
        return "***"
    }
    return s[:4] + "..." + "***"
}
```

### Input Validation

Validate all inputs:

```go
func (c *Connector) Validate(ctx context.Context, config *Config) error {
    if config.Token == "" && config.App == nil {
        return errors.New("either token or app credentials required")
    }
    
    if config.BaseURL != "" {
        u, err := url.Parse(config.BaseURL)
        if err != nil || u.Scheme != "https" {
            return errors.New("baseURL must be valid HTTPS URL")
        }
    }
    
    return nil
}
```

### Permissions

Request only required scopes:

```yaml
permissions:
  scopes:
    - repo                # Repository access
    - admin:repo_hook     # Webhook management
  # NOT requesting:
  # - admin:org          # Organization admin (not needed)
  # - delete_repo        # Repository deletion (explicit action)
```

## Performance

### Caching

Implement intelligent caching:

```go
type Connector struct {
    client *github.Client
    cache  *cache.Cache
}

func (c *Connector) GetRepository(ctx context.Context, org, repo string) (*Repository, error) {
    key := fmt.Sprintf("repo:%s/%s", org, repo)
    
    // Check cache
    if cached, found := c.cache.Get(key); found {
        return cached.(*Repository), nil
    }
    
    // Fetch from API
    result, err := c.client.GetRepo(ctx, org, repo)
    if err != nil {
        return nil, err
    }
    
    // Cache for 5 minutes
    c.cache.Set(key, result, 5*time.Minute)
    return result, nil
}
```

### Batching

Batch operations when possible:

```go
func (c *Connector) CreateRepositories(ctx context.Context, inputs []*RepoInput) error {
    // Process in batches to avoid overwhelming API
    const batchSize = 10
    
    for i := 0; i < len(inputs); i += batchSize {
        end := min(i+batchSize, len(inputs))
        batch := inputs[i:end]
        
        if err := c.processBatch(ctx, batch); err != nil {
            return err
        }
    }
    
    return nil
}
```

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Resources

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [GitHub GraphQL API Documentation](https://docs.github.com/en/graphql)
- [SCM Plugin SDK Documentation](https://docs.scm.dev/plugins/sdk)
- [Plugin Development Guide](../../docs/plugins/PLUGIN_SYSTEM.md)
