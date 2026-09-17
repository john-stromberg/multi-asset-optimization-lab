"""
Robustness checks: validate optimizer stability and sensitivity.
"""

import json
import numpy as np
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mean_variance_optimizer import MeanVarianceOptimizer
from sma_quant_core.models import Asset, PortfolioConstraints, PortfolioConstraint


def load_data():
    """Load sample assets and constraints."""
    data_dir = Path(__file__).parent.parent / "data"

    with open(data_dir / "sample_assets.json") as f:
        assets_data = json.load(f)
    assets = [Asset(**a) for a in assets_data]

    with open(data_dir / "sample_constraints.json") as f:
        constraints_data = json.load(f)

    constraints = PortfolioConstraints(budget_constraint=constraints_data.get("budget_constraint", 1.0))
    for c in constraints_data.get("constraints", []):
        constraints.constraints.append(PortfolioConstraint(**c))

    return assets, constraints


def test_return_perturbations():
    """Test optimizer sensitivity to small return changes."""
    assets, constraints = load_data()
    optimizer = MeanVarianceOptimizer(use_cvxpy=False)

    # Base case
    p_base = optimizer.optimize(assets, constraints, objective="max_sharpe")

    print("Sensitivity: Return Perturbations")
    print("="*80)
    print(f"Base Sharpe: {p_base.sharpe_ratio:.4f}")
    print()

    # Perturb each asset return by ±10%
    for i, asset in enumerate(assets):
        original_return = asset.expected_return

        # Down 10%
        asset.expected_return = original_return * 0.9
        p_down = optimizer.optimize(assets, constraints, objective="max_sharpe")

        # Up 10%
        asset.expected_return = original_return * 1.1
        p_up = optimizer.optimize(assets, constraints, objective="max_sharpe")

        # Restore
        asset.expected_return = original_return

        weight_base = p_base.weights.get(asset.id, 0)
        weight_down = p_down.weights.get(asset.id, 0)
        weight_up = p_up.weights.get(asset.id, 0)

        print(f"{asset.id}: return ±10%")
        print(f"  Base weight:   {weight_base:.2%}")
        print(f"  Down (-10%):   {weight_down:.2%}  (Δ {weight_down - weight_base:+.2%})")
        print(f"  Up   (+10%):   {weight_up:.2%}   (Δ {weight_up - weight_base:+.2%})")
        print()


def test_volatility_perturbations():
    """Test optimizer sensitivity to volatility changes."""
    assets, constraints = load_data()
    optimizer = MeanVarianceOptimizer(use_cvxpy=False)

    # Base case
    p_base = optimizer.optimize(assets, constraints, objective="max_sharpe")

    print("Sensitivity: Volatility Perturbations")
    print("="*80)
    print(f"Base Sharpe: {p_base.sharpe_ratio:.4f}")
    print()

    # Perturb each asset volatility by ±15%
    for i, asset in enumerate(assets):
        original_vol = asset.volatility

        # Down 15%
        asset.volatility = max(0.01, original_vol * 0.85)
        p_down = optimizer.optimize(assets, constraints, objective="max_sharpe")

        # Up 15%
        asset.volatility = original_vol * 1.15
        p_up = optimizer.optimize(assets, constraints, objective="max_sharpe")

        # Restore
        asset.volatility = original_vol

        weight_base = p_base.weights.get(asset.id, 0)
        weight_down = p_down.weights.get(asset.id, 0)
        weight_up = p_up.weights.get(asset.id, 0)

        print(f"{asset.id}: volatility ±15%")
        print(f"  Base weight:   {weight_base:.2%}")
        print(f"  Down (-15%):   {weight_down:.2%}  (Δ {weight_down - weight_base:+.2%})")
        print(f"  Up   (+15%):   {weight_up:.2%}   (Δ {weight_up - weight_base:+.2%})")
        print()


def test_constraint_infeasibility():
    """Test optimizer behavior when constraints become infeasible."""
    assets, constraints = load_data()
    optimizer = MeanVarianceOptimizer(use_cvxpy=False)

    print("Edge Case: Infeasible Constraints")
    print("="*80)

    # Test with increasingly restrictive min_return
    for min_ret in [0.05, 0.08, 0.12]:
        constraints_test = PortfolioConstraints()
        constraints_test.constraints = constraints.constraints.copy()
        constraints_test.add_return_constraint(min_return=min_ret)

        try:
            portfolio = optimizer.optimize(
                assets,
                constraints_test,
                objective="max_sharpe",
            )
            print(f"Min Return {min_ret:.0%}: feasible | Sharpe {portfolio.sharpe_ratio:.4f}")
        except Exception as e:
            print(f"Min Return {min_ret:.0%}: infeasible | {str(e)[:50]}")


def test_zero_volatility():
    """Test optimizer with risk-free asset (zero volatility)."""
    assets, constraints = load_data()

    # Add risk-free asset
    risk_free = Asset(
        id="RF",
        name="Risk-Free Asset",
        asset_class="cash",
        expected_return=0.02,
        volatility=0.0,
        current_price=1.0,
    )
    assets.append(risk_free)

    optimizer = MeanVarianceOptimizer(use_cvxpy=False)

    print("Edge Case: Risk-Free Asset (Zero Volatility)")
    print("="*80)

    portfolio = optimizer.optimize(assets, constraints, objective="max_sharpe")

    print(f"Status: {portfolio.status}")
    print(f"Portfolio Sharpe: {portfolio.sharpe_ratio:.4f}")
    print(f"Risk-Free allocation: {portfolio.weights.get('RF', 0):.2%}")


def main():
    """Run all robustness checks."""
    print("\n" + "="*80)
    print("ROBUSTNESS CHECKS: SENSITIVITY & EDGE CASES")
    print("="*80 + "\n")

    test_return_perturbations()
    print()
    test_volatility_perturbations()
    print()
    test_constraint_infeasibility()
    print()
    test_zero_volatility()

    print("\n" + "="*80)
    print("ROBUSTNESS CHECKS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
