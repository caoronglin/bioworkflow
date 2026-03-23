# Repository Settings and Templates
# This file documents the required repository settings

# ============================================
# Branch Protection Rules (configure in GitHub UI)
# ============================================
#
# Branch: main
# - Require a pull request before merging
# - Require approvals: 1
# - Require status checks to pass before merging
#   - lint-python
#   - lint-rust
#   - lint-frontend
#   - test-python (3.12)
#   - test-rust
#   - test-frontend
#   - security-scan
# - Require branches to be up to date before merging
# - Require linear history
# - Include administrators
# - Allow force pushes: No
# - Allow deletions: No

# ============================================
# Required Secrets (Settings > Secrets)
# ============================================
#
# Repository secrets:
# - PYPI_API_TOKEN: PyPI API token for publishing packages
# - CODECOV_TOKEN: Codecov token for coverage uploads
# - VERCEL_TOKEN: Vercel API token
# - VERCEL_ORG_ID: Vercel organization ID
# - VERCEL_PROJECT_ID: Vercel project ID
# - DOCKERHUB_USERNAME: Docker Hub username (optional)
# - DOCKERHUB_TOKEN: Docker Hub token (optional)
# - SLACK_WEBHOOK: Slack webhook for notifications (optional)

# ============================================
# Required Variables (Settings > Variables)
# ============================================
#
# Repository variables:
# - API_URL: Backend API URL for frontend builds
# - VERCEL_ORG_ID: Vercel organization ID
# - VERCEL_PROJECT_ID: Vercel project ID

# ============================================
# Environments (Settings > Environments)
# ============================================
#
# Environment: staging
# - No protection rules required
# - Can be deployed from: main, develop branches
#
# Environment: production
# - Required reviewers: 1
# - Wait timer: 5 minutes
# - Can be deployed from: main branch only
#
# Environment: pypi
# - Required reviewers: 1
# - Wait timer: 5 minutes
# - Can be deployed from: tags only

# ============================================
# GitHub Apps and Integrations
# ============================================
#
# Recommended apps:
# - Dependabot: Automated dependency updates
# - Codecov: Coverage reports
# - Snyk: Security scanning (optional)
# - Renovate: Alternative to Dependabot (optional)

# ============================================
# Workflow Permissions
# ============================================
#
# Settings > Actions > General > Workflow permissions
# - Read and write permissions
# - Allow GitHub Actions to create and approve pull requests

# ============================================
# Merge Settings
# ============================================
#
# Settings > General > Pull Requests
# - Allow squash merging (default)
# - Allow merge commits
# - Allow rebase merging
# - Always suggest updating pull request branches
# - Allow auto-merge