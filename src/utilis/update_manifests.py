import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def calculate_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_manifests():
    print("[INFO] Updating platform manifests (v1.4) with dynamic gene profiles scan...")
    
    # Core static tracked files
    tracked_files = [
        "src/scoring/hallmarks_prioritizer.py",
        "src/scoring/sensitivity_analysis.py",
        "src/scoring/external_integrations.py",
        "src/scoring/calibration.py",
        "src/scoring/generate_gene_profile.py",
        "src/run_phase2_pipeline.py",
        "data/phase2_output/phase2_prioritized_targets.csv",
        "data/phase2_output/phase2_enriched_targets.csv",
        "data/phase2_output/sensitivity_analysis_report.csv",
        "data/phase2_output/model_calibration_report.json"
    ]
    
    # Dynamically discover and add all gene profile JSON files
    profiles_dir = PROJECT_ROOT / "data" / "phase2_output" / "gene_profiles"
    if profiles_dir.exists():
        for profile_file in profiles_dir.glob("*.json"):
            # Ensure cross-platform path compatibility using forward slashes
            rel_path = str(profile_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
            if rel_path not in tracked_files:
                tracked_files.append(rel_path)
    
    manifest_data = {}
    for rel_path in tracked_files:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            manifest_data[rel_path] = calculate_sha256(full_path)
            print(f"[HASH] Registered: {rel_path}")
        else:
            print(f"[WARN] File not found (skipped): {rel_path}")
            
    manifest_path = PROJECT_ROOT / "data" / "run_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=4)
        
    print(f"[OK] Manifest successfully updated at: {manifest_path.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    update_manifests()