import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import pandas as pd


@dataclass
class SuitabilityReport:
    """Structured audit report returned by the Data Suitability Gatekeeper."""
    dataset_id: str
    status: str  # "PASSED", "CONDITIONAL", or "REJECTED"
    suitability_score: float
    passed_mandatory: List[str] = field(default_factory=list)
    failed_mandatory: List[str] = field(default_factory=list)
    passed_important: List[str] = field(default_factory=list)
    failed_important: List[str] = field(default_factory=list)
    passed_supportive: List[str] = field(default_factory=list)
    failed_supportive: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class DataSuitabilityGatekeeper:
    """
    Deterministic quality gatekeeper evaluating candidate datasets against
    mandatory, important, and supportive criteria defined in config.yaml.
    """

    # Standard HGNC-like gene symbol pattern (alphanumeric, hyphens allowed, starts with uppercase letter)
    HGNC_PATTERN = re.compile(r"^[A-Z][A-Z0-9\-]{1,15}$")

    def __init__(
        self,
        config: Dict[str, Any],
        min_samples: int = 6,
        min_valid_measurement_ratio: float = 0.40,
        min_valid_gene_symbol_ratio: float = 0.85,
    ) -> None:
        self.config = config
        suitability_cfg = config.get("data_suitability", {})

        self.mandatory_criteria: List[str] = suitability_cfg.get("mandatory_criteria", [])
        self.important_criteria: List[str] = suitability_cfg.get("important_criteria", [])
        self.supportive_criteria: List[str] = suitability_cfg.get("supportive_criteria", [])

        self.min_samples = min_samples
        self.min_valid_measurement_ratio = min_valid_measurement_ratio
        self.min_valid_gene_symbol_ratio = min_valid_gene_symbol_ratio

    def evaluate(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        gene_col: str = "gene_symbol",
    ) -> SuitabilityReport:
        """
        Evaluates a dataset DataFrame and its accompanying metadata dictionary.

        Args:
            df: Input feature/expression table containing a gene identifier column and numeric sample/feature columns.
            metadata: Provenance dictionary containing keys such as 'dataset_id', 'has_independent_replication',
                      'aging_relevance_verified', and 'assay_quality_passed'.
            gene_col: Name of the column holding HGNC gene symbols.

        Returns:
            SuitabilityReport detailing pass/fail status across all criteria tiers.
        """
        dataset_id = str(metadata.get("dataset_id", "unknown_dataset"))
        diagnostics: Dict[str, Any] = {}

        # Registry of criterion evaluators
        evaluators = {
            "measurement_availability": lambda: self._check_measurement_availability(df, gene_col, diagnostics),
            "sample_size_threshold": lambda: self._check_sample_size(df, gene_col, metadata, diagnostics),
            "correct_gene_annotation": lambda: self._check_gene_annotation(df, gene_col, diagnostics),
            "independent_replication": lambda: self._check_metadata_flag(
                metadata, "has_independent_replication", diagnostics
            ),
            "aging_relevance": lambda: self._check_metadata_flag(
                metadata, "aging_relevance_verified", diagnostics
            ),
            "assay_quality": lambda: self._check_metadata_flag(
                metadata, "assay_quality_passed", diagnostics
            ),
        }

        passed_mandatory, failed_mandatory = self._run_tier(self.mandatory_criteria, evaluators)
        passed_important, failed_important = self._run_tier(self.important_criteria, evaluators)
        passed_supportive, failed_supportive = self._run_tier(self.supportive_criteria, evaluators)

        # Determine final status and deterministic suitability score (0.0 to 100.0)
        if failed_mandatory:
            status = "REJECTED"
            score = 0.0
        else:
            # Base score 60 for passing all mandatory criteria
            # +20 points allocated across important criteria
            # +20 points allocated across supportive criteria
            imp_score = (
                20.0 * (len(passed_important) / len(self.important_criteria))
                if self.important_criteria
                else 20.0
            )
            sup_score = (
                20.0 * (len(passed_supportive) / len(self.supportive_criteria))
                if self.supportive_criteria
                else 20.0
            )
            score = round(60.0 + imp_score + sup_score, 2)
            status = "PASSED" if not failed_important else "CONDITIONAL"

        return SuitabilityReport(
            dataset_id=dataset_id,
            status=status,
            suitability_score=score,
            passed_mandatory=passed_mandatory,
            failed_mandatory=failed_mandatory,
            passed_important=passed_important,
            failed_important=failed_important,
            passed_supportive=passed_supportive,
            failed_supportive=failed_supportive,
            diagnostics=diagnostics,
        )

    def _run_tier(self, criteria_list: List[str], evaluators: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Executes evaluators for a specific priority tier."""
        passed, failed = [], []
        for criterion in criteria_list:
            check_fn = evaluators.get(criterion)
            if check_fn is None:
                # Unknown criterion in config fails closed for safety
                failed.append(criterion)
                continue
            if check_fn():
                passed.append(criterion)
            else:
                failed.append(criterion)
        return passed, failed

    def _check_measurement_availability(
        self, df: pd.DataFrame, gene_col: str, diagnostics: Dict[str, Any]
    ) -> bool:
        """Verifies that numeric measurements exist and meet minimum non-null coverage."""
        if df.empty or gene_col not in df.columns:
            diagnostics["measurement_coverage"] = 0.0
            return False

        feature_cols = [c for c in df.columns if c != gene_col]
        if not feature_cols:
            diagnostics["measurement_coverage"] = 0.0
            return False

        numeric_df = df[feature_cols].apply(pd.to_numeric, errors="coerce")
        total_cells = numeric_df.size
        valid_cells = int(numeric_df.notna().sum().sum())
        coverage = valid_cells / total_cells if total_cells > 0 else 0.0

        diagnostics["measurement_coverage"] = round(coverage, 4)
        return coverage >= self.min_valid_measurement_ratio

    def _check_sample_size(
        self,
        df: pd.DataFrame,
        gene_col: str,
        metadata: Dict[str, Any],
        diagnostics: Dict[str, Any],
    ) -> bool:
        """Verifies sample count from metadata or infers from feature columns."""
        if "sample_count" in metadata and metadata["sample_count"] is not None:
            sample_count = int(metadata["sample_count"])
        else:
            sample_count = len([c for c in df.columns if c != gene_col])

        diagnostics["effective_sample_count"] = sample_count
        return sample_count >= self.min_samples

    def _check_gene_annotation(
        self, df: pd.DataFrame, gene_col: str, diagnostics: Dict[str, Any]
    ) -> bool:
        """Verifies that gene identifiers conform to standard HGNC symbol syntax without duplicate row IDs."""
        if df.empty or gene_col not in df.columns:
            diagnostics["valid_gene_symbol_ratio"] = 0.0
            return False

        symbols = df[gene_col].dropna().astype(str).str.strip()
        if symbols.empty:
            diagnostics["valid_gene_symbol_ratio"] = 0.0
            return False

        valid_mask = symbols.apply(lambda s: bool(self.HGNC_PATTERN.match(s)))
        valid_ratio = float(valid_mask.mean())
        
        # For guide-level screening tables, multiple rows per gene symbol are expected.
        # Check uniqueness on sgrna_id if available, otherwise allow unique gene symbols.
        id_col = "sgrna_id" if "sgrna_id" in df.columns else gene_col
        has_duplicates = bool(df[id_col].duplicated().any()) if id_col in df.columns else bool(symbols.duplicated().any())

        diagnostics["valid_gene_symbol_ratio"] = round(valid_ratio, 4)
        diagnostics["has_duplicate_row_ids"] = has_duplicates

        return (valid_ratio >= self.min_valid_gene_symbol_ratio) and (not has_duplicates)

    @staticmethod
    def _check_metadata_flag(
        metadata: Dict[str, Any], key: str, diagnostics: Dict[str, Any]
    ) -> bool:
        """Evaluates boolean provenance flags supplied in dataset metadata."""
        val = bool(metadata.get(key, False))
        diagnostics[key] = val
        return val