import sys
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

# Ensure project root is accessible for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.normalization.robust_norm import robust_z_score_normalize
from src.validation.suitability_gatekeeper import DataSuitabilityGatekeeper
from src.utilis.generate_manifests import generate_data_manifest, generate_run_manifest


def load_config(config_path: str = None) -> dict:
    """Loads and validates the frozen configuration file relative to the project root."""
    resolved_path = Path(config_path) if config_path else PROJECT_ROOT / "config" / "config.yaml"
    if not resolved_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def execute_phase0_dry_run(config_path: str = None) -> None:
    """Executes an end-to-end Phase 0 dry run with suitability gating, normalization, and SHA-256 provenance."""
    cfg = load_config(config_path)
    version = cfg["project"]["version"]
    seed = cfg["project"]["random_seed"]
    np.random.seed(seed)

    print(f"=== Starting Phase 0 Dry Run ({version}) ===")
    print(f"[INFO] Loaded config version: {version} | Seed: {seed}")

    # 1. Generate synthetic input dataset (6 numeric features to satisfy sample_size_threshold >= 6)
    dry_run_dir = PROJECT_ROOT / "data" / "dry_run"
    dry_run_dir.mkdir(parents=True, exist_ok=True)
    input_csv_path = dry_run_dir / "synthetic_input_features.csv"

    genes = ["TP53", "FOXO3", "SIRT6", "MTOR", "IGF1R", "TERT", "KL", "APOE", "CDKN2A", "LMNA"]
    df_input = pd.DataFrame({
        "gene_symbol": genes,
        "standard_log2fc": [2.45, -1.80, 0.05, 1.15, -0.75, -0.80, 0.10, 0.95, -2.10, 1.90],
        "zero_mad_feature": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "low_coverage_feature": [0.5, np.nan, np.nan, np.nan, 1.2, np.nan, np.nan, np.nan, np.nan, np.nan],
        "replicate_4": [2.30, -1.75, 0.08, 1.20, -0.70, -0.82, 0.12, 0.90, -2.05, 1.85],
        "replicate_5": [2.50, -1.85, 0.03, 1.10, -0.78, -0.76, 0.09, 0.98, -2.15, 1.92],
        "replicate_6": [2.40, -1.78, 0.06, 1.18, -0.72, -0.79, 0.11, 0.92, -2.08, 1.88],
    })
    df_input.to_csv(input_csv_path, index=False)
    print(f"[INFO] Synthetic dry-run input dataset created at: {input_csv_path.relative_to(PROJECT_ROOT)}")

    # 2. Evaluate dataset quality via DataSuitabilityGatekeeper BEFORE normalization
    dataset_metadata = {
        "dataset_id": "PHASE0_SYNTHETIC_001",
        "has_independent_replication": True,
        "aging_relevance_verified": True,
        "assay_quality_passed": True,
    }
    gatekeeper = DataSuitabilityGatekeeper(config=cfg)
    suitability_report = gatekeeper.evaluate(df_input, metadata=dataset_metadata, gene_col="gene_symbol")
    report_dict = asdict(suitability_report)

    print(
        f"[INFO] Suitability Gatekeeper Status: {suitability_report.status} "
        f"| Score: {suitability_report.suitability_score}/100.0"
    )

    if suitability_report.status == "REJECTED":
        generate_run_manifest(
            config_path="config/config.yaml",
            output_path=str(PROJECT_ROOT / "run_manifest.json"),
            version=version,
            system_status="Aborted: Dataset Rejected by Suitability Gatekeeper",
            suitability_report=report_dict,
        )
        raise ValueError(
            f"Dataset '{suitability_report.dataset_id}' rejected due to failed mandatory criteria: "
            f"{suitability_report.failed_mandatory}"
        )

    # 3. Apply deterministic robust normalization passing config dictionary
    df_output = pd.DataFrame({"gene_symbol": df_input["gene_symbol"]})
    for col in ["standard_log2fc", "zero_mad_feature", "low_coverage_feature"]:
        df_output[f"{col}_norm"] = robust_z_score_normalize(df_input[col], config=cfg)

    output_csv_path = dry_run_dir / "normalized_output_features.csv"
    df_output.to_csv(output_csv_path, index=False)
    print(f"[OK] Normalized features saved to: {output_csv_path.relative_to(PROJECT_ROOT)}\n")

    print("--- Dry Run Normalization Preview ---")
    print(df_output.to_string(index=False))
    print("-------------------------------------\n")

    # 4. Generate cryptographic data and execution provenance manifests
    generate_data_manifest(
        data_dir=str(PROJECT_ROOT / "data"),
        output_path=str(PROJECT_ROOT / "data_manifest.json"),
        version=version,
    )
    generate_run_manifest(
        config_path="config/config.yaml",
        output_path=str(PROJECT_ROOT / "run_manifest.json"),
        version=version,
        system_status="Phase 0 Dry Run Completed",
        suitability_report=report_dict,
    )
    print("=== Phase 0 Dry Run Completed Successfully ===")


if __name__ == "__main__":
    execute_phase0_dry_run()