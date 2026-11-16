import sys
from pathlib import Path

# Fix module path resolution by adding project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import itertools

from src.scoring.hallmarks_prioritizer import HallmarksPrioritizer

def run_sensitivity_analysis():
    print("\n" + "="*80)
    print(" GEROSCIENCE DISCOVERY PLATFORM - GPS WEIGHT SENSITIVITY ANALYSIS")
    print("="*80)

    # Load base configuration and test input data from Phase 1 output or default stats
    stats_path = PROJECT_ROOT / "data" / "phase2_output" / "phase2_prioritized_targets.csv"
    if not stats_path.exists():
        print(f"[ERROR] Prioritized targets file not found at: {stats_path}")
        print("Please run 'python src/run_phase2_pipeline.py' first.")
        return

    df_base = pd.read_csv(stats_path)
    print(f"[INFO] Loaded {len(df_base)} candidate targets for sensitivity testing.")

    # Define weight grids (must sum to 1.0)
    stat_weights = [0.20, 0.30, 0.35, 0.40, 0.50]
    hallmark_weights = [0.20, 0.30, 0.35, 0.40, 0.50]
    
    combinations = []
    for sw, hw in itertools.product(stat_weights, hallmark_weights):
        ew = round(1.0 - (sw + hw), 2)
        if 0.1 <= ew <= 0.6:
            combinations.append({
                "statistical_significance": round(sw, 2),
                "hallmark_coverage": round(hw, 2),
                "effect_size": round(ew, 2)
            })

    print(f"[INFO] Evaluating {len(combinations)} weight configurations...")

    # Initialize prioritizer with temporary weights
    prioritizer = HallmarksPrioritizer({})
    
    stability_records = []
    for idx, weights in enumerate(combinations):
        prioritizer.weights = weights
        
        # Re-run scoring on the fly
        scored_df = prioritizer.prioritize(df_base, output_dir="data/phase2_output/sensitivity_tmp", min_gps_score=0.0)
        
        for rank, row in scored_df.iterrows():
            stability_records.append({
                "config_id": idx,
                "w_stat": weights["statistical_significance"],
                "w_hallmark": weights["hallmark_coverage"],
                "w_effect": weights["effect_size"],
                "gene_symbol": row["gene_symbol"],
                "gps_score": row["gps_score"],
                "rank": rank + 1
            })

    res_df = pd.DataFrame(stability_records)
    
    # Compute rank stability (Standard deviation of rank across configurations)
    rank_summary = res_df.groupby("gene_symbol")["rank"].agg(["mean", "std", "min", "max"]).reset_index()
    rank_summary = rank_summary.sort_values(by="mean").reset_index(drop=True)

    print("\n[RESULT] Target Rank Stability Across Weight Variations:")
    print(rank_summary.to_string(index=False))
    print("="*80 + "\n")

    # Save report
    out_dir = PROJECT_ROOT / "data" / "phase2_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "sensitivity_analysis_report.csv"
    rank_summary.to_csv(report_path, index=False)
    print(f"[OK] Sensitivity report saved to: {report_path.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    run_sensitivity_analysis()