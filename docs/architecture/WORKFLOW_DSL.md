# Workflow DSL Specification

## Overview

The SCM Workflow DSL (Domain-Specific Language) provides a declarative way to define automation workflows. Inspired by Ansible and GitHub Actions, it emphasizes idempotency, composability, and readability.

## Design Principles

1. **Declarative**: Describe *what* you want, not *how* to achieve it
2. **Idempotent**: Safe to run multiple times
3. **Composable**: Reusable steps and workflows
4. **Testable**: Can be validated and dry-run before execution
5. **Observable**: Built-in logging, metrics, and tracing

## Basic Structure

```yaml
apiVersion: workflows.scm.dev/v1
kind: Workflow
metadata:
  name: bootstrap-organization
  description: Bootstrap a new organization with standard configuration
  labels:
    team: platform
    category: onboarding

spec:
  # When should this workflow run?
  triggers:
    - type: manual
    - type: cron
      schedule: "0 2 * * *"
    - type: webhook
      source: github
      events: [repository.created]

  # What data does this workflow need?
  inputs:
    org_name:
      type: string
      required: true
      description: Organization name
    region:
      type: string
      default: us-west-2
      enum: [us-east-1, us-west-2, eu-west-1]

  # What should happen?
  steps:
    - name: create-repositories
      uses: github.repos:create
      with:
        org: ${{ inputs.org_name }}
        repos:
          - name: platform-api
            visibility: private
          - name: web-ui
            visibility: private

    - name: setup-branch-protection
      uses: github.repos:branch_protection
      with:
        org: ${{ inputs.org_name }}
        repo: platform-api
        rules:
          require_reviews: 2
          block_force_push: true
          require_status_checks: true

    - name: notify-team
      uses: slack.notify:send
      with:
        channel: "#platform-events"
        message: "Organization ${{ inputs.org_name }} bootstrapped successfully"

  # What to do on success/failure?
  on_success:
    - uses: audit.log:record
      with:
        event: workflow.completed
        status: success

  on_failure:
    - uses: slack.notify:send
      with:
        channel: "#platform-alerts"
        message: "⚠️ Workflow failed: ${{ workflow.name }}"
        priority: high
```

## Core Concepts

### 1. Triggers

Define when a workflow should execute.

#### Manual Trigger
```yaml
triggers:
  - type: manual
    requires_approval: true
    approvers:
      - team-leads
      - platform-admins
```

#### Cron Schedule
```yaml
triggers:
  - type: cron
    schedule: "0 2 * * *"  # Every day at 2 AM
    timezone: America/Los_Angeles
```

#### Webhook Trigger
```yaml
triggers:
  - type: webhook
    source: github
    events:
      - push
      - pull_request.opened
      - pull_request.synchronized
    filters:
      branches:
        - main
        - release/*
```

#### Event Bus Trigger
```yaml
triggers:
  - type: event
    source: nats
    subject: deployments.production.*
    filter: ${{ event.status == 'completed' }}
```

### 2. Inputs & Outputs

#### Input Definition
```yaml
inputs:
  repository:
    type: string
    required: true
    pattern: ^[a-zA-Z0-9-_]+$
    description: Repository name

  environment:
    type: string
    default: development
    enum: [development, staging, production]

  tags:
    type: array
    items:
      type: string
    default: []

  config:
    type: object
    required: false
    schema: schemas/app-config.json
```

#### Output Declaration
```yaml
outputs:
  deployment_url:
    description: URL of the deployed application
    value: ${{ steps.deploy.outputs.url }}

  commit_sha:
    description: Commit SHA that was deployed
    value: ${{ steps.build.outputs.sha }}
```

### 3. Steps

The core execution units of a workflow.

#### Simple Step
```yaml
steps:
  - name: create-repo
    uses: github.repos:create
    with:
      org: acme
      name: my-repo
      visibility: private
```

#### Step with Conditions
```yaml
steps:
  - name: deploy-production
    uses: kubernetes.deploy:apply
    when: ${{ inputs.environment == 'production' }}
    with:
      namespace: prod
      manifest: deploy/prod.yaml
```

#### Step with Retries
```yaml
steps:
  - name: flaky-api-call
    uses: http.request:post
    retry:
      max_attempts: 3
      backoff: exponential
      initial_delay: 1s
      max_delay: 30s
    with:
      url: https://api.example.com/deploy
```

