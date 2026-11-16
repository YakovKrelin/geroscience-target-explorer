import pytest
import pandas as pd
import numpy as np

from src.normalization.robust_norm import robust_z_score_normalize

@pytest.fixture
def base_config():
    """Base configuration fixture compliant with v1.2.1."""
    return {
        "normalization": {
            "mad_scale_factor": 1.4826,
            "clip_range": [-5.0, 5.0],
            "fallback_rules": {
                "mad_zero_valid_coverage_threshold": 0.40,
                "fallback_action_if_valid": "rank_percentile_normalization",
                "fallback_action_if_invalid": "set_null"
            }
        }
    }

def test_robust_z_score_normalize_standard(base_config):
    """Verify standard robust Z-score calculation and bounds."""
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 100.0])
    result = robust_z_score_normalize(series, base_config)
    
    assert result.notna().all()
    assert (result >= 0.0).all() and (result <= 1.0).all()

def test_mad_zero_fallback_to_rank(base_config):
    """Verify rule: if MAD == 0 but coverage >= 40%, rank normalization applies."""
    series = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])
    result = robust_z_score_normalize(series, base_config)
    
    assert result.notna().all()
    # For identical values, pandas rank(pct=True) assigns the average percentile (0.6 for 5 identical elements)
    assert (result == 0.6).all()

def test_insufficient_coverage_sets_null(base_config):
    """Verify rule: if valid observations < 40%, feature returns NaN."""
    series = pd.Series([10.0, None, None, None, None])
    result = robust_z_score_normalize(series, base_config)
    
    assert result.isna().all()