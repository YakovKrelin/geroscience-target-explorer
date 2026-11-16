import sys
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

# Ensure project root is accessible for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validation.suitability_gatekeeper import DataSuitabilityGatekeeper
from src.normalization.robust_norm import robust_z_score_normalize
from src.stats.mageck_test_c import MAGeCKTestCAnalyzer
from src.utilis.generate_manifests import generate_data_manifest, generate_run_manifest


def load_config(config_path: str = None) -> dict:
    """Loads and validates the frozen configuration file relative to the project root."""
    resolved_path = Path(config_path) if config_path else PROJECT_ROOT / "config" / "config.yaml"
    if not resolved_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def execute_phase1_pipeline(config_path: str = None) -> None:
    """Executes the end-to-end Phase 1 pipeline integrating Gating, Normalization, Test C, and Provenance."""
    cfg = load_config(config_path)
    version = cfg["project"]["version"]
    seed = cfg["project"]["random_seed"]
    np.random.seed(seed)

    print(f"=== Starting Phase 1 End-to-End Pipeline ({version}) ===")
    print(f"[INFO] Loaded config version: {version} | Seed: {seed}")

    # 1. Generate comprehensive screening count and feature table
    output_dir = PROJECT_ROOT / "data" / "phase1_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    input_csv_path = output_dir / "screening_counts_input.csv"

    # Must contain at least 6 samples to pass sample_size_threshold
    screening_data = {
        "sgrna_id": ["sg_tp53_1", "sg_tp53_2", "sg_foxo3_1", "sg_foxo3_2", "sg_sirt6_1", "sg_sirt6_2", 
                     "sg_mtor_1", "sg_mtor_2", "sg_igf1r_1", "sg_igf1r_2", "sg_tert_1", "sg_tert_2"],
        "gene_symbol": ["TP53", "TP53", "FOXO3", "FOXO3", "SIRT6", "SIRT6", 
                        "MTOR", "MTOR", "IGF1R", "IGF1R", "TERT", "TERT"],
        "ctrl_1": [120, 115, 210, 205, 150, 155, 180, 175, 90, 95, 130, 135],
        "ctrl_2": [125, 110, 215, 200, 148, 152, 182, 172, 92, 93, 132, 133],
        "ctrl_3": [122, 112, 212, 202, 149, 153, 181, 173, 91, 94, 131, 134],
        "treat_1": [20, 22, 450, 460, 151, 154, 70, 75, 300, 310, 40, 45],
        "treat_2": [18, 25, 440, 470, 149, 152, 68, 77, 295, 315, 38, 48],
        "treat_3": [19, 23, 445, 465, 150, 153, 69, 76, 298, 312, 39, 46],
    }
    df_input = pd.DataFrame(screening_data)
    df_input.to_csv(input_csv_path, index=False)
    print(f"[INFO] Screening count dataset created at: {input_csv_path.relative_to(PROJECT_ROOT)}")

    # 2. Step A: Data Suitability Quality Gating
    dataset_metadata = {
        "dataset_id": "PHASE1_SCREENING_001",
        "has_independent_replication": True,
        "aging_relevance_verified": True,
        "assay_quality_passed": True,
        "gene_annotation_valid": True, #Ensure that this flag is taken into account in the gatekeeper logic, if required.
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
            system_status="Aborted: Phase 1 Dataset Rejected by Suitability Gatekeeper",
            suitability_report=report_dict,
        )
        raise ValueError(
            f"Dataset '{suitability_report.dataset_id}' rejected due to failed mandatory criteria: "
            f"{suitability_report.failed_mandatory}"
        )

    # 3. Step B: Robust Normalization on control/treatment count metrics
    df_normalized = df_input.copy()
    for col in ["ctrl_1", "ctrl_2", "ctrl_3", "treat_1", "treat_2", "treat_3"]:
        df_normalized[f"{col}_norm"] = robust_z_score_normalize(df_input[col], config=cfg)

    norm_csv_path = output_dir / "normalized_screening_counts.csv"
    df_normalized.to_csv(norm_csv_path, index=False)
    print(f"[OK] Normalized screening data saved to: {norm_csv_path.relative_to(PROJECT_ROOT)}")

    # 4. Step C: Statistical Analysis via MAGeCKTestCAnalyzer (Test C)
    analyzer = MAGeCKTestCAnalyzer(config=cfg)
    treatment_cols = ["treat_1", "treat_2", "treat_3"]
    control_cols = ["ctrl_1", "ctrl_2", "ctrl_3"]

    stats_results_df = analyzer.run_analysis(
        count_table=df_input,
        treatment_cols=treatment_cols,
        control_cols=control_cols,
        output_dir=str(output_dir)
    )

    print("--- Test C Statistical Analysis Preview ---")
    print(stats_results_df.head(5).to_string(index=False))
    print("-------------------------------------------\n")

    # 5. Step D: Cryptographic Provenance Generation
    generate_data_manifest(
        data_dir=str(PROJECT_ROOT / "data"),
        output_path=str(PROJECT_ROOT / "data_manifest.json"),
        version=version,
    )
    generate_run_manifest(
        config_path="config/config.yaml",
        output_path=str(PROJECT_ROOT / "run_manifest.json"),
        version=version,
        system_status="Phase 1 Pipeline Completed Successfully",
        suitability_report=report_dict,
    )
    print("=== Phase 1 Pipeline Completed Successfully ===")


if __name__ == "__main__":
    execute_phase1_pipeline()