#### Step with Timeout
```yaml
steps:
  - name: long-running-task
    uses: custom.task:execute
    timeout: 30m
    with:
      command: process-large-dataset
```

### 4. Variables & Expressions

#### Context Variables
```yaml
# Workflow context
${{ workflow.name }}           # Workflow name
${{ workflow.run_id }}         # Unique run ID
${{ workflow.triggered_by }}   # User/system that triggered

# Input context
${{ inputs.org_name }}         # Input parameter value

# Step context
${{ steps.build.outputs.sha }} # Output from previous step
${{ steps.test.status }}       # Status: success, failure, skipped

# Environment context
${{ env.CI }}                  # Environment variable
${{ secrets.github_token }}    # Secret (redacted in logs)

# Event context (for webhook triggers)
${{ event.repository.name }}
${{ event.pull_request.number }}
```

#### Expressions
```yaml
# Comparison
${{ inputs.count > 10 }}
${{ inputs.env == 'production' }}

# Logical operators
${{ inputs.deploy && inputs.environment == 'prod' }}
${{ inputs.skip_tests || inputs.fast_mode }}

# String operations
${{ startsWith(inputs.branch, 'release/') }}
${{ contains(inputs.tags, 'critical') }}

# Filters
${{ inputs.repos | map(r => r.name) }}
${{ inputs.tags | filter(t => t != 'deprecated') }}
```

### 5. Conditionals

#### Step-Level Conditions
```yaml
steps:
  - name: run-tests
    uses: test.runner:execute
    when: ${{ !inputs.skip_tests }}

  - name: deploy-staging
    uses: deploy:apply
    when: ${{ inputs.environment != 'production' }}

  - name: manual-approval
    uses: approval.gate:wait
    when: ${{ inputs.environment == 'production' }}
```

#### Conditional Expressions
```yaml
steps:
  - name: conditional-notify
    uses: slack.notify:send
    when: ${{ steps.deploy.status == 'success' && inputs.notify }}
    with:
      channel: "#deployments"
```

### 6. Loops & Iteration

#### Loop Over List
```yaml
steps:
  - name: create-repositories
    uses: github.repos:create
    for_each: ${{ inputs.repositories }}
    with:
      org: acme
      name: ${{ item.name }}
      visibility: ${{ item.visibility }}
```

#### Loop with Index
```yaml
steps:
  - name: deploy-regions
    uses: cloud.deploy:apply
    for_each: ${{ inputs.regions }}
    with:
      region: ${{ item }}
      identifier: region-${{ index }}
```

#### Matrix Strategy
```yaml
steps:
  - name: test-matrix
    uses: test.runner:execute
    matrix:
      os: [ubuntu, macos, windows]
      version: [18, 20, 22]
      exclude:
        - os: macos
          version: 18
    with:
      os: ${{ matrix.os }}
      node_version: ${{ matrix.version }}
```

### 7. Dependencies

#### Sequential Steps
```yaml
steps:
  - name: build
    uses: build:docker
    
  - name: test
    needs: [build]
    uses: test:run
    
  - name: deploy
    needs: [test]
    uses: deploy:apply
```

#### Parallel Steps
```yaml
steps:
  - name: test-unit
    uses: test:unit
    
  - name: test-integration
    uses: test:integration
    
  - name: lint
    uses: lint:check
    
  # These run in parallel (no needs)
    
  - name: deploy
    needs: [test-unit, test-integration, lint]
    uses: deploy:apply
```

### 8. Error Handling

#### Continue on Error
```yaml
steps:
  - name: optional-step
    uses: optional.task:run
    continue_on_error: true
```

#### Custom Error Handling
```yaml
steps:
  - name: risky-operation
    uses: external.api:call
    on_error:
      - uses: rollback.action:execute
      - uses: notify.team:alert
```

#### Retry Logic
```yaml
steps:
  - name: flaky-test
    uses: test:run
    retry:
      max_attempts: 3
      on_errors: [timeout, connection_error]
      backoff: exponential
```

### 9. Notifications & Handlers

#### Success Handler
```yaml
on_success:
  - uses: slack.notify:send
    with:
      channel: "#deployments"
      message: "✅ Deployment successful"
```

