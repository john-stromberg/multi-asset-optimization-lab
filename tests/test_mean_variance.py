"""
Unit tests for mean-variance optimizer.
"""

import pytest
import numpy as np
from datetime import datetime
from src.mean_variance_optimizer import MeanVarianceOptimizer, EfficientFrontier
from sma_quant_core.models import Asset, PortfolioConstraints


@pytest.fixture
def sample_assets():
    """Sample assets for testing."""
    return [
        Asset("VTSAX", "US Stock", "equity", 0.08, 0.15),
        Asset("VTIAX", "Intl Stock", "equity", 0.07, 0.18),
        Asset("BND", "Bonds", "fixed_income", 0.04, 0.05),
    ]


@pytest.fixture
def sample_correlation():
    """Sample correlation matrix."""
    return np.array([
        [1.00, 0.90, -0.20],
        [0.90, 1.00, -0.15],
        [-0.20, -0.15, 1.00],
    ])


@pytest.fixture
def sample_constraints():
    """Sample constraints."""
    constraints = PortfolioConstraints()
    constraints.add_weight_constraint("VTSAX", 0.1, 0.6)
    constraints.add_weight_constraint("VTIAX", 0.1, 0.4)
    constraints.add_weight_constraint("BND", 0.1, 0.5)
    return constraints


def test_optimizer_initialization():
    """Test optimizer creation."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)
    assert opt is not None


def test_optimize_max_sharpe(sample_assets, sample_correlation, sample_constraints):
    """Test Sharpe ratio maximization."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)
    portfolio = opt.optimize(
        sample_assets,
        sample_constraints,
        correlation_matrix=sample_correlation,
        objective="max_sharpe",
    )

    assert portfolio.sharpe_ratio >= 0
    assert len(portfolio.weights) == len(sample_assets)
    assert abs(sum(portfolio.weights.values()) - 1.0) < 0.01


def test_weights_satisfy_constraints(sample_assets, sample_correlation, sample_constraints):
    """Test that optimized weights satisfy constraints."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)
    portfolio = opt.optimize(
        sample_assets,
        sample_constraints,
        correlation_matrix=sample_correlation,
    )

    # Check bounds
    for constraint in sample_constraints.constraints:
        if constraint.constraint_type == "min_weight" and constraint.asset_id:
            assert portfolio.weights[constraint.asset_id] >= constraint.lower_bound - 1e-6
        elif constraint.constraint_type == "max_weight" and constraint.asset_id:
            assert portfolio.weights[constraint.asset_id] <= constraint.upper_bound + 1e-6


def test_efficient_frontier(sample_assets, sample_correlation, sample_constraints):
    """Test efficient frontier generation."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)
    frontier = EfficientFrontier(opt)

    points = frontier.generate(
        sample_assets,
        sample_constraints,
        correlation_matrix=sample_correlation,
        n_points=5,
    )

    assert len(points) > 0
    assert all("return" in p and "volatility" in p for p in points)


def test_empty_assets():
    """Test error on empty assets."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)
    constraints = PortfolioConstraints()

    with pytest.raises(ValueError):
        opt.optimize([], constraints)
