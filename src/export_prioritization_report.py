import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def export_report():
    input_path = PROJECT_ROOT / "data" / "phase2_output" / "phase2_prioritized_targets.csv"
    if not input_path.exists():
        print(f"[ERROR] Prioritized targets file not found at: {input_path}")
        print("Please run 'python src/run_phase2_pipeline.py' first to generate the dataset.")
        return

    df = pd.read_csv(input_path)
    
    print("\n" + "="*80)
    print(" GEROSCIENCE DISCOVERY PLATFORM (v1.2.1) - FINAL TARGET PRIORITIZATION REPORT")
    print("="*80)
    print(df[["gene_symbol", "gps_score", "hallmark_count", "fdr", "lfc", "hallmarks"]].to_string(index=False))
    print("="*80 + "\n")

    # Export options: additional summary markdown or formatted CSV export
    report_md_path = PROJECT_ROOT / "data" / "phase2_output" / "target_prioritization_summary.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# Geroscience Discovery Platform - Target Prioritization Report\n\n")
        f.write("Generated via Phase 1 & 2 Integrated Pipeline (v1.2.1-Implementation-Freeze).\n\n")
        f.write(df.to_markdown(index=False))

    print(f"[OK] Summary Markdown report successfully exported to: {report_md_path.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    export_report()