#### Failure Handler
```yaml
on_failure:
  - uses: pagerduty.incident:create
    with:
      severity: high
      description: "Workflow ${{ workflow.name }} failed"
  - uses: rollback.action:execute
```

#### Cleanup (Always Runs)
```yaml
on_complete:
  - uses: cleanup.temp:remove
    with:
      paths: [/tmp/build-*]
```

### 10. Sub-Workflows

#### Call Another Workflow
```yaml
steps:
  - name: provision-infrastructure
    uses: workflow:call
    with:
      workflow: provision-vpc
      inputs:
        region: ${{ inputs.region }}
        environment: ${{ inputs.environment }}
```

#### Reusable Workflow
```yaml
# provision-vpc.yaml
apiVersion: workflows.scm.dev/v1
kind: Workflow
metadata:
  name: provision-vpc
  reusable: true

spec:
  inputs:
    region:
      type: string
      required: true
    environment:
      type: string
      required: true

  steps:
    - name: create-vpc
      uses: aws.vpc:create
      with:
        region: ${{ inputs.region }}
```

## Advanced Features

### 1. Template Interpolation

#### Go Templates
```yaml
steps:
  - name: generate-config
    uses: file.template:render
    with:
      template: |
        server {
          listen {{ .Port }};
          server_name {{ .Domain }};
          location / {
            proxy_pass http://{{ .Backend }}:{{ .BackendPort }};
          }
        }
      values:
        Port: 80
        Domain: example.com
        Backend: localhost
        BackendPort: 8080
```

#### Jinja2 Templates
```yaml
steps:
  - name: render-notification
    uses: template.jinja:render
    with:
      template: |
        Deployment to {{ environment }} completed!
        {% if status == 'success' %}
        ✅ All checks passed
        {% else %}
        ❌ Some checks failed
        {% endif %}
      values:
        environment: ${{ inputs.environment }}
        status: ${{ steps.deploy.status }}
```

### 2. Secrets & Credentials

```yaml
steps:
  - name: deploy-with-credentials
    uses: cloud.deploy:apply
    with:
      credentials: ${{ secrets.aws_credentials }}
      region: us-west-2
```

**Secret References** (never logged):
- `${{ secrets.github_token }}`
- `${{ secrets.aws_access_key }}`
- `${{ vault.path.to.secret }}`

### 3. Artifacts

#### Upload Artifacts
```yaml
steps:
  - name: build-binary
    uses: build:compile
    outputs:
      artifacts:
        - path: dist/app
          name: application-binary
          retention: 30d
```

#### Download Artifacts
```yaml
steps:
  - name: test-binary
    uses: test:run
    with:
      binary: ${{ artifacts.application-binary.path }}
```

### 4. Approvals

#### Manual Approval Gate
```yaml
steps:
  - name: wait-for-approval
    uses: approval.gate:wait
    with:
      approvers:
        - platform-team
        - security-team
      timeout: 24h
      message: "Production deployment requires approval"
```

### 5. Notifications

```yaml
steps:
  - name: notify-slack
    uses: slack.notify:send
    with:
      channel: "#deployments"
      message: |
        Deployment started
        Environment: ${{ inputs.environment }}
        Triggered by: ${{ workflow.triggered_by }}
        Run ID: ${{ workflow.run_id }}
      blocks:
        - type: section
          text: "Status: In Progress"
```

## Complete Example: CI/CD Pipeline

