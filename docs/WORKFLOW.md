# Research to Production Workflow

## Overview

This document defines the process for moving quantitative research from **exploration** (notebooks, experimentation) to **production** (validated, tested, deployed code).

## Phases

### Phase 1: Exploration (develop branch)

**Goal**: Prototype new optimization approach or algorithm

**Activities**:
- Create feature branch: `git checkout -b feature/mean-variance-v2`
- Write exploratory notebooks in `research/`
- Experiment with different parameters, models, constraints
- Document findings and key insights

**Deliverables**:
- Runnable notebook(s) demonstrating the approach
- Preliminary results and metrics
- Known limitations and next steps

**Example**: `research/01_optimization_exploration.ipynb`

```python
# Experiment: test optimizer sensitivity to return assumptions
for assumed_return in [0.05, 0.07, 0.09]:
	assets[0].expected_return = assumed_return
	portfolio = optimizer.optimize(assets, constraints)
	print(f"Return assumption {assumed_return:.1%} → Sharpe {portfolio.sharpe_ratio:.4f}")
```

### Phase 2: Validation (develop → main PR)

**Goal**: Prove the approach is correct, robust, and production-ready

**Validation gates**:

1. **Unit Tests** (automated)
   - Test individual components (optimizer, constraints, metrics)
   - Coverage ≥ 80%
   - All tests pass

2. **Integration Tests** (automated)
   - Test end-to-end workflows
   - Example: optimize → validate → report

3. **Robustness Checks** (manual review on PR)
   - Sensitivity analysis: how do results change with small input changes?
   - Edge cases: empty portfolios, zero-volatility assets, infeasible constraints
   - Stress testing: extreme market conditions

4. **Backtesting** (manual review on PR)
   - Execute strategy on historical data
   - Measure realized returns, Sharpe ratio, drawdowns
   - Compare vs. benchmarks

5. **Code Review** (manual)
   - Is the code clear and maintainable?
   - Are assumptions documented?
   - Are edge cases handled?

**Approval criteria**:
- ✓ All tests passing
- ✓ Coverage ≥ 80%
- ✓ Robustness checks confirm stability
- ✓ Backtest meets success metrics
- ✓ Code reviewed and approved

### Phase 3: Production (main branch)

**Goal**: Deploy validated research as stable, monitored service

**Activities**:
- Merge to main after all gates pass
- Tag release (e.g., `v0.2.0`)
- Monitor metrics (coverage, test success rate, deployment frequency)
- Log any issues and gather user feedback

**Monitoring**:
- CI/CD metrics (build success rate, test execution time)
- Runtime metrics (Sharpe ratio, allocation stability, convergence time)
- User feedback (PM satisfaction, portfolio performance)

## Workflow Diagram

```
Research          Validation           Production
(develop)         (PR review)          (main)

┌─────────────┐   ┌──────────────┐   ┌──────────┐
│ Experiments │──→│ Unit Tests   │──→│ Release  │
│ Notebooks   │   │ Integration  │   │ v0.2.0   │
│ Prototypes  │   │ Coverage     │   │ Deploy   │
└─────────────┘   │ Robustness   │   └──────────┘
				  │ Backtesting  │
				  │ Code Review  │
				  └──────────────┘
```

## Example: Mean-Variance Optimizer

### Phase 1: Exploration

```bash
# Create feature branch
git checkout -b feature/mean-variance-optimizer

# Write exploratory notebook
jupyter notebook research/01_optimization_exploration.ipynb

# Experiment with optimization objectives
# Test efficient frontier generation
# Analyze sensitivity to return assumptions

# Commit and push
git add research/01_optimization_exploration.ipynb
git commit -m "research: explore mean-variance optimization"
git push origin feature/mean-variance-optimizer
```

### Phase 2: Validation

```bash
# Implement production-grade code
# src/mean_variance_optimizer.py (implements IOptimizer interface)

# Write unit tests
# tests/test_mean_variance.py (5 tests, 80% coverage)

# Write integration tests
# tests/test_integration.py (4 tests, end-to-end workflows)

# Run all tests locally
pytest tests/ -v --cov=src --cov-report=html

# Create PR: feature/mean-variance-optimizer → develop
# CI/CD automatically runs tests

# GitHub Actions results:
# ✓ Tests pass on Python 3.10, 3.11
# ✓ Code style: flake8 OK
# ✓ Type checking: mypy OK
# ✓ Coverage: 85%

# Run robustness checks
python tests/test_robustness.py

# Run backtest
python src/backtest.py

# Get code review approval
# Merge PR to develop
```

