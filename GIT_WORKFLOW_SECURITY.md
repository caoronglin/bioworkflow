# Git Workflow & Security Guidelines
# BioWorkflow Project

## Git Branch Strategy

### Branch Types

1. **main** - Production branch
   - Protected branch
   - Requires PR review
   - CI/CD must pass
   - Only accept merge from: release/*, hotfix/*

2. **develop** - Development branch (optional for small teams)
   - Integration branch
   - Accept feature/* branches

3. **feature/*** - Feature branches
   - Naming: feature/<issue-id>-<short-description>
   - Example: feature/123-add-pandas3-support
   - Branch from: main or develop
   - Must be squashed when merging

4. **release/*** - Release branches
   - Naming: release/v<major>.<minor>.<patch>
   - Example: release/v0.3.0
   - Branch from: main
   - Only bug fixes allowed

5. **hotfix/*** - Hotfix branches
   - Naming: hotfix/<issue-id>-<description>
   - Example: hotfix/456-fix-security-vulnerability
   - Branch from: main
   - Must merge back to: main AND develop (if exists)

### Commit Message Convention

Format: `<type>(<scope>): <subject>`

Types:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvement
- **test**: Test related
- **chore**: Build/CI/tooling
- **security**: Security fix

Scopes (examples):
- backend
- frontend
- api
- pipeline
- mcp
- chart
- ai
- docs

Examples:
```
feat(backend): add pandas 3.x support with pyarrow backend

fix(api): resolve SQL injection vulnerability in search endpoint

refactor(frontend): migrate to Composition API with <script setup>

security(backend): implement rate limiting for authentication endpoints

feat(ai): integrate OpenAI for intelligent query assistant

perf(chart): optimize large dataset rendering with virtual scrolling
```

### Before Commit Checklist

- [ ] Code follows project style guidelines (black, ruff, eslint)
- [ ] All tests pass (pytest, npm test)
- [ ] Type checking passes (mypy, tsc)
- [ ] Security scan passes (bandit, npm audit)
- [ ] Documentation updated (if needed)
- [ ] Commit message follows convention
- [ ] No secrets or credentials in code

### Dangerous Operations Checklist

Before any destructive operation, you MUST:

1. **Create Backup Branch**
   ```bash
   git branch backup/$(date +%Y%m%d)-$(git rev-parse --short HEAD)-before-<operation>
   ```

2. **Destructive Operations Definition**:
   - Deleting > 20 lines of code
   - Refactoring core modules
   - Database schema changes
   - API breaking changes
   - Dependency major version upgrades

3. **Approval Required For**:
   - Changes to authentication/authorization
   - Database migration scripts
   - API version changes
   - Security-related code
   - CI/CD pipeline changes

## Security Guidelines

### Code Security

1. **Input Validation**
   - Validate all user inputs
   - Use Pydantic models for API validation
   - Sanitize file uploads

2. **SQL Injection Prevention**
   - Use SQLAlchemy ORM (not raw SQL)
   - If raw SQL needed, use parameterized queries
   - Never concatenate user input into SQL

3. **XSS Prevention**
   - Vue automatically escapes HTML
   - Sanitize Markdown with DOMPurify
   - Use CSP headers

4. **Authentication**
   - Use strong JWT implementation
   - Implement proper token refresh
   - Use bcrypt for password hashing
   - Enable MFA (optional but recommended)

5. **Authorization**
   - Implement RBAC (Role-Based Access Control)
   - Check permissions on every endpoint
   - Use principle of least privilege

6. **Secrets Management**
   - Never commit secrets to git
   - Use environment variables
   - Use Vault in production
   - Rotate keys regularly

### Infrastructure Security

1. **Container Security**
   - Use non-root user
   - Read-only filesystem
   - Scan images for vulnerabilities
   - Use minimal base images

2. **Network Security**
   - Use HTTPS only
   - Implement proper firewall rules
   - Use private networks for internal services
   - Implement DDoS protection

3. **Monitoring**
   - Log all security events
   - Set up alerts for suspicious activity
   - Regular security audits
   - Penetration testing

### Security Checklist for New Features

- [ ] Input validation implemented
- [ ] Authentication required (if needed)
- [ ] Authorization checks implemented
- [ ] No secrets in code
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection (for forms)
- [ ] Rate limiting applied
- [ ] Error messages don't leak info
- [ ] Security tests added

### Incident Response Plan

1. **Detection**
   - Automated alerts
   - User reports
   - Monitoring systems

2. **Containment**
   - Isolate affected systems
   - Revoke compromised credentials
   - Block malicious IPs

3. **Investigation**
   - Preserve logs
   - Analyze attack vector
   - Determine scope

4. **Recovery**
   - Fix vulnerabilities
   - Restore services
   - Verify security

5. **Post-Incident**
   - Document lessons learned
   - Update security measures
   - Train team

---

**Last Updated**: 2026-02-22
**Version**: 1.0
**Owner**: BioWorkflow Team
