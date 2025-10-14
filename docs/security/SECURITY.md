# Security Guide

## Overview

Security is a foundational principle of SCM Platform. This document outlines security practices, threat models, and hardening guidelines for production deployments.

## Security Model

### Defense in Depth

Multiple layers of security controls:

1. **Network Layer**: TLS, mTLS, network policies
2. **Authentication**: OIDC/SAML, service accounts, workload identity
3. **Authorization**: RBAC/ABAC, least privilege
4. **Data**: Encryption at rest and in transit
5. **Application**: Input validation, output encoding, secrets management
6. **Runtime**: Sandboxing, resource limits, audit logging
7. **Supply Chain**: Signed artifacts, SBOM, provenance

## Authentication

### User Authentication

#### OIDC (Recommended)

```yaml
auth:
  oidc:
    enabled: true
    issuerURL: https://auth.example.com/
    clientID: scm-platform
    clientSecret:
      vault: vault:kv/oidc/client-secret
    scopes: [openid, profile, email, groups]
    claimMappings:
      username: preferred_username
      email: email
      groups: groups
```

**Supported Providers**:
- Okta
- Auth0
- Azure AD
- Google Workspace
- Keycloak
- Any OIDC-compliant provider

#### SAML 2.0

```yaml
auth:
  saml:
    enabled: true
    idpMetadataURL: https://idp.example.com/metadata
    entityID: urn:scm:platform
    certificate:
      vault: vault:kv/saml/cert
    privateKey:
      vault: vault:kv/saml/key
```

### Service Accounts

**Short-Lived Tokens** (recommended):
```bash
# Create service account
scm auth create-service-account \
  --name ci-pipeline \
  --role automation \
  --ttl 1h

# Output: token with 1-hour expiration
```

**API Keys** (not recommended for production):
```bash
# Legacy support only
scm auth create-api-key --name legacy-integration
```

### Workload Identity (SPIFFE/SPIRE)

For Kubernetes deployments:

```yaml
workloadIdentity:
  enabled: true
  spire:
    serverAddress: spire-server.spire:8081
    trustDomain: scm.example.com
```

Benefits:
- Automatic credential rotation
- No static credentials
- mTLS between services
- Fine-grained identity

## Authorization

### RBAC (Role-Based Access Control)

#### Built-in Roles

**Organization Roles**:
- `org:admin` - Full control over organization
- `org:member` - Read access to organization resources
- `org:billing` - Billing and usage management

**Project Roles**:
- `project:admin` - Full control over project
- `project:developer` - Execute workflows, manage configurations
- `project:viewer` - Read-only access

**System Roles**:
- `system:admin` - Platform administration
- `system:operator` - Operational tasks (backups, monitoring)
- `plugin:developer` - Publish and manage plugins

#### Custom Roles

```yaml
apiVersion: rbac.scm.dev/v1
kind: Role
metadata:
  name: deployment-manager
rules:
  - resources: [workflows]
    verbs: [read, execute]
    conditions:
      - field: metadata.labels.type
        operator: equals
        value: deployment
  - resources: [secrets]
    verbs: [read]
    scopes: [project:*/environment:production]
```

### ABAC (Attribute-Based Access Control)

Dynamic policies based on attributes:

```yaml
apiVersion: policy.scm.dev/v1
kind: AuthorizationPolicy
metadata:
  name: production-access
spec:
  rules:
    - effect: allow
      principals: [group:platform-team]
      actions: [workflows:execute]
      resources: [project:*/environment:production]
      conditions:
        - key: request.time.hour
          operator: between
          values: [9, 17]  # Business hours only
        - key: request.approval.count
          operator: gte
          value: 2
```

## Secrets Management

### Never Store Secrets in Code

❌ **Bad**:
```yaml
steps:
  - name: deploy
    with:
      api_key: sk-1234567890abcdef  # Hardcoded secret!
```

✅ **Good**:
```yaml
steps:
  - name: deploy
    with:
      api_key: ${{ secrets.api_key }}  # Reference
```

### External Secrets

#### HashiCorp Vault

```yaml
secretsManagement:
  provider: vault
  vault:
    address: https://vault.example.com
    namespace: scm-platform
    authMethod: kubernetes
    role: scm-runner
    mountPath: /v1/secret/data
```

**Read Secret**:
```python
# Platform handles this automatically
secret_value = get_secret("vault:kv/data/github/token")
```

#### AWS Secrets Manager

```yaml
secretsManagement:
  provider: aws-secrets-manager
  aws:
    region: us-west-2
    roleARN: arn:aws:iam::123456789:role/scm-secrets-reader
```

#### Azure Key Vault

