from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class HallmarksPrioritizer:
    """
    Phase 2 module for evaluating genes against the 14 Hallmarks of Aging
    and computing a multi-criteria Geroscience Priority Score (GPS).
    """

    # Expanded 14 Hallmarks of Aging taxonomy
    CANONICAL_HALLMARKS = [
        "Genomic instability",
        "Telomere attrition",
        "Epigenetic alterations",
        "Loss of proteostasis",
        "Disabled macroautophagy",
        "Deregulated nutrient-sensing",
        "Mitochondrial dysfunction",
        "Cellular senescence",
        "Stem cell exhaustion",
        "Altered intercellular communication",
        "Chronic inflammation",
        "Dysbiosis",
        "Macromitophagy impairment",
        "Altered mechanical properties"
    ]

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        scoring_cfg = config.get("scoring", {})
        
        self.weights = scoring_cfg.get("criteria_weights", {
            "statistical_significance": 0.35,
            "hallmark_coverage": 0.35,
            "effect_size": 0.30
        })
        
        # Hallmark knowledge base for core geroscience targets
        self.hallmark_database = scoring_cfg.get("hallmark_knowledge_base", {
            "TP53": ["Genomic instability", "Cellular senescence", "Mitochondrial dysfunction"],
            "FOXO3": ["Deregulated nutrient-sensing", "Cellular senescence", "Chronic inflammation"],
            "SIRT6": ["Epigenetic alterations", "Genomic instability", "Deregulated nutrient-sensing"],
            "MTOR": ["Deregulated nutrient-sensing", "Disabled macroautophagy", "Loss of proteostasis"],
            "IGF1R": ["Deregulated nutrient-sensing", "Cellular senescence"],
            "TERT": ["Telomere attrition", "Stem cell exhaustion"],
            "KL": ["Chronic inflammation", "Deregulated nutrient-sensing", "Altered intercellular communication"],
            "APOE": ["Altered intercellular communication", "Chronic inflammation", "Loss of proteostasis"],
            "CDKN2A": ["Cellular senescence", "Stem cell exhaustion"],
            "LMNA": ["Genomic instability", "Loss of proteostasis", "Altered mechanical properties"]
        })

    def prioritize(
        self,
        stats_results_df: pd.DataFrame,
        output_dir: str = "data/phase2_output",
        min_gps_score: float = 0.0
    ) -> pd.DataFrame:
        """
        Calculates multi-criteria Geroscience Priority Scores (GPS) integrating
        MAGeCK statistical results and Hallmark annotations, and filters by min_gps_score.

        Args:
            stats_results_df: DataFrame containing gene symbols, FDR, p_value, and lfc from Phase 1.
            output_dir: Directory to save prioritized targets report.
            min_gps_score: Minimum Geroscience Priority Score threshold for filtering targets.

        Returns:
            Filtered DataFrame sorted by Geroscience Priority Score (descending).
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] Evaluating targets against 14 Hallmarks of Aging (min GPS threshold: {min_gps_score})...")

        records = []
        for _, row in stats_results_df.iterrows():
            gene = row["gene_symbol"]
            fdr = float(row.get("fdr", 1.0))
            lfc = float(row.get("lfc", 0.0))
            
            # 1. Hallmark annotation lookup & breadth calculation
            associated_hallmarks = self.hallmark_database.get(gene, [])
            hallmark_count = len(associated_hallmarks)
            hallmark_score_ratio = min(1.0, hallmark_count / 4.0)

            # 2. Statistical score component (-log10 FDR, clipped and normalized)
            stat_score = float(min(1.0, -np.log10(max(fdr, 1e-10)) / 10.0))

            # 3. Effect size component (absolute log2 fold change normalized)
            effect_score = float(min(1.0, abs(lfc) / 3.0))

            # 4. Composite Geroscience Priority Score (GPS)
            gps = (
                self.weights["statistical_significance"] * stat_score +
                self.weights["hallmark_coverage"] * hallmark_score_ratio +
                self.weights["effect_size"] * effect_score
            ) * 100.0

            # Apply filter threshold
            if gps >= min_gps_score:
                records.append({
                    "gene_symbol": gene,
                    "gps_score": round(gps, 2),
                    "hallmark_count": hallmark_count,
                    "hallmarks": "; ".join(associated_hallmarks) if associated_hallmarks else "None",
                    "stat_component_score": round(stat_score * 100, 2),
                    "hallmark_component_score": round(hallmark_score_ratio * 100, 2),
                    "effect_component_score": round(effect_score * 100, 2),
                    "fdr": fdr,
                    "lfc": lfc
                })

        prioritized_df = pd.DataFrame(records)
        if not prioritized_df.empty:
            prioritized_df = prioritized_df.sort_values(by="gps_score", ascending=False).reset_index(drop=True)

        report_path = out_path / "phase2_prioritized_targets.csv"
        prioritized_df.to_csv(report_path, index=False)
        print(f"[OK] Filtered prioritized targets successfully saved to: {report_path}")

        return prioritized_df