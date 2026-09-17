"""
Main entry point: run optimization and generate reports.
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
import sys

from src.mean_variance_optimizer import MeanVarianceOptimizer, EfficientFrontier
from sma_quant_core.models import Asset, PortfolioConstraints, PortfolioConstraint
from sma_quant_core.reporting import DecisionMemo, ReportGenerator


def load_assets(filepath):
    """Load assets from JSON."""
    with open(filepath) as f:
        data = json.load(f)
    return [Asset(**item) for item in data]


def load_constraints(filepath):
    """Load constraints from JSON."""
    with open(filepath) as f:
        data = json.load(f)

    constraints = PortfolioConstraints(budget_constraint=data.get("budget_constraint", 1.0))
    for c in data.get("constraints", []):
        constraints.constraints.append(PortfolioConstraint(**c))

    return constraints


def main():
    parser = argparse.ArgumentParser(description="Multi-Asset Portfolio Optimization")
    parser.add_argument("--assets", default="data/sample_assets.json", help="Assets JSON file")
    parser.add_argument("--constraints", default="data/sample_constraints.json", help="Constraints JSON file")
    parser.add_argument("--objective", default="max_sharpe", choices=["max_sharpe", "min_volatility", "target_return"])
    parser.add_argument("--target-return", type=float, default=None, help="Target return for target_return objective")
    parser.add_argument("--use-cvxpy", action="store_true", help="Use cvxpy if available")
    parser.add_argument("--frontier", action="store_true", help="Generate efficient frontier")
    parser.add_argument("--output", default="reports", help="Output directory for reports")

    args = parser.parse_args()

    # Load data
    print("Loading assets and constraints...")
    assets = load_assets(args.assets)
    constraints = load_constraints(args.constraints)

    print(f"Loaded {len(assets)} assets")

    # Create optimizer
    opt = MeanVarianceOptimizer(use_cvxpy=args.use_cvxpy)

    # Optimize
    print(f"Optimizing portfolio ({args.objective})...")
    portfolio = opt.optimize(
        assets,
        constraints,
        objective=args.objective,
        target_return=args.target_return,
    )

    print(f"\nOptimized Portfolio:")
    print(f"  Return: {portfolio.expected_return:.2%}")
    print(f"  Volatility: {portfolio.expected_volatility:.2%}")
    print(f"  Sharpe Ratio: {portfolio.sharpe_ratio:.4f}")
    print(f"\n  Weights:")
    for asset_id, weight in sorted(portfolio.weights.items(), key=lambda x: -x[1]):
        print(f"    {asset_id}: {weight:.2%}")

    # Generate efficient frontier
    if args.frontier:
        print("\nGenerating efficient frontier...")
        frontier = EfficientFrontier(opt)
        points = frontier.generate(assets, constraints, n_points=20)

        print(f"Generated {len(points)} frontier points")
        frontier_report = ReportGenerator.efficient_frontier_report(
            assets, points, portfolio.weights, portfolio.sharpe_ratio
        )

    # Generate decision memo
    memo = DecisionMemo(
        title="Portfolio Optimization Results",
        date=datetime.now(),
        author="Quantitative Research",
        question="What is the optimal asset allocation under given constraints?",
        evidence=f"Mean-variance optimization on {len(assets)} assets. Objective: {args.objective}",
        interpretation=f"Optimal allocation achieves {portfolio.sharpe_ratio:.4f} Sharpe ratio with {portfolio.expected_return:.2%} expected return and {portfolio.expected_volatility:.2%} expected volatility.",
        recommendation=f"Implement allocation: " + ", ".join([f"{a}={w:.1%}" for a, w in sorted(portfolio.weights.items(), key=lambda x: -x[1])]),
        risks=[
            "Model assumes historical correlations persist",
            "Backtested on sample data; real performance may differ",
            "Constraints may become infeasible with market changes",
        ],
        metadata={
            "sharpe_ratio": portfolio.sharpe_ratio,
            "expected_return": portfolio.expected_return,
            "expected_volatility": portfolio.expected_volatility,
            "n_assets": len(assets),
            "optimizer": portfolio.metadata.get("optimizer", "unknown"),
        },
    )

    # Save report
    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    memo_path = output_path / f"decision_memo_{timestamp}.md"
    with open(memo_path, "w") as f:
        f.write(memo.to_markdown())

    print(f"\nDecision memo saved to: {memo_path}")

    # Save portfolio as JSON
    portfolio_path = output_path / f"portfolio_{timestamp}.json"
    with open(portfolio_path, "w") as f:
        json.dump(portfolio.to_dict(), f, indent=2)

    print(f"Portfolio saved to: {portfolio_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