```yaml
secretsManagement:
  provider: azure-keyvault
  azure:
    vaultURL: https://scm-vault.vault.azure.net/
    tenantID: abc-123-def-456
    clientID: xyz-789
```

#### Google Cloud Secret Manager

```yaml
secretsManagement:
  provider: gcp-secret-manager
  gcp:
    projectID: scm-platform-prod
    serviceAccount: scm-runner@project.iam.gserviceaccount.com
```

### Secret Rotation

**Automatic Rotation**:
```yaml
secrets:
  - name: database-password
    vault: vault:kv/database/password
    rotation:
      enabled: true
      schedule: "0 2 1 * *"  # Monthly
      notifyChannels: ["#security-alerts"]
```

**Manual Rotation**:
```bash
scm secrets rotate github-token
```

### Secret Redaction

**Automatic in Logs**:
```python
# Input
logger.info(f"Using token: {token}")

# Output (automatically redacted)
[INFO] Using token: ***REDACTED***
```

**Patterns Detected**:
- API keys (sk-*, ghp_*, etc.)
- JWTs
- Passwords (common patterns)
- Private keys
- Certificates

## Data Encryption

### At Rest

**Database Encryption**:
```yaml
postgresql:
  encryption:
    enabled: true
    kmsKeyID: arn:aws:kms:us-west-2:123:key/abc-123
```

**Object Storage Encryption**:
```yaml
objectStorage:
  s3:
    encryption:
      enabled: true
      type: aws:kms
      kmsKeyID: arn:aws:kms:us-west-2:123:key/def-456
```

**Field-Level Encryption**:
```yaml
# Sensitive fields encrypted before storage
database:
  encryptedFields:
    - credentials.password
    - credentials.privateKey
    - personalData.email
```

### In Transit

**TLS Everywhere**:
```yaml
tls:
  minVersion: "1.3"
  cipherSuites:
    - TLS_AES_128_GCM_SHA256
    - TLS_AES_256_GCM_SHA384
    - TLS_CHACHA20_POLY1305_SHA256
```

**mTLS for Internal Communication**:
```yaml
internalTLS:
  enabled: true
  mtls: true
  certificateAuthority: spire
```

## Supply Chain Security

### Signed Artifacts

**Sign Releases**:
```bash
# Sign container image
cosign sign ghcr.io/scm/platform:v2.0.0

# Sign plugin
cosign sign ghcr.io/scm/plugins/github:v1.2.3
```

**Verify Signatures**:
```bash
# Verify before loading
cosign verify --key cosign.pub ghcr.io/scm/platform:v2.0.0
```

### SBOM (Software Bill of Materials)

**Generate SBOM**:
```bash
syft packages ghcr.io/scm/platform:v2.0.0 -o spdx-json > sbom.json
```

**Scan for Vulnerabilities**:
```bash
grype sbom:sbom.json
```

**Required for**:
- Core platform releases
- Official plugins
- Recommended for community plugins

### Provenance

**SLSA Attestations**:
```yaml
attestations:
  - predicate:
      buildType: https://github.com/scm/build/v1
      builder:
        id: https://github.com/scm/builder
      invocation:
        configSource:
          uri: git+https://github.com/scm/platform@refs/heads/main
          digest:
            sha256: abc123...
```

### Dependency Scanning

**Automated Scanning**:
- Dependabot alerts
- Trivy scanning
- Snyk integration
- OSV database checks

## Runtime Security

### Container Security

**Non-Root User**:
```dockerfile
# Run as non-root
USER 1000:1000
```

**Read-Only Root Filesystem**:
```yaml
securityContext:
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
  capabilities:
    drop: [ALL]
```

**Resource Limits**:
```yaml
resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Network Policies

**Restrict Egress**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: scm-runner-netpol
spec:
  podSelector:
    matchLabels:
      app: scm-runner
  policyTypes:
    - Egress
  egress:
    # Allow DNS
    - to:
      - namespaceSelector:
          matchLabels:
            name: kube-system
      ports:
        - protocol: UDP
          port: 53
    # Allow external HTTPS only
    - to:
      - ipBlock:
          cidr: 0.0.0.0/0
          except:
            - 10.0.0.0/8
            - 172.16.0.0/12
            - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443
```

### Plugin Sandboxing

**WASM Sandbox**:
```yaml
plugins:
  untrusted:
    isolation: wasm
    capabilities:
      network: [https://api.github.com]
      filesystem: []  # No filesystem access
      environment: [GITHUB_TOKEN]  # Limited env vars
```

**gRPC Isolation**:
```yaml
plugins:
  official:
    isolation: grpc
    resources:
      memory: 256Mi
      cpu: 100m
    timeout: 300s
```

