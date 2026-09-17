"""
Backtesting module: validate optimizer performance on historical data.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys

from mean_variance_optimizer import MeanVarianceOptimizer
from sma_quant_core.models import Asset, PortfolioConstraints, PortfolioConstraint
from sma_quant_core.backtester import Backtester


def generate_synthetic_prices(n_days=252 * 3, n_assets=5, seed=42):
    """Generate synthetic price data for backtesting."""
    np.random.seed(seed)

    dates = pd.date_range(start="2020-01-01", periods=n_days, freq="D")

    # Asset returns (from sample data)
    asset_returns = [0.08, 0.07, 0.04, 0.06, 0.03]
    asset_vols = [0.15, 0.18, 0.05, 0.12, 0.15]

    # Generate correlated returns
    asset_ids = ["VTSAX", "VTIAX", "BND", "VGSLX", "GLD"]
    price_data = {}

    for i, (asset_id, annual_ret, annual_vol) in enumerate(zip(asset_ids, asset_returns, asset_vols)):
        daily_ret = annual_ret / 252
        daily_vol = annual_vol / np.sqrt(252)

        returns = np.random.normal(daily_ret, daily_vol, n_days)
        prices = 100 * np.exp(np.cumsum(returns))
        price_data[asset_id] = pd.Series(prices, index=dates)

    return price_data


def backtest_optimization_strategy(assets, constraints, price_series, start_date, end_date):
    """
    Backtest: rebalance quarterly using mean-variance optimizer.

    Args:
        assets: List of Asset objects
        constraints: PortfolioConstraints
        price_series: {asset_id: pd.Series of prices}
        start_date: Backtest start
        end_date: Backtest end

    Returns:
        BacktestResult with performance metrics
    """

    # Create backtester
    backtester = Backtester(assets, price_series, slippage=0.0005, commissions=0.001)

    # Strategy: quarterly rebalance using optimizer
    optimizer = MeanVarianceOptimizer(use_cvxpy=False)

    def strategy_fn(date, market_data):
        """Strategy function: optimize at each rebalance date."""
        # Re-optimize based on latest prices
        portfolio = optimizer.optimize(
            assets,
            constraints,
            objective="max_sharpe",
        )
        return portfolio.weights

    # Run backtest
    result = backtester.run(
        strategy_fn,
        start_date,
        end_date,
        initial_capital=1000000.0,
        rebalance_frequency="quarterly",
    )

    return result


def main():
    """Run backtest and report results."""

    # Load assets and constraints
    with open("data/sample_assets.json") as f:
        assets_data = json.load(f)
    assets = [Asset(**a) for a in assets_data]

    with open("data/sample_constraints.json") as f:
        constraints_data = json.load(f)

    constraints = PortfolioConstraints(budget_constraint=constraints_data.get("budget_constraint", 1.0))
    for c in constraints_data.get("constraints", []):
        constraints.constraints.append(PortfolioConstraint(**c))

    # Generate synthetic price data
    print("Generating synthetic price data...")
    price_series = generate_synthetic_prices(n_days=252 * 3, n_assets=5, seed=42)

    # Run backtest
    print("Running backtest: quarterly rebalancing with mean-variance optimization...")
    start_date = datetime(2020, 1, 2)
    end_date = datetime(2022, 12, 30)

    result = backtest_optimization_strategy(assets, constraints, price_series, start_date, end_date)

    # Print results
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80)
    print(f"Period: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}")
    print(f"Initial Capital: ${result.initial_capital:,.0f}")
    print(f"Final Capital: ${result.final_capital:,.0f}")
    print()
    print(f"Total Return: {result.total_return:.2%}")
    print(f"Annual Return: {result.annual_return:.2%}")
    print(f"Volatility: {result.volatility:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.4f}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")
    print(f"Sortino Ratio: {result.sortino_ratio:.4f}")
    print(f"Win Rate: {result.win_rate:.2%}")
    print()
    print(f"Total Trades: {len(result.trades)}")
    if result.trades:
        total_costs = sum(t['cost'] for t in result.trades)
        print(f"Total Transaction Costs: ${total_costs:,.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