### Phase 3: Production

```bash
# Create PR: develop → main
# CI/CD validates robustness + backtest

# Once approved, merge to main

# Tag release
git tag -a v0.2.0 -m "Release: mean-variance optimizer with efficient frontier"
git push origin v0.2.0

# Build and push Docker image
docker build -t sma-quantitative/portfolio-optimizer:v0.2.0 .
docker push registry.example.com/sma-quantitative/portfolio-optimizer:v0.2.0

# Monitor production metrics
# - Sharpe ratio > 0.4
# - Allocation changes < 5% month-over-month
# - Zero runtime errors
```

## Decision Memo Template

At each phase transition, document findings in a **Decision Memo**:

```markdown
# Decision Memo: Mean-Variance Optimizer

**Date**: 2026-09-16
**Author**: Quantitative Research Team
**Status**: Ready for Production

## Question
What is the optimal asset allocation under given constraints?

## Evidence
- Mean-variance optimization on 5 assets
- 3-year backtesting period with quarterly rebalancing
- Robustness tests: return/volatility perturbations, edge cases
- Integration tests: 4 end-to-end workflows

## Interpretation
The optimizer achieves 0.59 Sharpe ratio with 5.6% expected return and 6.1% volatility.
Results are stable under ±10% return and ±15% volatility perturbations.
Backtest shows consistent positive returns with max drawdown of -8%.

## Recommendation
Approve for production deployment. Recommend quarterly rebalancing with decision memos
generated automatically after each optimization run.

## Risks
- Equal-weight fallback without cvxpy (install cvxpy for true optimization)
- Model assumes correlations persist (backtest on live data to validate)
- Does not include dynamic hedging (consider for future enhancement)

## Next Steps
- [ ] Install cvxpy in production environment
- [ ] Set up monitoring dashboard
- [ ] Create operational runbook
- [ ] Begin quarterly rebalancing pilot
```

## Branch Protection Rules

Enforce production quality via GitHub branch protection:

```
main branch:
  ✓ Require pull request reviews before merging
  ✓ Require status checks to pass (CI/CD)
  ✓ Require branches to be up to date
  ✓ Require code review approval before merge
  ✓ Require commit signatures

develop branch:
  ✓ Require status checks to pass
  ✓ Optional: require 1 review approval
```

## Checklist: Ready for Production?

Before merging to main:

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Code coverage ≥ 80%
- [ ] Linting passes (flake8, black)
- [ ] Type checking passes (mypy)
- [ ] Robustness checks document stable behavior
- [ ] Backtest shows positive returns and Sharpe ≥ 0.4
- [ ] Code reviewed by peer
- [ ] Decision memo signed off by PM
- [ ] Documentation complete (README, docstrings, assumptions)
- [ ] No hardcoded values or debug prints
- [ ] Error handling for edge cases
- [ ] Monitoring alerts configured

## Metrics to Track

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| Test Coverage | N/A | ≥ 80% | ≥ 80% |
| Backtest Sharpe | Exploratory | ≥ 0.4 | ≥ 0.4 |
| Build Success Rate | N/A | 100% | 100% |
| Code Review Time | N/A | ≤ 2 days | ≤ 2 days |
| Time to Production | N/A | N/A | ≤ 1 week |

## Troubleshooting

**Q: Tests pass locally but fail in CI/CD**
- A: Check Python version (test on 3.10, 3.11), dependency versions, environment variables

**Q: Backtest fails on large datasets**
- A: Reduce dataset size, increase memory limit, optimize algorithm for performance

**Q: Code review takes too long**
- A: Ensure clear documentation, concise PR description, address feedback promptly

**Q: Metrics degraded in production**
- A: Rollback to previous release, investigate root cause, deploy fix to develop first

## References

- Validation Framework: `docs/VALIDATION_FRAMEWORK.md`
- Deployment Guide: `docs/DEPLOYMENT.md`
- sma-quant-core Interfaces: `https://github.com/john-stromberg/sma-quant-core`
