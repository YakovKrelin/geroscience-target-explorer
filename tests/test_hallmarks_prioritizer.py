import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.scoring.hallmarks_prioritizer import HallmarksPrioritizer


@pytest.fixture
def sample_stats_df() -> pd.DataFrame:
    return pd.DataFrame({
        "gene_symbol": ["FOXO3", "SIRT6", "TP53"],
        "lfc": [2.5, 0.2, -1.8],
        "p_value": [0.001, 0.05, 0.002],
        "fdr": [0.005, 0.08, 0.012],
        "significant": [True, False, True]
    })


@pytest.fixture
def mock_config() -> dict:
    return {
        "scoring": {
            "criteria_weights": {
                "statistical_significance": 0.4,
                "hallmark_coverage": 0.4,
                "effect_size": 0.2
            }
        }
    }


def test_hallmarks_prioritizer_execution(mock_config, sample_stats_df):
    prioritizer = HallmarksPrioritizer(config=mock_config)
    result_df = prioritizer.prioritize(sample_stats_df, output_dir="data/test_phase2_output")

    assert not result_df.empty
    assert "gps_score" in result_df.columns
    assert "hallmark_count" in result_df.columns
    assert "hallmarks" in result_df.columns
    
    top_target = result_df.iloc[0]
    assert top_target["gene_symbol"] == "FOXO3"
    assert top_target["gps_score"] > 0.0