```yaml
apiVersion: workflows.scm.dev/v1
kind: Workflow
metadata:
  name: ci-cd-pipeline
  description: Complete CI/CD pipeline with testing, security scanning, and deployment

spec:
  triggers:
    - type: webhook
      source: github
      events: [push]
      filters:
        branches: [main, develop]

  inputs:
    environment:
      type: string
      default: development
      enum: [development, staging, production]

  steps:
    # Build Stage
    - name: checkout-code
      uses: git.clone:checkout
      with:
        repository: ${{ event.repository.full_name }}
        ref: ${{ event.after }}

    - name: build-docker-image
      uses: docker.build:image
      with:
        context: .
        tags:
          - ${{ event.repository.name }}:${{ event.after }}
          - ${{ event.repository.name }}:latest

    # Test Stage (parallel)
    - name: run-unit-tests
      needs: [build-docker-image]
      uses: test.runner:execute
      with:
        suite: unit
        image: ${{ steps.build-docker-image.outputs.image }}

    - name: run-integration-tests
      needs: [build-docker-image]
      uses: test.runner:execute
      with:
        suite: integration
        image: ${{ steps.build-docker-image.outputs.image }}

    - name: run-e2e-tests
      needs: [build-docker-image]
      uses: test.runner:execute
      when: ${{ inputs.environment == 'production' }}
      with:
        suite: e2e
        image: ${{ steps.build-docker-image.outputs.image }}

    # Security Stage (parallel)
    - name: security-scan
      needs: [build-docker-image]
      uses: security.trivy:scan
      with:
        image: ${{ steps.build-docker-image.outputs.image }}
        severity: [HIGH, CRITICAL]

    - name: sast-scan
      needs: [checkout-code]
      uses: security.sast:analyze
      with:
        path: .

    # Gate for Production
    - name: production-approval
      needs: [run-unit-tests, run-integration-tests, run-e2e-tests, security-scan]
      when: ${{ inputs.environment == 'production' }}
      uses: approval.gate:wait
      with:
        approvers: [release-managers]
        timeout: 24h

    # Deploy Stage
    - name: deploy-application
      needs: [production-approval]
      uses: kubernetes.deploy:apply
      with:
        namespace: ${{ inputs.environment }}
        image: ${{ steps.build-docker-image.outputs.image }}
        replicas: ${{ inputs.environment == 'production' ? 5 : 2 }}

    # Verification Stage
    - name: health-check
      needs: [deploy-application]
      uses: http.request:get
      retry:
        max_attempts: 10
        initial_delay: 5s
      with:
        url: ${{ steps.deploy-application.outputs.health_url }}
        expect_status: 200

    # Notification
    - name: notify-success
      needs: [health-check]
      uses: slack.notify:send
      with:
        channel: "#deployments"
        message: |
          ✅ Deployment Successful
          Environment: ${{ inputs.environment }}
          Commit: ${{ event.after }}
          URL: ${{ steps.deploy-application.outputs.url }}

  on_failure:
    - uses: rollback.deploy:previous
      when: ${{ inputs.environment == 'production' }}
    - uses: pagerduty.incident:create
      with:
        severity: high
        description: "CI/CD pipeline failed for ${{ event.repository.name }}"
```

## Validation & Testing

### Syntax Validation
```bash
scm workflow validate workflow.yaml
```

### Dry-Run (Plan)
```bash
scm workflow plan workflow.yaml \
  --input org_name=acme \
  --input environment=staging
```

### Local Execution
```bash
scm workflow run workflow.yaml \
  --input org_name=acme \
  --dry-run
```

## Best Practices

1. **Idempotency**: Ensure steps can be safely re-run
2. **Naming**: Use descriptive step names
3. **Error Handling**: Always handle failures gracefully
4. **Secrets**: Never hardcode secrets, use secret management
5. **Documentation**: Add descriptions to workflows and inputs
6. **Testing**: Validate workflows before production use
7. **Monitoring**: Use structured logging and metrics
8. **Versioning**: Version workflows and track changes

## Migration from v1.0.0 TOML Format

### Old Format (v1.0.0)
```toml
[service.setup]
name = ["apache2"]
action = ["install", "enable"]

[file.conf]
name = ["/etc/apache2/apache2.conf"]
action = ["create"]
content = ["ServerName localhost"]
```

### New Format (v2.0.0)
```yaml
apiVersion: workflows.scm.dev/v1
kind: Workflow
steps:
  - name: install-apache
    uses: service.package:install
    with:
      name: apache2
      enabled: true

  - name: configure-apache
    uses: file.content:write
    with:
      path: /etc/apache2/apache2.conf
      content: "ServerName localhost"
```

### Compatibility Bridge

Both formats are supported for a transition period. The platform automatically detects and converts TOML to the new DSL format internally.

## Next Steps

- See [PLUGIN_SYSTEM.md](../plugins/PLUGIN_SYSTEM.md) for plugin development
- See [API_SPECIFICATION.md](../api/API_SPECIFICATION.md) for API details
- See [ARCHITECTURE.md](../../ARCHITECTURE.md) for overall design