## Audit & Compliance

### Audit Logging

**Audit Events**:
```json
{
  "timestamp": "2025-10-14T10:30:00Z",
  "eventID": "evt-abc123",
  "actor": {
    "type": "user",
    "id": "user-456",
    "email": "jane@example.com",
    "groups": ["platform-team"]
  },
  "action": "workflows:execute",
  "resource": {
    "type": "workflow",
    "id": "wf-789",
    "org": "acme",
    "project": "platform"
  },
  "result": "success",
  "metadata": {
    "sourceIP": "203.0.113.42",
    "userAgent": "scm-cli/2.0.0"
  }
}
```

**Tamper-Evident**:
- Append-only storage
- Cryptographic checksums
- Immutable once written
- Regular integrity checks

**Retention**:
```yaml
audit:
  retention:
    standard: 90d
    compliance: 7y  # For regulated industries
  export:
    enabled: true
    destinations:
      - type: s3
        bucket: audit-archive
      - type: splunk
        endpoint: https://splunk.example.com
```

### Compliance

**SOC 2 Type II**:
- Access controls
- Data encryption
- Audit logging
- Incident response
- Security monitoring

**ISO 27001**:
- Information security management
- Risk assessment
- Security controls
- Continuous improvement

**GDPR**:
- Data privacy
- Right to erasure
- Data portability
- Consent management

## Threat Model (STRIDE)

### Spoofing Identity
**Threat**: Attacker impersonates legitimate user
**Mitigations**:
- mTLS with SPIRE
- JWT validation
- Webhook signature verification
- API key rotation

### Tampering
**Threat**: Unauthorized modification of data
**Mitigations**:
- Signed artifacts
- Immutable audit logs
- Database integrity checks
- Input validation

### Repudiation
**Threat**: Users deny actions
**Mitigations**:
- Complete audit trail
- Request correlation IDs
- Non-repudiation via signatures
- Timestamping

### Information Disclosure
**Threat**: Unauthorized access to sensitive data
**Mitigations**:
- Encryption at rest and in transit
- Secret redaction in logs
- Scoped access controls
- Data classification

### Denial of Service
**Threat**: System unavailability
**Mitigations**:
- Rate limiting
- Resource quotas
- Circuit breakers
- Backpressure mechanisms

### Elevation of Privilege
**Threat**: Gaining unauthorized permissions
**Mitigations**:
- Principle of least privilege
- Capability-based security
- Plugin sandboxing
- Regular privilege audits

## Incident Response

### Detection

**Monitoring**:
- Failed authentication attempts
- Unusual API access patterns
- Privilege escalations
- Suspicious plugin behavior
- Resource exhaustion

**Alerting**:
```yaml
alerts:
  - name: multiple-failed-logins
    condition: failed_auth_count > 5 in 5m
    severity: high
    notify: [security-team]
  
  - name: privilege-escalation
    condition: role_change AND target_role contains 'admin'
    severity: critical
    notify: [security-team, platform-leads]
```

### Response Procedures

1. **Detect**: Automated alerts, manual reports
2. **Contain**: Revoke access, isolate systems
3. **Investigate**: Review logs, analyze impact
4. **Remediate**: Fix vulnerability, restore service
5. **Learn**: Post-mortem, improve defenses

### Security Contacts

Report security vulnerabilities:
- **Email**: security@scm.dev (PGP key available)
- **Private disclosure** preferred
- **90-day disclosure** timeline

## Security Checklist

### Development
- [ ] All dependencies scanned
- [ ] Static analysis (SAST) passed
- [ ] Dynamic analysis (DAST) passed
- [ ] Secrets not hardcoded
- [ ] Input validation implemented
- [ ] Output encoding implemented
- [ ] Error messages don't leak info

### Deployment
- [ ] TLS 1.3 enforced
- [ ] Network policies configured
- [ ] RBAC roles configured
- [ ] Secrets in external vault
- [ ] Audit logging enabled
- [ ] Monitoring configured
- [ ] Backup and recovery tested

### Operations
- [ ] Regular security updates
- [ ] Vulnerability scanning scheduled
- [ ] Access reviews quarterly
- [ ] Incident response plan tested
- [ ] Security training completed
- [ ] Penetration testing annual

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [SLSA Framework](https://slsa.dev/)

## Next Steps

- Review [ARCHITECTURE.md](../../ARCHITECTURE.md) for security architecture
- See [KUBERNETES.md](../deployment/KUBERNETES.md) for secure deployment
- Explore [PLUGIN_SYSTEM.md](../plugins/PLUGIN_SYSTEM.md) for plugin security
