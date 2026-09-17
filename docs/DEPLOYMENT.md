# Deployment & Containerization Guide

## Overview

This guide explains how to deploy the portfolio optimization lab as a containerized service for reproducible research and production use.

## Local Development (Docker Compose)

### Development Container with Jupyter

```bash
# Start development environment with Jupyter Lab
docker-compose up optimizer-dev

# Access Jupyter at http://localhost:8888
# Open research/01_optimization_exploration.ipynb to explore optimization
```

### Test Container

```bash
# Run full test suite in isolated environment
docker-compose up optimizer-test
```

## CI/CD Pipeline

### GitHub Actions Workflow

Location: `.github/workflows/tests.yml`

Triggered on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Pipeline stages**:

1. **Tests** (Python 3.10, 3.11)
   - Install dependencies
   - Lint: flake8
   - Type check: mypy
   - Unit & integration tests with coverage
   - Upload coverage to Codecov

2. **Validation** (PRs to main only)
   - Robustness checks (sensitivity analysis)
   - Backtest validation
   - Only runs if tests pass

### Branch Strategy

- **main**: Production-ready code
  - All tests passing
  - Code reviewed
  - Robustness validated
  - Tagged releases

- **develop**: Research staging
  - Tests passing
  - New features being validated
  - Integration testing

- **feature/xxx**: Development branches
  - Experimental features
  - Local testing before PR

## Deployment Workflow

### Step 1: Create Feature Branch

```bash
git checkout -b feature/new-optimizer

# Make changes, test locally
pytest tests/ -v
```

### Step 2: Push and Create PR

```bash
# Commit and push
git add src/ tests/
git commit -m "feat: new optimization approach"
git push origin feature/new-optimizer

# Create PR on GitHub: feature/new-optimizer → develop
```

### Step 3: Automated Validation

GitHub Actions automatically:
- Runs tests (both Python versions)
- Checks code style
- Validates robustness
- Reports coverage

### Step 4: Code Review

- Peer review the implementation
- Verify decision memo
- Discuss methodology

### Step 5: Merge to Develop

Once approved:
- Merge PR to develop
- Actions re-runs full test suite

### Step 6: Validate Production Readiness

Before merging to main:

```bash
# Run robustness checks locally
python tests/test_robustness.py

# Run backtest
python src/backtest.py

# Generate production decision memo
python src/main.py --objective max_sharpe --output reports/
```

### Step 7: Merge to Main & Release

```bash
# Create PR: develop → main
# CI/CD validates again

# Once approved, merge to main

# Create release tag
git tag -a v0.2.0 -m "Release: mean-variance optimizer"
git push origin v0.2.0
```

## Production Deployment

### Docker Image Build

```bash
# Build image
docker build -t sma-quantitative/portfolio-optimizer:latest .

# Tag for registry
docker tag sma-quantitative/portfolio-optimizer:latest \
  registry.example.com/sma-quantitative/portfolio-optimizer:v0.2.0

# Push to registry
docker push registry.example.com/sma-quantitative/portfolio-optimizer:v0.2.0
```

###  Kubernetes Deployment (Optional)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: optimizer-config
data:
  assets.json: | (base64 encoded sample_assets.json)
  constraints.json: | (base64 encoded sample_constraints.json)

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portfolio-optimizer-api
spec:
  replicas: 2
  selector:
	matchLabels:
	  app: portfolio-optimizer
  template:
	metadata:
	  labels:
		app: portfolio-optimizer
	spec:
	  containers:
	  - name: optimizer
		image: registry.example.com/sma-quantitative/portfolio-optimizer:v0.2.0
		ports:
		- containerPort: 8000
		volumeMounts:
		- name: config
		  mountPath: /app/config
	  volumes:
	  - name: config
		configMap:
		  name: optimizer-config
```

## Monitoring & Logging

### Local Container Logs

```bash
# View logs
docker-compose logs optimizer-dev

# Follow logs
docker-compose logs -f optimizer-test
```

### Production Metrics (Suggested)

- Test coverage (from codecov)
- Build success/failure rate
- Deployment frequency
- Lead time for changes
- Mean time to recovery (MTTR)

## Troubleshooting

### Issue: ModuleNotFoundError

**Cause**: Python path not set correctly in container

**Solution**:
```bash
# Ensure setup.py is installed
pip install -e .

# Or use PYTHONPATH
export PYTHONPATH=/app/src:$PYTHONPATH
```

### Issue: Tests fail in container but pass locally

**Cause**: Python version or dependency mismatch

**Solution**:
```bash
# Check versions in container
docker-compose run optimizer-test python --version

# Rebuild image
docker-compose build --no-cache

# Update pyproject.toml if needed
```

### Issue: Out of memory running backtest

**Cause**: Large price dataset or insufficient container memory

**Solution**:
```bash
# Increase docker memory limit
docker-compose -f docker-compose.yml run \
  --memory 4g \
  optimizer-test \
  pytest tests/test_integration.py -v
```

## Best Practices

1. **Always test locally first**: `pytest -v` before pushing
2. **Use feature branches**: Isolate changes, easier review
3. **Write descriptive commit messages**: Helps with future debugging
4. **Include tests with new code**: Ensures robustness
5. **Document assumptions**: Decision memos for PMs, comments for developers
6. **Tag releases**: Makes it easy to rollback if needed
7. **Monitor production**: Track build/test metrics over time

## Next Steps

- [ ] Set up Codecov integration for coverage tracking
- [ ] Add pre-commit hooks for local linting
- [ ] Integrate with Slack for build notifications
- [ ] Set up production monitoring dashboard
- [ ] Create runbook for operational troubleshooting
