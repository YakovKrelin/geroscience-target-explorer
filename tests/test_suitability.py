import os
import sys
import pytest
import numpy as np
import pandas as pd

# Ensure project root is in sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.validation.suitability_gatekeeper import DataSuitabilityGatekeeper, SuitabilityReport


@pytest.fixture
def frozen_config() -> dict:
    """Provides the standard v1.2.1 data suitability configuration."""
    return {
        "data_suitability": {
            "mandatory_criteria": [
                "measurement_availability",
                "sample_size_threshold",
                "correct_gene_annotation",
            ],
            "important_criteria": [
                "independent_replication",
            ],
            "supportive_criteria": [
                "aging_relevance",
                "assay_quality",
            ],
        }
    }


@pytest.fixture
def valid_expression_df() -> pd.DataFrame:
    """Provides a valid synthetic expression matrix with 6 samples and clean HGNC symbols."""
    return pd.DataFrame({
        "gene_symbol": ["TP53", "FOXO3", "SIRT6", "MTOR", "IGF1R", "TERT"],
        "sample_1": [1.2, -0.5, 0.8, 1.5, -1.1, 0.3],
        "sample_2": [1.4, -0.4, 0.9, 1.3, -1.0, 0.4],
        "sample_3": [1.1, -0.6, 0.7, 1.6, -1.2, 0.2],
        "sample_4": [-0.8, 1.1, -0.3, -0.9, 0.8, -0.5],
        "sample_5": [-0.9, 1.2, -0.4, -1.0, 0.9, -0.4],
        "sample_6": [-0.7, 1.0, -0.2, -0.8, 0.7, -0.6],
    })


def test_suitability_passed_full_score(frozen_config, valid_expression_df):
    """Dataset meeting all mandatory, important, and supportive criteria returns PASSED with score 100.0."""
    gatekeeper = DataSuitabilityGatekeeper(config=frozen_config)
    metadata = {
        "dataset_id": "GSE_AGING_001",
        "has_independent_replication": True,
        "aging_relevance_verified": True,
        "assay_quality_passed": True,
    }

    report: SuitabilityReport = gatekeeper.evaluate(valid_expression_df, metadata)

    assert report.dataset_id == "GSE_AGING_001"
    assert report.status == "PASSED"
    assert report.suitability_score == 100.0
    assert len(report.failed_mandatory) == 0
    assert len(report.failed_important) == 0
    assert len(report.failed_supportive) == 0


def test_suitability_passed_partial_supportive(frozen_config, valid_expression_df):
    """Dataset passing mandatory and important but missing one supportive criterion remains PASSED with score 90.0."""
    gatekeeper = DataSuitabilityGatekeeper(config=frozen_config)
    metadata = {
        "dataset_id": "GSE_AGING_002",
        "has_independent_replication": True,
        "aging_relevance_verified": True,
        "assay_quality_passed": False,
    }

    report = gatekeeper.evaluate(valid_expression_df, metadata)

    assert report.status == "PASSED"
    assert report.suitability_score == 90.0
    assert report.failed_supportive == ["assay_quality"]


def test_suitability_conditional_missing_replication(frozen_config, valid_expression_df):
    """Dataset passing mandatory criteria but lacking independent replication returns CONDITIONAL."""
    gatekeeper = DataSuitabilityGatekeeper(config=frozen_config)
    metadata = {
        "dataset_id": "GSE_PILOT_003",
        "has_independent_replication": False,
        "aging_relevance_verified": True,
        "assay_quality_passed": True,
    }

    report = gatekeeper.evaluate(valid_expression_df, metadata)

    assert report.status == "CONDITIONAL"
    assert report.suitability_score == 80.0
    assert report.failed_important == ["independent_replication"]
    assert len(report.failed_mandatory) == 0


def test_suitability_rejected_low_coverage(frozen_config, valid_expression_df):
    """Dataset with measurement coverage below 40% fails measurement_availability and returns REJECTED."""
    sparse_df = valid_expression_df.copy()
    # Mask 5 out of 6 sample columns with NaN (~16.7% valid coverage < 40%)
    for col in ["sample_2", "sample_3", "sample_4", "sample_5", "sample_6"]:
        sparse_df[col] = np.nan

    gatekeeper = DataSuitabilityGatekeeper(config=frozen_config)
    metadata = {
        "dataset_id": "GSE_SPARSE_004",
        "has_independent_replication": True,
        "aging_relevance_verified": True,
        "assay_quality_passed": True,
    }

    report = gatekeeper.evaluate(sparse_df, metadata)

    assert report.status == "REJECTED"
    assert report.suitability_score == 0.0
    assert "measurement_availability" in report.failed_mandatory
    assert report.diagnostics["measurement_coverage"] < 0.40


def test_suitability_rejected_small_sample_size(frozen_config, valid_expression_df):
    """Dataset with fewer than 6 samples fails sample_size_threshold and returns REJECTED."""
    small_df = valid_expression_df[["gene_symbol", "sample_1", "sample_2", "sample_3"]]

    gatekeeper = DataSuitabilityGatekeeper(config=frozen_config)
    metadata = {
        "dataset_id": "GSE_SMALL_005",
        "has_independent_replication": True,
        "aging_relevance_verified": True,
        "assay_quality_passed": True,
    }

    report = gatekeeper.evaluate(small_df, metadata)

    assert report.status == "REJECTED"
    assert report.suitability_score == 0.0
    assert "sample_size_threshold" in report.failed_mandatory
    assert report.diagnostics["effective_sample_count"] == 3


def test_suitability_rejected_invalid_or_duplicate_genes(frozen_config, valid_expression_df):
    """Dataset with malformed gene symbols or duplicates fails correct_gene_annotation and returns REJECTED."""
    bad_genes_df = valid_expression_df.copy()
    bad_genes_df["gene_symbol"] = ["TP53", "TP53", "123_invalid", "lowercase_gene", "???", "TERT"]

    gatekeeper = DataSuitabilityGatekeeper(config=frozen_config)
    metadata = {
        "dataset_id": "GSE_BADGENES_006",
        "has_independent_replication": True,
        "aging_relevance_verified": True,
        "assay_quality_passed": True,
    }

    report = gatekeeper.evaluate(bad_genes_df, metadata)

    assert report.status == "REJECTED"
    assert report.suitability_score == 0.0
    assert "correct_gene_annotation" in report.failed_mandatory
    assert report.diagnostics["has_duplicate_genes"] is True


def test_suitability_unknown_criterion_fails_closed(frozen_config, valid_expression_df):
    """Unknown mandatory criterion in config must fail closed to prevent silent bypass."""
    tampered_config = {
        "data_suitability": {
            "mandatory_criteria": ["non_existent_rule"],
            "important_criteria": [],
            "supportive_criteria": [],
        }
    }
    gatekeeper = DataSuitabilityGatekeeper(config=tampered_config)
    report = gatekeeper.evaluate(valid_expression_df, {"dataset_id": "GSE_TAMPER_007"})

    assert report.status == "REJECTED"
    assert report.suitability_score == 0.0
    assert "non_existent_rule" in report.failed_mandatory