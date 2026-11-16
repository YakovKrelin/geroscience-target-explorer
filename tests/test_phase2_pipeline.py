import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.validation.suitability_gatekeeper import DataSuitabilityGatekeeper
from src.normalization.robust_norm import robust_z_score_normalize
from src.stats.mageck_test_c import MAGeCKTestCAnalyzer
from src.scoring.hallmarks_prioritizer import HallmarksPrioritizer


@pytest.fixture
def integrated_test_config() -> dict:
    return {
        "project": {
            "version": "v1.2.1-Implementation-Freeze",
            "random_seed": 20261116
        },
        "data_suitability": {
            "mandatory_criteria": ["measurement_availability", "sample_size_threshold", "correct_gene_annotation"],
            "important_criteria": ["independent_replication"],
            "supportive_criteria": ["aging_relevance"]
        },
        "statistical_tests": {
            "test_c": {
                "enabled": True,
                "method": "RRA",
                "alpha_threshold": 0.05
            }
        },
        "scoring": {
            "criteria_weights": {
                "statistical_significance": 0.35,
                "hallmark_coverage": 0.35,
                "effect_size": 0.30
            }
        }
    }


@pytest.fixture
def sample_screening_data() -> pd.DataFrame:
    return pd.DataFrame({
        "sgrna_id": ["sg_tp53_1", "sg_tp53_2", "sg_foxo3_1", "sg_foxo3_2", "sg_sirt6_1", "sg_sirt6_2"],
        "gene_symbol": ["TP53", "TP53", "FOXO3", "FOXO3", "SIRT6", "SIRT6"],
        "ctrl_1": [120, 115, 210, 205, 150, 155],
        "ctrl_2": [125, 110, 215, 200, 148, 152],
        "ctrl_3": [122, 112, 212, 202, 149, 153],
        "treat_1": [20, 22, 450, 460, 151, 154],
        "treat_2": [18, 25, 440, 470, 149, 152],
        "treat_3": [19, 23, 445, 465, 150, 153],
    })


def test_end_to_end_phase1_and_phase2_pipeline(integrated_test_config, sample_screening_data):
    # 1. Gatekeeper evaluation
    gatekeeper = DataSuitabilityGatekeeper(config=integrated_test_config)
    metadata = {
        "dataset_id": "TEST_INTEGRATED_001",
        "has_independent_replication": True,
        "aging_relevance_verified": True
    }
    report = gatekeeper.evaluate(sample_screening_data, metadata=metadata, gene_col="gene_symbol")
    assert report.status in ["PASSED", "CONDITIONAL"]

    # 2. Normalization execution
    df_norm = sample_screening_data.copy()
    for col in ["ctrl_1", "treat_1"]:
        df_norm[f"{col}_norm"] = robust_z_score_normalize(sample_screening_data[col], config=integrated_test_config)
    assert not df_norm.empty

    # 3. Statistical Analysis (Test C - MAGeCK RRA)
    analyzer = MAGeCKTestCAnalyzer(config=integrated_test_config)
    stats_df = analyzer.run_analysis(
        count_table=sample_screening_data,
        treatment_cols=["treat_1", "treat_2", "treat_3"],
        control_cols=["ctrl_1", "ctrl_2", "ctrl_3"],
        output_dir="data/test_integration_output"
    )
    assert not stats_df.empty
    assert "fdr" in stats_df.columns

    # 4. Multi-Criteria Prioritization (Hallmarks GPS)
    prioritizer = HallmarksPrioritizer(config=integrated_test_config)
    prioritized_df = prioritizer.prioritize(
        stats_results_df=stats_df,
        output_dir="data/test_integration_output"
    )

    assert not prioritized_df.empty
    assert "gps_score" in prioritized_df.columns
    assert "hallmark_count" in prioritized_df.columns
    assert "hallmarks" in prioritized_df.columns
    
    # Top target should have a valid composite score
    top_target = prioritized_df.iloc[0]
    assert top_target["gps_score"] > 0.0