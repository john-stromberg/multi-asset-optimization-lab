# Production Validation Framework

## Overview

This document outlines the validation strategy for promoting portfolio optimization research from **develop** (research branch) to **main** (production).

## Validation Stages

### Stage 1: Unit Tests ✓
- **Location**: `tests/test_mean_variance.py`
- **Coverage**: 5 unit tests
  - Optimizer initialization
  - Sharpe ratio maximization
  - Constraint satisfaction
  - Efficient frontier generation
  - Edge cases (empty assets)

### Stage 2: Integration Tests ✓
- **Location**: `tests/test_integration.py`
- **Coverage**: 4 end-to-end workflow tests
  - Full optimization workflow (optimize → validate → report)
  - Efficient frontier generation and analysis
  - Sensitivity to return targets
  - Constraint binding

### Stage 3: Backtesting
- **Location**: `src/backtest.py`
- **Methodology**:
  - Quarterly rebalancing strategy
  - 3-year historical period (synthetic data)
  - Realistic slippage (0.05%) and commissions (0.1%)
  - Metrics: total return, Sharpe ratio, max drawdown, win rate
- **Success Criteria**:
  - Positive cumulative returns
  - Sharpe ratio ≥ 0.4
  - Max drawdown ≤ -40%

### Stage 4: Robustness Checks
- **Location**: `tests/test_robustness.py`
- **Checks**:
  - Return perturbations (±10%): weight changes should be stable
  - Volatility perturbations (±15%): allocation sensitivity
  - Constraint infeasibility: graceful handling
  - Edge cases: risk-free assets, zero-volatility instruments

## Validation Gates

| Stage | Gate | Status | Approval |
|-------|------|--------|----------|
| Unit Tests | Pass all 5 tests | ✓ | Automated (CI/CD) |
| Integration Tests | Pass all 4 tests | ✓ | Automated (CI/CD) |
| Backtesting | Positive return, Sharpe ≥ 0.4 | ⏳ | Manual review |
| Robustness | Allocations stable under perturbations | ⏳ | Manual review |

## Deployment Checklist

- [ ] All unit & integration tests passing (CI/CD)
- [ ] Backtest results documented (returns, metrics, market regime)
- [ ] Robustness report complete (sensitivity analysis, edge cases)
- [ ] Decision memo reviewed by PM (recommendation sound, risks documented)
- [ ] Code reviewed (logic clear, edge cases handled, documentation complete)
- [ ] Merge to main branch
- [ ] Tag release (e.g., v0.2.0)

## Success Metrics

- **Correctness**: Unit + integration tests pass
- **Stability**: Allocations robust to parameter changes
- **Performance**: Backtest Sharpe ≥ 0.4, positive cumulative return
- **Explainability**: Decision memo clearly communicates findings and risks

## Known Limitations

1. **Equal-weight fallback**: Without cvxpy, optimizer returns equal-weight allocation (constraint-aware optimizer requires convex optimization library)
2. **Synthetic backtests**: Historical correlation/volatility may not persist
3. **Transaction costs**: Modest slippage/commissions; real markets may differ
4. **Static constraints**: Model assumes constraints don't change during backtest period

## Next Steps

1. Install cvxpy for true mean-variance optimization
2. Backtest on real historical price data
3. Add performance attribution (factor contributions)
4. Extend to multi-period dynamic allocation
