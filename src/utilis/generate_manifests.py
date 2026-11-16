import os
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


def compute_sha256(file_path: str) -> str:
    """Computes the SHA-256 cryptographic checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_git_commit_hash() -> str:
    """Retrieves the current Git HEAD commit hash if available."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        return commit
    except Exception:
        return "untracked_workspace"


def generate_data_manifest(
    data_dir: str = "data",
    output_path: str = "data_manifest.json",
    version: str = "v1.2.1-Implementation-Freeze",
) -> Dict[str, Any]:
    """Scans data directory and generates a SHA-256 cryptographic data manifest."""
    base_path = Path(data_dir)
    files_metadata = []

    if base_path.exists():
        for file_path in sorted(base_path.rglob("*")):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(base_path))
                files_metadata.append({
                    "relative_path": rel_path,
                    "size_bytes": file_path.stat().st_size,
                    "sha256": compute_sha256(str(file_path)),
                })

    manifest = {
        "manifest_type": "data_manifest",
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(files_metadata),
        "files": files_metadata,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[OK] Data manifest successfully generated at: {output_path}")
    return manifest


def generate_run_manifest(
    config_path: str = "config/config.yaml",
    output_path: str = "run_manifest.json",
    version: str = "v1.2.1-Implementation-Freeze",
    system_status: str = "Phase 0 Dry Run Completed",
    suitability_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generates an execution provenance manifest binding config hash, git commit, and suitability audit."""
    cfg_file = Path(config_path)
    if not cfg_file.exists():
        raise FileNotFoundError(f"Cannot generate run manifest; config missing at: {config_path}")

    manifest: Dict[str, Any] = {
        "manifest_type": "run_manifest",
        "version": version,
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit_hash(),
        "configuration": {
            "config_file": config_path.replace("\\", "/"),
            "sha256": compute_sha256(str(cfg_file)),
        },
        "system_status": system_status,
        "audit_compliance": "Enforced",
    }

    if suitability_report is not None:
        manifest["data_suitability_audit"] = suitability_report

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[OK] Run manifest successfully generated at: {output_path}")
    return manifest