# 🚀 Deployment & CI/CD Guide

This document provides comprehensive guidance for deploying MarkerEngine Core Backend and understanding the CI/CD pipeline.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment Platforms](#deployment-platforms)
- [Environment Configuration](#environment-configuration)
- [Security & Validation](#security--validation)
- [Troubleshooting](#troubleshooting)
- [Development Workflow](#development-workflow)

## 🚀 Quick Start

### Prerequisites

```bash
# Install required tools
pip install -r backend/requirements-base.txt
npm install --prefix frontend
docker --version
```

### Platform CLI Tools

```bash
# Render (optional)
npm install -g @render/cli

# Fly.io
curl -L https://fly.io/install.sh | sh

# Railway
npm install -g @railway/cli
```

### Deploy with Unified Script

```bash
# Validate configuration only
./scripts/deploy.sh render staging --validate-only

# Deploy to staging
./scripts/deploy.sh fly staging

# Deploy to production
./scripts/deploy.sh railway production

# Dry run
./scripts/deploy.sh render production --dry-run
```

## 🔄 CI/CD Pipeline

### Workflows Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI Pipeline** | Push/PR | Core testing, linting, security |
| **Security Scanning** | Daily/Manual | Comprehensive security analysis |
| **E2E Tests** | Push/Schedule | End-to-end testing |
| **Deployment Validation** | Manual | Pre-deployment validation |

### CI Pipeline (`ci.yml`)

**Runs on**: Every push to `main`/`develop`, PRs to `main`

**Jobs**:
1. **Backend Tests** - Python testing, linting, type checking
2. **Frontend Tests** - Jest/React Testing Library tests
3. **Integration Tests** - Docker-based integration testing
4. **Security Scan** - Basic vulnerability scanning

**Key Features**:
- ✅ Python 3.11 standardized across all jobs
- ✅ Dependency caching for faster builds
- ✅ Coverage reporting to Codecov
- ✅ Parallel execution for speed

### Security Workflow (`security.yml`)

**Runs on**: Daily schedule, manual trigger, main branch pushes

**Advanced Security Features**:
- **CodeQL Analysis** - Static code analysis for security vulnerabilities
- **Dependency Scanning** - Advanced Python/NPM vulnerability detection
- **Container Scanning** - Docker image security analysis
- **License Compliance** - GPL/AGPL license detection
- **Security Policy Validation** - Configuration security checks

### Test Infrastructure

**Frontend Testing**:
```json
{
  "framework": "Jest + React Testing Library",
  "coverage": "Enabled with lcov reports",
  "scripts": {
    "test": "jest --coverage --watchAll=false",
    "test:ci": "jest --ci --coverage --watchAll=false"
  }
}
```

**E2E Testing**:
```typescript
// Playwright configuration with:
- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile device testing
- API integration tests
- Performance validation
```

## 🌐 Deployment Platforms

### Render.com

**Configuration**: `render.yaml`
```yaml
services:
  - type: web
    name: markerengine-backend
    env: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: ENVIRONMENT
        value: production
```

**Deploy**:
```bash
# Using unified script
./scripts/deploy.sh render production

# Direct git push
git push origin main  # Auto-deploys
```

### Fly.io

**Configuration**: `fly.toml`
```toml
app = "me-core-backend"
primary_region = "sin"

[build]
  dockerfile = "backend/Dockerfile.fly"
  target = "base"

[env]
  SPARK_NLP_ENABLED = "false"
```

**Deploy**:
```bash
# Using unified script
./scripts/deploy.sh fly production

# Direct flyctl
flyctl deploy
```

### Railway

**Configuration**: `railway.json` + `nixpacks.toml`
```toml
[phases.build]
cmds = ["pip install -r requirements-base.txt"]

[phases.start]
cmd = "python minimal_app.py"
```

**Deploy**:
```bash
# Using unified script
./scripts/deploy.sh railway production

# Direct railway CLI
railway up
```

## ⚙️ Environment Configuration

### Required Environment Variables

```bash
# Core Application
SECRET_KEY=<strong-random-secret>
DATABASE_URL=mongodb://username:password@host:port/database
ENVIRONMENT=production

# Optional Features
SPARK_NLP_ENABLED=false
REDIS_URL=redis://host:port/0
MOONSHOT_API_KEY=<optional-api-key>
OPENAI_API_KEY=<optional-api-key>

# Security
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_ENABLED=true
HTTPS_ONLY=true
```

### Platform-Specific Secrets

**Render**:
```bash
# Set in Render dashboard under Environment
DATABASE_URL=mongodb+srv://...
SECRET_KEY=your-secret-key
```

**Fly.io**:
```bash
flyctl secrets set DATABASE_URL="mongodb+srv://..."
flyctl secrets set SECRET_KEY="your-secret-key"
```

**Railway**:
```bash
railway variables set DATABASE_URL="mongodb+srv://..."
railway variables set SECRET_KEY="your-secret-key"
```

## 🔒 Security & Validation

### Security Features

1. **Automated Scanning**:
   - Dependency vulnerability detection
   - Container image security scanning
   - Static code analysis (CodeQL)
   - License compliance checking

2. **Security Headers**:
   ```
   Strict-Transport-Security: max-age=31536000
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   Content-Security-Policy: default-src 'self'
   ```

3. **Secrets Management**:
   - No hardcoded secrets in code
   - Environment variable validation
   - Secure secret rotation procedures

### Pre-deployment Validation

```bash
# Comprehensive validation
./scripts/deploy.sh fly production --validate-only

# Manual validation workflow
gh workflow run deployment-validation.yml \
  -f platform=fly \
  -f environment=production \
  -f validate_only=true
```

### Rollback Procedures

```bash
# Quick rollback to previous version
./scripts/rollback.sh fly --force

# Rollback to specific version
./scripts/rollback.sh render --version=v123

# Dry run rollback
./scripts/rollback.sh railway --dry-run
```

## 🔧 Troubleshooting

### Common Issues

**1. Dependency Conflicts**
```bash
# Check requirements compatibility
pip-compile --dry-run backend/requirements-base.txt

# Fix conflicts
pip install pip-tools
pip-compile backend/requirements-base.txt
```

**2. Docker Build Failures**
```bash
# Local testing
cd backend
docker build --target base -t test .
docker run --rm -p 8000:8000 test

# Check logs
docker logs <container-id>
```

**3. CI Pipeline Failures**
```bash
# Check specific job logs in GitHub Actions
# Common fixes:
- Update dependencies in requirements files
- Fix linting errors: black backend/ && flake8 backend/
- Fix type errors: mypy backend/app
```

**4. Deployment Health Check Failures**
```bash
# Test health endpoint locally
curl http://localhost:8000/health
curl http://localhost:8000/api/health/live

# Common fixes:
- Check DATABASE_URL is set
- Verify all required environment variables
- Check application logs for startup errors
```

### Debug Commands

```bash
# Local development
cd backend && python minimal_app.py

# Test with Docker
docker run -it --rm markerengine-backend bash

# Platform-specific debugging
flyctl logs --app your-app
railway logs
# Render: Check dashboard logs
```

## 🔄 Development Workflow

### Branch Strategy

```
main (production)
  ↳ develop (staging)
    ↳ feature/your-feature
    ↳ bugfix/issue-description
    ↳ hotfix/critical-fix
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Development & Testing**
   ```bash
   # Run tests locally
   cd backend && pytest
   cd frontend && npm test
   
   # Lint code
   black backend/ && flake8 backend/
   cd frontend && npm run lint
   ```

3. **Pre-commit Validation**
   ```bash
   # Validate configuration
   ./scripts/deploy.sh fly staging --validate-only
   
   # Security check
   gh workflow run security.yml
   ```

4. **Create Pull Request**
   - CI pipeline runs automatically
   - Security scans execute
   - Code review required
   - All checks must pass

5. **Deployment**
   ```bash
   # After PR merge to develop
   ./scripts/deploy.sh fly staging
   
   # After merge to main
   ./scripts/deploy.sh fly production
   ```

### Release Process

1. **Pre-release Validation**
   ```bash
   gh workflow run deployment-validation.yml \
     -f platform=fly \
     -f environment=production \
     -f validate_only=true
   ```

2. **Deploy to Staging**
   ```bash
   ./scripts/deploy.sh fly staging
   ```

3. **Run E2E Tests**
   ```bash
   gh workflow run e2e-tests.yml
   ```

4. **Deploy to Production**
   ```bash
   ./scripts/deploy.sh fly production
   ```

5. **Post-deployment Monitoring**
   - Monitor application health
   - Check error logs
   - Validate critical user flows
   - Monitor performance metrics

## 📞 Support

- **CI/CD Issues**: Check GitHub Actions logs
- **Deployment Issues**: Use `./scripts/deploy.sh --help`
- **Security Concerns**: Review `SECURITY.md`
- **General Support**: Create GitHub issue with deployment logs

---

*Last updated: $(date)*