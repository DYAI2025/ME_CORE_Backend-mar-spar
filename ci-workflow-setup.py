#!/usr/bin/env python3
"""
CI Workflow Setup Script for MarkerEngine Core Backend
======================================================

This script provides utilities for setting up, validating, and managing
GitHub Actions workflows for the MarkerEngine project. It can generate
workflow templates, validate existing configurations, and help set up
CI infrastructure for new projects.

Usage:
    python ci-workflow-setup.py --help
    python ci-workflow-setup.py generate --type ci
    python ci-workflow-setup.py validate --all
    python ci-workflow-setup.py init --project-name my-project

Author: MarkerEngine Team
License: Creative Commons BY-NC-SA 4.0
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WorkflowTemplates:
    """Templates for different types of GitHub Actions workflows."""

    @staticmethod
    def get_ci_workflow() -> Dict[str, Any]:
        """Generate a comprehensive CI workflow template."""
        return {
            "name": "CI Pipeline",
            "on": {
                "push": {"branches": ["main", "develop"]},
                "pull_request": {"branches": ["main", "develop"]},
            },
            "env": {
                "PYTHON_VERSION": "3.11",
                "NODE_VERSION": "18",
                "JAVA_VERSION": "11",
            },
            "jobs": {
                "backend-tests": {
                    "name": "Backend Tests",
                    "runs-on": "ubuntu-latest",
                    "services": {
                        "mongodb": {
                            "image": "mongo:6.0",
                            "ports": ["27017:27017"],
                            "options": (
                                "--health-cmd \"mongosh --eval 'db.adminCommand({ping: 1})'\" "
                                "--health-interval 10s --health-timeout 5s --health-retries 5"
                            ),
                        },
                        "redis": {
                            "image": "redis:7-alpine",
                            "ports": ["6379:6379"],
                            "options": (
                                '--health-cmd "redis-cli ping" '
                                "--health-interval 10s --health-timeout 5s --health-retries 5"
                            ),
                        },
                    },
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v5",
                            "with": {"python-version": "${{ env.PYTHON_VERSION }}"},
                        },
                        {
                            "name": "Cache Python dependencies",
                            "uses": "actions/cache@v4",
                            "with": {
                                "path": "~/.cache/pip",
                                "key": "${{ runner.os }}-pip-${{ hashFiles('backend/requirements*.txt') }}",
                                "restore-keys": "${{ runner.os }}-pip-",
                            },
                        },
                        {
                            "name": "Install dependencies",
                            "run": "cd backend\npython -m pip install --upgrade pip\npip install -r requirements-base.txt\npip install -r requirements-dev.txt",
                        },
                        {
                            "name": "Lint with flake8",
                            "run": "cd backend\nflake8 . --count --select=E9,F63,F7,F82 --show-source --statistics\nflake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics",
                        },
                        {
                            "name": "Type check with mypy",
                            "run": "cd backend\nmypy app --ignore-missing-imports",
                        },
                        {
                            "name": "Test with pytest",
                            "env": {
                                "DATABASE_URL": "mongodb://localhost:27017/test_db",
                                "REDIS_URL": "redis://localhost:6379/0",
                                "SPARK_NLP_ENABLED": "false",
                            },
                            "run": "cd backend\npytest tests/ -v --cov=app --cov-report=xml --cov-report=html",
                        },
                        {
                            "name": "Upload coverage",
                            "uses": "codecov/codecov-action@v4",
                            "with": {
                                "file": "./backend/coverage.xml",
                                "flags": "backend",
                                "name": "backend-coverage",
                            },
                        },
                    ],
                },
                "frontend-tests": {
                    "name": "Frontend Tests",
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Use Node.js",
                            "uses": "actions/setup-node@v4",
                            "with": {
                                "node-version": "${{ env.NODE_VERSION }}",
                                "cache": "npm",
                                "cache-dependency-path": "frontend/package-lock.json",
                            },
                        },
                        {"name": "Install dependencies", "run": "cd frontend\nnpm ci"},
                        {"name": "Lint", "run": "cd frontend\nnpm run lint"},
                        {
                            "name": "Type check",
                            "run": "cd frontend\nnpm run type-check",
                        },
                        {"name": "Test", "run": "cd frontend\nnpm run test:ci"},
                        {"name": "Build", "run": "cd frontend\nnpm run build"},
                    ],
                },
                "integration-tests": {
                    "name": "Integration Tests",
                    "needs": ["backend-tests", "frontend-tests"],
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Set up Docker Buildx",
                            "uses": "docker/setup-buildx-action@v3",
                        },
                        {"name": "Build images", "run": "docker-compose build"},
                        {
                            "name": "Run integration tests",
                            "run": "docker-compose -f docker-compose.test.yml up --abort-on-container-exit",
                        },
                        {
                            "name": "Cleanup",
                            "if": "always()",
                            "run": "docker-compose -f docker-compose.test.yml down -v",
                        },
                    ],
                },
                "security-scan": {
                    "name": "Security Scan (Basic)",
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Run Trivy vulnerability scanner",
                            "uses": "aquasecurity/trivy-action@master",
                            "with": {
                                "scan-type": "fs",
                                "scan-ref": ".",
                                "format": "sarif",
                                "output": "trivy-results.sarif",
                            },
                        },
                        {
                            "name": "Upload Trivy scan results",
                            "uses": "github/codeql-action/upload-sarif@v3",
                            "if": "always()",
                            "with": {"sarif_file": "trivy-results.sarif"},
                        },
                        {
                            "name": "Set up Python for security checks",
                            "uses": "actions/setup-python@v5",
                            "with": {"python-version": "${{ env.PYTHON_VERSION }}"},
                        },
                        {
                            "name": "Basic Python security check",
                            "run": 'pip install safety bandit\ncd backend\nsafety check -r requirements-base.txt --short-report || echo "⚠️ Safety check completed with warnings"\nbandit -r . -f txt --exclude ./tests || echo "⚠️ Bandit scan completed with warnings"',
                        },
                        {
                            "name": "NPM audit (if applicable)",
                            "run": 'if [ -f "frontend/package.json" ]; then\n  cd frontend\n  npm audit --audit-level=high || echo "⚠️ NPM audit completed with warnings"\nfi',
                        },
                    ],
                },
            },
        }

    @staticmethod
    def get_security_workflow() -> Dict[str, Any]:
        """Generate a comprehensive security workflow template."""
        return {
            "name": "Security Analysis",
            "on": {
                "schedule": [{"cron": "0 2 * * *"}],  # Daily at 2 AM
                "workflow_dispatch": None,
                "push": {"branches": ["main"]},
            },
            "jobs": {
                "codeql-analysis": {
                    "name": "CodeQL Analysis",
                    "runs-on": "ubuntu-latest",
                    "permissions": {
                        "actions": "read",
                        "contents": "read",
                        "security-events": "write",
                    },
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Initialize CodeQL",
                            "uses": "github/codeql-action/init@v3",
                            "with": {"languages": "python,javascript"},
                        },
                        {
                            "name": "Perform CodeQL Analysis",
                            "uses": "github/codeql-action/analyze@v3",
                        },
                    ],
                },
                "dependency-scan": {
                    "name": "Dependency Vulnerability Scan",
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v5",
                            "with": {"python-version": "3.11"},
                        },
                        {
                            "name": "Advanced Python Security Scan",
                            "run": "pip install safety pip-audit\ncd backend\nsafety check -r requirements-base.txt --json > safety-results.json || true\npip-audit -r requirements-base.txt --format=json --output=pip-audit-results.json || true",
                        },
                        {
                            "name": "Node.js Security Audit",
                            "if": "hashFiles('frontend/package.json') != ''",
                            "run": "cd frontend\nnpm audit --json > npm-audit-results.json || true",
                        },
                    ],
                },
            },
        }

    @staticmethod
    def get_deployment_validation_workflow() -> Dict[str, Any]:
        """Generate a deployment validation workflow template."""
        return {
            "name": "Deployment Validation",
            "on": {
                "workflow_dispatch": {
                    "inputs": {
                        "platform": {
                            "description": "Deployment platform",
                            "required": True,
                            "default": "render",
                            "type": "choice",
                            "options": ["render", "fly", "railway"],
                        },
                        "environment": {
                            "description": "Target environment",
                            "required": True,
                            "default": "staging",
                            "type": "choice",
                            "options": ["staging", "production"],
                        },
                    }
                }
            },
            "jobs": {
                "validate-deployment": {
                    "name": "Validate Deployment Configuration",
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Validate deployment configuration",
                            "run": "./scripts/deploy.sh ${{ github.event.inputs.platform }} ${{ github.event.inputs.environment }} --validate-only",
                        },
                        {
                            "name": "Build validation",
                            "run": "docker build -f backend/Dockerfile .",
                        },
                    ],
                }
            },
        }


class CIWorkflowSetup:
    """Main class for CI workflow setup and management."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.workflows_dir = self.project_root / ".github" / "workflows"

    def ensure_workflows_directory(self):
        """Ensure the .github/workflows directory exists."""
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Workflows directory ensured at: {self.workflows_dir}")

    def generate_workflow(
        self, workflow_type: str, output_file: Optional[str] = None
    ) -> str:
        """Generate a workflow file based on type."""
        templates = {
            "ci": WorkflowTemplates.get_ci_workflow,
            "security": WorkflowTemplates.get_security_workflow,
            "deployment": WorkflowTemplates.get_deployment_validation_workflow,
        }

        if workflow_type not in templates:
            raise ValueError(
                f"Unknown workflow type: {workflow_type}. Available: {list(templates.keys())}"
            )

        workflow_content = templates[workflow_type]()

        if output_file is None:
            output_file = f"{workflow_type}.yml"

        self.ensure_workflows_directory()
        output_path = self.workflows_dir / output_file

        with open(output_path, "w") as f:
            yaml.dump(workflow_content, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Generated {workflow_type} workflow at: {output_path}")
        return str(output_path)

    def validate_workflow(self, workflow_file: Path) -> Dict[str, Any]:
        """Validate a workflow file."""
        result = {"valid": False, "errors": [], "warnings": [], "info": []}

        try:
            if not workflow_file.exists():
                result["errors"].append(
                    f"Workflow file does not exist: {workflow_file}"
                )
                return result

            with open(workflow_file, "r") as f:
                workflow_data = yaml.safe_load(f)

            # Basic validation checks
            required_fields = ["name", "jobs"]
            for field in required_fields:
                if field not in workflow_data:
                    result["errors"].append(f"Missing required field: {field}")

            # Check for 'on' field (can be parsed as True/boolean or 'on' string)
            if "on" not in workflow_data and True not in workflow_data:
                result["errors"].append(
                    "Missing required field: on (workflow triggers)"
                )

            # Check for outdated action versions
            outdated_actions = {
                "actions/checkout@v2": "actions/checkout@v4",
                "actions/checkout@v3": "actions/checkout@v4",
                "actions/setup-python@v3": "actions/setup-python@v5",
                "actions/setup-python@v4": "actions/setup-python@v5",
                "actions/setup-node@v2": "actions/setup-node@v4",
                "actions/setup-node@v3": "actions/setup-node@v4",
                "actions/cache@v2": "actions/cache@v4",
                "actions/cache@v3": "actions/cache@v4",
            }

            workflow_str = str(workflow_data)
            for old_action, new_action in outdated_actions.items():
                if old_action in workflow_str:
                    result["warnings"].append(
                        f"Outdated action found: {old_action} -> consider updating to {new_action}"
                    )

            # Check for Python version consistency
            if "PYTHON_VERSION" in workflow_str:
                result["info"].append(
                    "Python version is configured in environment variables"
                )

            result["valid"] = len(result["errors"]) == 0

        except yaml.YAMLError as e:
            result["errors"].append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")

        return result

    def validate_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Validate all workflow files in the project."""
        results = {}

        if not self.workflows_dir.exists():
            logger.warning(f"Workflows directory does not exist: {self.workflows_dir}")
            return results

        for workflow_file in self.workflows_dir.glob("*.yml"):
            results[workflow_file.name] = self.validate_workflow(workflow_file)

        return results

    def init_project(self, project_name: str, features: List[str] = None):
        """Initialize CI infrastructure for a new project."""
        features = features or ["ci", "security", "deployment"]

        logger.info(f"Initializing CI infrastructure for project: {project_name}")

        # Generate workflow files
        generated_files = []
        for feature in features:
            try:
                file_path = self.generate_workflow(feature)
                generated_files.append(file_path)
            except ValueError:
                logger.warning(f"Skipping unknown feature: {feature}")

        # Create basic project structure files if they don't exist
        self._create_project_files(project_name)

        logger.info(
            f"Project initialization complete. Generated files: {generated_files}"
        )
        return generated_files

    def _create_project_files(self, project_name: str):
        """Create basic project structure files."""
        files_to_create = {
            ".gitignore": self._get_gitignore_content(),
            "README.md": self._get_readme_content(project_name),
            "requirements-base.txt": self._get_requirements_content(),
            "pytest.ini": self._get_pytest_config(),
        }

        for filename, content in files_to_create.items():
            file_path = self.project_root / filename
            if not file_path.exists():
                with open(file_path, "w") as f:
                    f.write(content)
                logger.info(f"Created: {file_path}")

    def _get_gitignore_content(self) -> str:
        """Get .gitignore content for Python projects."""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Environment
.env
.env.local
.env.production

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# OS
.DS_Store
Thumbs.db
"""

    def _get_readme_content(self, project_name: str) -> str:
        """Get README.md content."""
        return f"""# {project_name}

## Overview

Brief description of your project.

## Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd {project_name.lower().replace(' ', '-')}

# Install dependencies
pip install -r requirements-base.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run the application
python app/main.py
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline**: Runs tests, linting, and security scans on every push
- **Security Analysis**: Daily security scans and vulnerability assessments
- **Deployment Validation**: Validates deployment configurations

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests locally
4. Create a pull request

## License

This project is licensed under the Creative Commons BY-NC-SA 4.0 license.
"""

    def _get_requirements_content(self) -> str:
        """Get basic requirements.txt content."""
        return """# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2
python-dotenv==1.0.0

# Testing (dev)
pytest==7.4.4
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code quality (dev)
flake8==6.1.0
black==23.12.1
mypy==1.8.0
"""

    def _get_pytest_config(self) -> str:
        """Get pytest configuration."""
        return """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
"""


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="CI Workflow Setup Script for MarkerEngine Projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ci-workflow-setup.py generate --type ci
  python ci-workflow-setup.py generate --type security --output custom-security.yml
  python ci-workflow-setup.py validate --all
  python ci-workflow-setup.py validate --file .github/workflows/ci.yml
  python ci-workflow-setup.py init --project-name "My New Project" --features ci security
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate workflow files")
    generate_parser.add_argument(
        "--type",
        choices=["ci", "security", "deployment"],
        required=True,
        help="Type of workflow to generate",
    )
    generate_parser.add_argument(
        "--output", help="Output filename (defaults to <type>.yml)"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate workflow files")
    validate_group = validate_parser.add_mutually_exclusive_group(required=True)
    validate_group.add_argument(
        "--all", action="store_true", help="Validate all workflows"
    )
    validate_group.add_argument("--file", help="Validate specific workflow file")

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize CI infrastructure for a new project"
    )
    init_parser.add_argument(
        "--project-name", required=True, help="Name of the project"
    )
    init_parser.add_argument(
        "--features",
        nargs="+",
        default=["ci", "security", "deployment"],
        choices=["ci", "security", "deployment"],
        help="Features to enable (default: all)",
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize the setup class
    setup = CIWorkflowSetup()

    try:
        if args.command == "generate":
            output_file = setup.generate_workflow(args.type, args.output)
            print(f"✅ Generated workflow: {output_file}")

        elif args.command == "validate":
            if args.all:
                results = setup.validate_all_workflows()
                print("🔍 Validation Results:")
                print("=" * 50)

                all_valid = True
                for filename, result in results.items():
                    status = "✅ VALID" if result["valid"] else "❌ INVALID"
                    print(f"{status} {filename}")

                    for error in result["errors"]:
                        print(f"  ❌ ERROR: {error}")
                    for warning in result["warnings"]:
                        print(f"  ⚠️  WARNING: {warning}")
                    for info in result["info"]:
                        print(f"  ℹ️  INFO: {info}")
                    print()

                    if not result["valid"]:
                        all_valid = False

                if all_valid:
                    print("🎉 All workflows are valid!")
                else:
                    print("⚠️  Some workflows have issues that need attention.")
                    sys.exit(1)
            else:
                result = setup.validate_workflow(Path(args.file))
                status = "✅ VALID" if result["valid"] else "❌ INVALID"
                print(f"{status} {args.file}")

                for error in result["errors"]:
                    print(f"  ❌ ERROR: {error}")
                for warning in result["warnings"]:
                    print(f"  ⚠️  WARNING: {warning}")
                for info in result["info"]:
                    print(f"  ℹ️  INFO: {info}")

                if not result["valid"]:
                    sys.exit(1)

        elif args.command == "init":
            generated_files = setup.init_project(args.project_name, args.features)
            print(f"🚀 Initialized CI infrastructure for '{args.project_name}'")
            print("Generated files:")
            for file_path in generated_files:
                print(f"  ✅ {file_path}")
            print("\nNext steps:")
            print("1. Review and customize the generated workflow files")
            print("2. Commit and push to your repository")
            print("3. Configure any required secrets in GitHub repository settings")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
