import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.stats.mageck_test_c import MAGeCKTestCAnalyzer


@pytest.fixture
def mock_count_table() -> pd.DataFrame:
    return pd.DataFrame({
        "sgrna_id": ["sg1", "sg2", "sg3", "sg4", "sg5", "sg6"],
        "gene_symbol": ["TP53", "TP53", "FOXO3", "FOXO3", "SIRT6", "SIRT6"],
        "ctrl_1": [100, 120, 200, 210, 150, 155],
        "ctrl_2": [105, 115, 195, 215, 148, 152],
        "treat_1": [20, 25, 400, 420, 150, 153],
        "treat_2": [18, 22, 410, 430, 152, 150],
    })


@pytest.fixture
def test_config() -> dict:
    return {
        "statistical_tests": {
            "test_c": {
                "enabled": True,
                "method": "RRA",
                "alpha_threshold": 0.05,
                "permutation_count": 500,
                "parameters": {"score_metric": "neg_lfc"}
            }
        }
    }


def test_mageck_analyzer_execution(test_config, mock_count_table):
    analyzer = MAGeCKTestCAnalyzer(config=test_config)
    treatment_cols = ["treat_1", "treat_2"]
    control_cols = ["ctrl_1", "ctrl_2"]

    result_df = analyzer.run_analysis(
        mock_count_table,
        treatment_cols=treatment_cols,
        control_cols=control_cols,
        output_dir="data/test_output"
    )

    assert not result_df.empty
    assert "gene_symbol" in result_df.columns
    assert "fdr" in result_df.columns
    assert "significant" in result_df.columns
    
    # TP53 drops significantly in treatment -> should be flagged or ranked high
    tp53_row = result_df[result_df["gene_symbol"] == "TP53"].iloc[0]
    assert tp53_row["lfc"] < 0