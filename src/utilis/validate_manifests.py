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

def validate_manifests():
    print("\n" + "="*80)
    print(" GEROSCIENCE DISCOVERY PLATFORM - MANIFEST INTEGRITY VALIDATION")
    print("="*80)
    
    manifest_path = PROJECT_ROOT / "data" / "run_manifest.json"
    if not manifest_path.exists():
        print(f"[ERROR] Manifest file not found at: {manifest_path}")
        print("Please run 'python src/utilis/update_manifests.py' first.")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        stored_manifest = json.load(f)

    mismatches = 0
    missing = 0
    checked = 0

    for rel_path, expected_hash in stored_manifest.items():
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            print(f"[MISSING] File not found: {rel_path}")
            missing += 1
            continue
            
        current_hash = calculate_sha256(full_path)
        checked += 1
        
        if current_hash == expected_hash:
            print(f"[VALID] {rel_path}")
        else:
            print(f"[TAMPERED/CHANGED] {rel_path}")
            print(f"  Expected: {expected_hash}")
            print(f"  Got:      {current_hash}")
            mismatches += 1

    print("="*80)
    print(f"Validation Summary: Checked {checked}, Mismatches {mismatches}, Missing {missing}")
    
    if mismatches == 0 and missing == 0:
        print("[SUCCESS] All platform files successfully verified. Integrity check PASSED.")
    else:
        print("[WARNING] Integrity check FAILED. Some files have changed or are missing.")
    print("="*80 + "\n")

if __name__ == "__main__":
    validate_manifests()