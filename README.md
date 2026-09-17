# multi-asset-optimization-lab

Track: **SMA Quantitative Research**

## Research Purpose

Research-grade portfolio optimization using mean-variance theory and constrained optimization.

Demonstrates best practices:
- **Methodology-first**: Explicit assumptions, model choices, robustness checks
- **Research → Production separation**: notebooks for exploration, validated src/ for production
- **Reproducible**: versioned data, pinned dependencies, comprehensive tests
- **Actionable**: decision memos for portfolio managers

## Quick Start

```bash
# Install (requires sma-quant-core)
pip install -e ".[dev,optimization]"

# Run optimization
python src/main.py --objective max_sharpe --output reports/

# Run tests
pytest tests/ -v --cov=src
```

## Architecture

```
├── src/
│   ├── mean_variance_optimizer.py    # IOptimizer implementation
│   └── main.py                       # CLI entry point
├── research/                         # Exploratory notebooks
├── tests/
│   ├── test_mean_variance.py         # Unit tests (5 tests)
│   └── test_integration.py           # End-to-end workflows (4 tests)
├── data/
│   ├── sample_assets.json            # 5-asset portfolio
│   └── sample_constraints.json       # Portfolio constraints
├── reports/                          # Generated decision memos & portfolios
└── pyproject.toml                    # Dependencies + dev tools
```

## Key Components

### MeanVarianceOptimizer

Implements `sma_quant_core.interfaces.IOptimizer`:
- **Objectives**: maximize Sharpe ratio, minimize volatility, target return
- **Solver**: cvxpy (robust) or fallback to equal-weight
- **Constraints**: weight bounds, portfolio return/volatility targets
- **Output**: OptimizedPortfolio with weights, metrics, and metadata

### EfficientFrontier

Generates optimal risk-return curve:
- Multiple target returns → frontier points
- Each point: optimal weights for that return level
- Useful for trade-off analysis and PM communication

### Decision Memo

Automatically generated after each optimization:
- **Question**: What portfolio decision are we optimizing?
- **Evidence**: Methodology, assumptions, data
- **Interpretation**: What do results mean for portfolio management?
- **Recommendation**: Specific allocation + rationale
- **Risks**: Model limitations, backtesting caveats

## Development Workflow

**Explore** (develop branch + research/notebooks)
→ **Validate** (unit & integration tests)
→ **Produce** (merge to main, stable CLI)

## Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test
pytest tests/test_mean_variance.py::test_optimize_max_sharpe -v
```

**Results**: 9/9 passing
- Unit tests: asset handling, optimization convergence, constraint satisfaction, edge cases
- Integration tests: end-to-end workflows, efficient frontier generation, sensitivity analysis

## Methodology

### Mean-Variance Theory

Markowitz (1952) framework:
- Assumes normal return distributions
- Utility = E[R] - λ·σ² (risk aversion)
- Solves: argmax Sharpe = (E[R] - Rf) / σ subject to constraints

### Key Assumptions

1. Returns normally distributed
2. Historical correlations persist
3. Expected returns/volatility accurately estimated
4. No transaction costs in modeling

### Limitations

- Real markets have fat tails (underestimates extreme risk)
- Correlations break down in market stress
- Point estimates are uncertain

### Extensions (TODO)

- [ ] Black-Litterman (incorporate views)
- [ ] Factor-aware optimization (Fama-French)
- [ ] Robust optimization (worst-case scenarios)
- [ ] Dynamic allocation (multi-period)

## Decision Memo Example

```markdown
# Portfolio Optimization Results

**Question**: What asset allocation maximizes risk-adjusted return?

**Evidence**: Mean-variance optimization on 5 assets (US/Intl stocks, bonds, real estate, gold)
with constraints: weight bounds, min 5% return, max 12% volatility.

**Interpretation**: Optimal allocation achieves 0.52 Sharpe ratio with 6.5% expected return
and 9.8% volatility.

**Recommendation**:
- US Stocks (VTSAX): 40%
- Intl Stocks (VTIAX): 20%
- Bonds (BND): 25%
- Real Estate (VGSLX): 10%
- Gold (GLD): 5%

**Risks**:
- Model assumes historical 3-year correlations persist
- Backtested on sample data; implementation includes transaction costs
- Constraints may become infeasible if markets stress
```

## Contributing

1. Create feature branch from develop
2. Implement + test with `pytest`
3. Add test cases to `tests/`
4. Run: `pytest --cov=src` + `black src/` + `flake8 src/`
5. Submit PR with decision memo (if applicable)

## References

- Markowitz, H. (1952). "Portfolio Selection" - Foundational mean-variance paper
- Boyd & Vandenberghe (2004). "Convex Optimization" - Optimization theory
- cvxpy Docs: https://www.cvxpy.org/
- sma-quant-core: https://github.com/john-stromberg/sma-quant-core
