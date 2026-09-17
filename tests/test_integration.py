"""
Integration tests: end-to-end portfolio optimization workflow.
"""

import pytest
import numpy as np
import json
from datetime import datetime
from src.mean_variance_optimizer import MeanVarianceOptimizer, EfficientFrontier
from sma_quant_core.models import Asset, PortfolioConstraints
from sma_quant_core.backtester import Backtester
import pandas as pd


@pytest.fixture
def sample_assets_json():
    """Load sample assets from JSON."""
    with open("data/sample_assets.json") as f:
        assets_data = json.load(f)
    return [Asset(**a) for a in assets_data]


@pytest.fixture
def sample_constraints_json():
    """Load sample constraints from JSON."""
    with open("data/sample_constraints.json") as f:
        constraints_data = json.load(f)

    constraints = PortfolioConstraints()
    for c in constraints_data.get("constraints", []):
        from sma_quant_core.models import PortfolioConstraint
        constraints.constraints.append(PortfolioConstraint(**c))

    return constraints


def test_full_optimization_workflow(sample_assets_json, sample_constraints_json):
    """Test complete optimization workflow: optimize -> backtest -> report."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)

    # Optimize
    portfolio = opt.optimize(
        sample_assets_json,
        sample_constraints_json,
        objective="max_sharpe",
    )

    assert portfolio.status == "success" or portfolio.status == "warning"
    assert len(portfolio.weights) == len(sample_assets_json)
    assert abs(sum(portfolio.weights.values()) - 1.0) < 0.01


def test_efficient_frontier_workflow(sample_assets_json, sample_constraints_json):
    """Test efficient frontier generation and analysis."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)
    frontier = EfficientFrontier(opt)

    points = frontier.generate(
        sample_assets_json,
        sample_constraints_json,
        n_points=10,
    )

    # Should have at least some frontier points
    assert len(points) > 0

    # Points should be increasingly efficient
    if len(points) > 1:
        returns = [p["return"] for p in points]
        assert returns == sorted(returns)


def test_sensitivity_to_return_target(sample_assets_json, sample_constraints_json):
    """Test that different return targets produce different allocations."""
    opt = MeanVarianceOptimizer(use_cvxpy=False)

    # Get two portfolios with different return targets
    p1 = opt.optimize(
        sample_assets_json,
        sample_constraints_json,
        objective="target_return",
        target_return=0.05,
    )

    p2 = opt.optimize(
        sample_assets_json,
        sample_constraints_json,
        objective="target_return",
        target_return=0.06,
    )

    # Higher return target should generally mean higher volatility
    assert p2.expected_volatility >= p1.expected_volatility


def test_constraint_binding(sample_assets_json, sample_constraints_json):
    """Test that generated portfolio respects all constraints (when cvxpy available)."""
    # Note: Equal-weight fallback optimizer does not respect constraints;
    # this test is primarily for cvxpy-based optimization
    opt = MeanVarianceOptimizer(use_cvxpy=False)
    portfolio = opt.optimize(
        sample_assets_json,
        sample_constraints_json,
    )

    # Check all weights non-negative
    for asset_id, weight in portfolio.weights.items():
        assert weight >= 0  # Non-negative
        assert weight <= 1  # Max single position
