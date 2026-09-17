"""
Mean-variance portfolio optimizer using cvxpy.
Production-ready implementation for constrained portfolio optimization.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

try:
    import cvxpy as cp
    HAS_CVXPY = True
except ImportError:
    HAS_CVXPY = False

from sma_quant_core.models import Asset, PortfolioConstraints, OptimizedPortfolio
from sma_quant_core.interfaces import IOptimizer
from sma_quant_core.metrics import Metrics
from datetime import datetime


class MeanVarianceOptimizer(IOptimizer):
    """
    Mean-Variance Portfolio Optimizer using Markowitz theory.

    Maximizes risk-adjusted return (Sharpe ratio) or minimizes risk subject to constraints.
    """

    def __init__(self, use_cvxpy: bool = True):
        """
        Initialize optimizer.

        Args:
            use_cvxpy: If True, uses cvxpy for robust optimization. If False, uses fallback.
        """
        self.use_cvxpy = use_cvxpy and HAS_CVXPY

    def optimize(
        self,
        assets: List[Asset],
        constraints: PortfolioConstraints,
        correlation_matrix: Optional[np.ndarray] = None,
        risk_free_rate: float = 0.02,
        objective: str = "max_sharpe",  # "max_sharpe", "min_volatility", "target_return"
        target_return: Optional[float] = None,
        **kwargs
    ) -> OptimizedPortfolio:
        """
        Optimize portfolio weights.

        Args:
            assets: List of Asset objects
            constraints: Portfolio constraints
            correlation_matrix: Correlation matrix (if None, assumes independence)
            risk_free_rate: Risk-free rate for Sharpe ratio
            objective: Optimization objective
            target_return: For "target_return" objective
            **kwargs: Additional options

        Returns:
            OptimizedPortfolio with weights and metrics
        """
        if len(assets) == 0:
            raise ValueError("No assets provided")

        n_assets = len(assets)

        if self.use_cvxpy:
            return self._optimize_cvxpy(
                assets, constraints, correlation_matrix, risk_free_rate, objective, target_return
            )
        else:
            return self._optimize_fallback(
                assets, constraints, correlation_matrix, risk_free_rate, objective
            )

    def _optimize_cvxpy(
        self,
        assets: List[Asset],
        constraints: PortfolioConstraints,
        correlation_matrix: Optional[np.ndarray],
        risk_free_rate: float,
        objective: str,
        target_return: Optional[float],
    ) -> OptimizedPortfolio:
        """Optimization using cvxpy (requires cvxpy installation)."""
        if not HAS_CVXPY:
            raise RuntimeError("cvxpy not installed. Install with: pip install cvxpy")

        n = len(assets)

        # Extract returns and volatilities
        returns = np.array([asset.expected_return for asset in assets])
        vols = np.array([asset.volatility for asset in assets])

        # Covariance matrix
        if correlation_matrix is None:
            correlation_matrix = np.eye(n)

        cov = np.diag(vols) @ correlation_matrix @ np.diag(vols)

        # Decision variables
        w = cp.Variable(n)

        # Objective function
        portfolio_return = returns @ w
        portfolio_vol = cp.sqrt(w @ cov @ w)
        sharpe = (portfolio_return - risk_free_rate) / portfolio_vol

        if objective == "max_sharpe":
            prob = cp.Problem(cp.Maximize(sharpe))
        elif objective == "min_volatility":
            prob = cp.Problem(cp.Minimize(portfolio_vol))
        elif objective == "target_return":
            if target_return is None:
                raise ValueError("target_return required for 'target_return' objective")
            prob = cp.Problem(
                cp.Minimize(portfolio_vol),
                [portfolio_return >= target_return]
            )
        else:
            raise ValueError(f"Unknown objective: {objective}")

        # Add constraints
        # Budget constraint
        prob.constraints += [cp.sum(w) == constraints.budget_constraint]

        # Weight bounds and constraints
        for constraint in constraints.constraints:
            if constraint.constraint_type == "min_weight" and constraint.asset_id:
                for i, asset in enumerate(assets):
                    if asset.id == constraint.asset_id:
                        prob.constraints += [w[i] >= constraint.lower_bound]
            elif constraint.constraint_type == "max_weight" and constraint.asset_id:
                for i, asset in enumerate(assets):
                    if asset.id == constraint.asset_id:
                        prob.constraints += [w[i] <= constraint.upper_bound]
            elif constraint.constraint_type == "min_return":
                prob.constraints += [portfolio_return >= constraint.lower_bound]
            elif constraint.constraint_type == "max_volatility":
                prob.constraints += [portfolio_vol <= constraint.upper_bound]

        # Non-negative weights (long-only)
        prob.constraints += [w >= 0]

        # Solve
        try:
            prob.solve(solver=cp.SCS, verbose=False)
        except Exception as e:
            raise RuntimeError(f"Optimization failed: {e}")

        if prob.status != "optimal":
            raise ValueError(f"Optimization did not converge: {prob.status}")

        weights_array = np.array(w.value).flatten()
        weights_dict = {asset.id: float(weights_array[i]) for i, asset in enumerate(assets)}

        # Calculate metrics
        portfolio_ret = float(portfolio_return.value)
        portfolio_volatility = float(portfolio_vol.value)
        sharpe_ratio = (portfolio_ret - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0.0

        return OptimizedPortfolio(
            id=f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            assets=assets,
            weights=weights_dict,
            expected_return=portfolio_ret,
            expected_volatility=portfolio_volatility,
            sharpe_ratio=sharpe_ratio,
            status="success",
            metadata={
                "optimizer": "cvxpy_mean_variance",
                "objective": objective,
                "solver": "SCS",
            },
        )

    def _optimize_fallback(
        self,
        assets: List[Asset],
        constraints: PortfolioConstraints,
        correlation_matrix: Optional[np.ndarray],
        risk_free_rate: float,
        objective: str,
    ) -> OptimizedPortfolio:
        """Fallback: equal-weight allocation with warnings."""
        n = len(assets)
        weights_array = np.ones(n) / n
        weights_dict = {asset.id: float(weights_array[i]) for i, asset in enumerate(assets)}

        metrics = Metrics.portfolio_metrics(weights_array, assets, correlation_matrix, risk_free_rate)

        return OptimizedPortfolio(
            id=f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            assets=assets,
            weights=weights_dict,
            expected_return=metrics["expected_return"],
            expected_volatility=metrics["expected_volatility"],
            sharpe_ratio=metrics["sharpe_ratio"],
            status="warning",
            warnings=["cvxpy not available; using equal-weight fallback"],
            metadata={"optimizer": "fallback_equal_weight"},
        )


class EfficientFrontier:
    """Generate efficient frontier (curve of optimal risk-return combinations)."""

    def __init__(self, optimizer: IOptimizer):
        """Initialize with an optimizer instance."""
        self.optimizer = optimizer

    def generate(
        self,
        assets: List[Asset],
        constraints: PortfolioConstraints,
        correlation_matrix: Optional[np.ndarray] = None,
        risk_free_rate: float = 0.02,
        target_returns: Optional[np.ndarray] = None,
        n_points: int = 20,
    ) -> List[Dict]:
        """
        Generate efficient frontier points.

        Args:
            assets: List of assets
            constraints: Portfolio constraints
            correlation_matrix: Correlation matrix
            risk_free_rate: Risk-free rate
            target_returns: Specific returns to optimize for (if None, generates points)
            n_points: Number of frontier points to generate

        Returns:
            List of frontier points {return, volatility, sharpe, weights}
        """
        frontier_points = []

        if target_returns is None:
            # Generate range of target returns
            min_ret = min(asset.expected_return for asset in assets) * 0.9
            max_ret = max(asset.expected_return for asset in assets) * 1.1
            target_returns = np.linspace(min_ret, max_ret, n_points)

        for ret_target in target_returns:
            try:
                # Create constraint for target return
                constraints_copy = PortfolioConstraints()
                constraints_copy.constraints = constraints.constraints.copy()
                constraints_copy.budget_constraint = constraints.budget_constraint

                portfolio = self.optimizer.optimize(
                    assets,
                    constraints_copy,
                    correlation_matrix,
                    risk_free_rate,
                    objective="target_return",
                    target_return=ret_target,
                )

                frontier_points.append({
                    "return": portfolio.expected_return,
                    "volatility": portfolio.expected_volatility,
                    "sharpe": portfolio.sharpe_ratio,
                    "weights": portfolio.weights,
                })
            except Exception as e:
                # Skip infeasible points
                continue

        return frontier_points
