# CI/CD Pipeline Documentation

This document explains the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Automated Trading System.

## Table of Contents

- [Overview](#overview)
- [Pipeline Stages](#pipeline-stages)
- [Configuration](#configuration)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Environment Setup](#environment-setup)
- [Security Considerations](#security-considerations)
- [Deployment Process](#deployment-process)
- [Troubleshooting](#troubleshooting)

## Overview

The CI/CD pipeline automates testing, building, and deployment of the Automated Trading System. It ensures code quality, identifies issues early, and streamlines the deployment process.

### Pipeline Triggers

The pipeline is triggered on:

- **Push** to `main` or `develop` branches
- **Pull Requests** targeting `main` or `develop` branches
- **Weekly** schedule (Sunday at midnight UTC)

## Pipeline Stages

The CI/CD pipeline consists of the following stages:

1. **Linting & Code Quality**
   - Code formatting (black)
   - Import sorting (isort)
   - Static analysis (flake8)
   - Type checking (mypy)

2. **Testing**
   - Unit tests
   - Integration tests
   - Mock tests
   - Test coverage analysis

3. **Security**
   - Dependency vulnerability scanning (safety)
   - Code security scanning (bandit)

4. **Build**
   - Python package building
   - Docker image building

5. **Deployment**
   - Staging deployment (on push to `develop`)
   - Production deployment (on push to `main`)

6. **Publishing**
   - PyPI package publishing (on release tags)

## Configuration

The CI/CD pipeline is configured using GitHub Actions. The main configuration file is located at `.github/workflows/ci_cd.yml` (or `ci_cd_config.yml` at the project root).

### Required Secrets

The following secrets must be configured in the GitHub repository settings:

| Secret Name | Purpose |
|-------------|---------|
| `DOCKERHUB_USERNAME` | Docker Hub username for image publishing |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `AWS_ACCESS_KEY_ID` | AWS access key for deployments |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for deployments |
| `PYPI_API_TOKEN` | PyPI API token for package publishing |

## GitHub Actions Workflows

### Lint Job

The lint job performs code quality checks:

```yaml
lint:
  name: Code Quality and Linting
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Check code formatting with black
      run: |
        black --check app tests
    
    - name: Check import sorting with isort
      run: |
        isort --check-only --profile black app tests
    
    - name: Lint with flake8
      run: |
        flake8 app tests
    
    - name: Check type hints with mypy
      run: |
        mypy app
```

### Test Job

The test job runs the application tests:

```yaml
test:
  name: Run Tests
  runs-on: ubuntu-latest
  needs: lint
  strategy:
    matrix:
      python-version: ['3.8', '3.9', '3.10']
      test-type: ['unit', 'integration', 'mock']
  
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run ${{ matrix.test-type }} tests
      run: |
        python run_tests.py --${{ matrix.test-type }}
```

### Coverage Job

The coverage job analyzes test coverage:

```yaml
coverage:
  name: Test Coverage
  runs-on: ubuntu-latest
  needs: lint
  
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests with coverage
      run: |
        python run_tests.py --unit --integration --mock --coverage
    
    - name: Upload coverage report
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
        verbose: true
```

### Security Scan Job

The security scan job checks for vulnerabilities:

```yaml
security-scan:
  name: Security Scan
  runs-on: ubuntu-latest
  needs: lint
  
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install bandit safety
    
    - name: Scan code with Bandit
      run: |
        bandit -r app -f json -o bandit-results.json
    
    - name: Check dependencies with Safety
      run: |
        safety check -r requirements.txt --full-report
```

### Docker Build Job

The Docker build job creates and publishes a Docker image:

```yaml
docker-build:
  name: Build Docker Image
  runs-on: ubuntu-latest
  needs: [test, coverage]
  if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')
  
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Extract metadata for Docker
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: yourorganization/voicetradewithschwab
        tags: |
          type=ref,event=branch
          type=semver,pattern={{version}}
          type=sha,format=short
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=registry,ref=yourorganization/voicetradewithschwab:buildcache
        cache-to: type=registry,ref=yourorganization/voicetradewithschwab:buildcache,mode=max
```

### Deployment Jobs

The deployment jobs automate the deployment process:

```yaml
deploy-staging:
  name: Deploy to Staging
  runs-on: ubuntu-latest
  needs: docker-build
  if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
  environment: staging
  
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install deployment tools
      run: |
        python -m pip install --upgrade pip
        pip install ansible
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Deploy to staging environment
      run: |
        ansible-playbook -i deploy/inventory/staging.yml deploy/deploy.yml --extra-vars "environment=staging version=${{ github.sha }}"
```

## Environment Setup

### Deployment Environments

The pipeline uses GitHub Environments for deployment:

1. **Staging Environment**
   - Triggered on pushes to the `develop` branch
   - Used for testing in a production-like environment
   - Configured with staging-specific variables

2. **Production Environment**
   - Triggered on pushes to the `main` branch
   - Deployed to production servers
   - Requires approval before deployment

### Environment Configuration

To set up the environments in GitHub:

1. Go to repository settings
2. Navigate to "Environments"
3. Create "staging" and "production" environments
4. Configure environment-specific secrets
5. Set up required reviewers for production deployment

## Security Considerations

### Secret Management

All sensitive information is stored as GitHub Secrets:

- Never hardcode credentials in workflows
- Rotate secrets periodically
- Use environment-specific secrets when appropriate

### Code Scanning

The pipeline includes security scanning:

- Dependencies are checked for vulnerabilities
- Code is scanned for security issues
- Results are uploaded as artifacts

### Approvals and Protections

- Production deployments require manual approval
- Branch protection rules prevent direct pushes to main/develop
- Pull request reviews are required before merging

## Deployment Process

The deployment process follows these steps:

1. **Build and Test**: Code is built and tested thoroughly
2. **Docker Image**: A Docker image is created and pushed to Docker Hub
3. **Ansible Deployment**: Ansible playbooks deploy the application
4. **Verification**: Post-deployment verification ensures the system is operational

### Ansible Playbooks

The deployment uses Ansible playbooks located in the `deploy/` directory:

- `deploy/inventory/`: Contains environment-specific inventory files
- `deploy/deploy.yml`: Main deployment playbook
- `deploy/roles/`: Contains deployment roles

## Troubleshooting

### Common Issues

#### Failed Tests

If tests fail in the pipeline:

1. Check the test logs in GitHub Actions
2. Run the failing tests locally
3. Fix issues and push changes

#### Deployment Failures

If deployment fails:

1. Check the deployment logs
2. Verify environment configuration
3. Ensure infrastructure is available
4. Check network connectivity

#### Security Scan Alerts

If security scans report issues:

1. Review the security scan results
2. Address high-priority vulnerabilities immediately
3. Create tickets for lower priority issues
4. Update dependencies if needed

### Contacting Support

For pipeline issues:

1. Check existing GitHub Issues
2. Open a new issue with detailed information
3. Contact the DevOps team for urgent issues

## Testing in CI/CD

### Test Organization

The project follows a standard Python package structure, which is critical for proper test discovery and execution in CI/CD:

```
automated-trading/
├── app/                        # Main application package
│   ├── api/                    # API modules
│   ├── services/               # Service modules
│   └── ...                     # Other application modules
├── tests/                      # Test directory
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── ...                     # Other test types
├── run_tests.py                # Main test runner
└── ...                         # Other project files
```

This structure allows for clean imports in test files:

```python
# Proper imports in test files
from app.services.trading_service import TradingService
from app.api.schwab_client import SchwabAPIClient
```

No path manipulation is needed in test files, ensuring consistent behavior across different environments.

### Test Execution

Tests are run as part of the CI/CD pipeline using the `run_tests.py` script:

```yaml
- name: Run Tests
  run: python run_tests.py --${{ matrix.test-type }}
```

The test types are configured based on the matrix strategy:

```yaml
strategy:
  matrix:
    test-type: ['unit', 'integration', 'mock']
```

### Coverage Analysis

Test coverage is calculated and enforced using the `--coverage` flag:

```yaml
- name: Run Coverage Analysis
  run: python run_tests.py --unit --integration --mock --coverage
```

Coverage reports are generated in the `coverage_reports/` directory and uploaded as artifacts. 