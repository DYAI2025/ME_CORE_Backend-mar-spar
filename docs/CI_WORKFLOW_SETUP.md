# CI Workflow Setup Script Documentation

## Overview

The `ci-workflow-setup.py` script is a comprehensive utility for managing GitHub Actions workflows in MarkerEngine projects. It provides tools for generating, validating, and initializing CI/CD infrastructure with best practices built-in.

## Features

- **Generate Workflow Templates**: Create standardized GitHub Actions workflows
- **Validate Existing Workflows**: Check workflow files for common issues and outdated actions
- **Initialize New Projects**: Set up complete CI infrastructure for new projects
- **Best Practices Enforcement**: Uses latest action versions and security best practices

## Installation & Requirements

The script requires Python 3.8+ and has the following dependencies:
- `pyyaml` (for YAML processing)
- Standard library modules: `argparse`, `json`, `os`, `sys`, `pathlib`, `logging`

PyYAML is already included in the project's requirements, so no additional installation is needed.

## Usage

### 1. Generate Workflow Files

Create standardized workflow templates:

```bash
# Generate a CI workflow
python ci-workflow-setup.py generate --type ci

# Generate a security workflow with custom name
python ci-workflow-setup.py generate --type security --output custom-security.yml

# Generate deployment validation workflow
python ci-workflow-setup.py generate --type deployment
```

**Available workflow types:**
- `ci`: Comprehensive CI pipeline with backend/frontend tests, linting, type checking
- `security`: Advanced security analysis with CodeQL, dependency scanning
- `deployment`: Deployment validation and configuration checking

### 2. Validate Workflow Files

Check existing workflows for issues:

```bash
# Validate all workflow files
python ci-workflow-setup.py validate --all

# Validate a specific workflow file
python ci-workflow-setup.py validate --file .github/workflows/ci.yml
```

**Validation checks:**
- Required fields (name, triggers, jobs)
- Outdated GitHub Action versions
- YAML syntax errors
- Best practice compliance

### 3. Initialize New Projects

Set up complete CI infrastructure for new projects:

```bash
# Initialize with all features
python ci-workflow-setup.py init --project-name "My New Project"

# Initialize with specific features only
python ci-workflow-setup.py init --project-name "Backend API" --features ci security
```

**Generated files:**
- GitHub Actions workflows (`.github/workflows/`)
- `.gitignore` with Python/Node.js patterns
- `README.md` with project structure
- `requirements-base.txt` with common dependencies
- `pytest.ini` with testing configuration

## Workflow Templates

### CI Pipeline Template

The CI workflow template includes:

**Backend Testing:**
- Python 3.11 with pip caching
- MongoDB and Redis services for testing
- Flake8 linting with E9,F63,F7,F82 error codes
- MyPy type checking
- Pytest with coverage reporting
- Codecov integration

**Frontend Testing:**
- Node.js 18 with npm caching
- ESLint linting
- TypeScript type checking
- Jest testing with CI configuration
- Production build validation

**Integration Testing:**
- Docker Compose based testing
- Cross-service validation
- Cleanup procedures

**Security Scanning:**
- Trivy vulnerability scanner
- Safety/Bandit Python security tools
- NPM audit for Node.js dependencies

### Security Workflow Template

Advanced security analysis with:
- **CodeQL Analysis**: Static code analysis for Python/JavaScript
- **Dependency Scanning**: Advanced vulnerability detection
- **Container Security**: Docker image scanning
- **Scheduled Runs**: Daily automated security checks

### Deployment Validation Template

Pre-deployment validation including:
- Configuration validation for multiple platforms (Render, Fly.io, Railway)
- Docker build verification
- Environment-specific checks
- Manual trigger with platform/environment selection

## Configuration

### Environment Variables

The workflows use these standardized environment variables:
- `PYTHON_VERSION`: "3.11" (standardized across all jobs)
- `NODE_VERSION`: "18"
- `JAVA_VERSION`: "11" (for Spark NLP if needed)

### GitHub Actions Versions

The script uses the latest stable versions:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/setup-node@v4`
- `actions/cache@v4`
- `docker/setup-buildx-action@v3`

## Best Practices

The script enforces these best practices:

1. **Version Consistency**: Standardized Python/Node versions across all jobs
2. **Dependency Caching**: Efficient caching for faster builds
3. **Parallel Execution**: Independent jobs run in parallel
4. **Error Handling**: Graceful failure handling and cleanup
5. **Security First**: Built-in security scanning and validation
6. **Documentation**: Comprehensive README and configuration files

## Examples

### Validating Current Project Workflows

```bash
cd /path/to/your/project
python ci-workflow-setup.py validate --all
```

Expected output:
```
🔍 Validation Results:
==================================================
✅ VALID ci.yml
  ⚠️  WARNING: Outdated action found: actions/setup-python@v4 -> consider updating to actions/setup-python@v5
  ℹ️  INFO: Python version is configured in environment variables

✅ VALID security.yml
  ℹ️  INFO: Python version is configured in environment variables

🎉 All workflows are valid!
```

### Setting Up a New Microservice

```bash
mkdir my-new-service
cd my-new-service
python /path/to/ci-workflow-setup.py init --project-name "Payment Service" --features ci security

# This creates:
# .github/workflows/ci.yml
# .github/workflows/security.yml
# .gitignore
# README.md
# requirements-base.txt
# pytest.ini
```

### Generating Custom Workflows

```bash
# Create a custom CI workflow for a specific project
python ci-workflow-setup.py generate --type ci --output payment-service-ci.yml

# The generated workflow can be customized further for specific needs
```

## Integration with MarkerEngine Project

This script is designed specifically for the MarkerEngine ecosystem and includes:

- **Platform Support**: Render, Fly.io, Railway deployment configurations
- **Service Dependencies**: MongoDB, Redis service containers
- **Technology Stack**: FastAPI, React, Pytest, Jest configurations
- **Security Standards**: Safety, Bandit, CodeQL integration
- **Monitoring**: Prometheus metrics and health checks

## Troubleshooting

### Common Issues

1. **PyYAML not found**: Install with `pip install pyyaml`
2. **Permission denied**: Make script executable with `chmod +x ci-workflow-setup.py`
3. **Invalid YAML**: Check workflow syntax with `python -c "import yaml; yaml.safe_load(open('file.yml'))"`

### Validation Errors

The script checks for common workflow issues:
- Missing required fields (name, triggers, jobs)
- Outdated action versions
- YAML syntax errors
- Security misconfigurations

## Contributing

When modifying the script:

1. **Add new workflow types** by extending the `WorkflowTemplates` class
2. **Update validation rules** in the `validate_workflow` method
3. **Test thoroughly** with both new and existing projects
4. **Update documentation** for any new features or changes

## License

This script is part of the MarkerEngine project and is licensed under Creative Commons BY-NC-SA 4.0.