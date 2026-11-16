from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

@dataclass
class EvidenceAxis:
    """Represents an independent stream of scientific evidence."""
    score: float  # Normalized score between 0.0 and 1.0
    confidence_grade: str  # 'A', 'B+', 'B', 'C', etc.
    sources: List[str] = field(default_factory=list)  # DOIs, database IDs, URLs
    description: str = ""

@dataclass
class CausalProfile:
    """Differentiates correlation from causation and defines intervention modality."""
    is_causal_driver: bool
    causal_confidence: float  # 0.0 to 1.0
    recommended_modality: str  # 'activation', 'inhibition', 'targeted_degradation', 'modulation'
    expected_benefit: str
    known_risks: List[str] = field(default_factory=list)

@dataclass
class TargetEvidenceRecord:
    """Comprehensive multi-axis evidence record for a geroscience target (v1.3)."""
    gene_symbol: str
    overall_priority: str  # 'High', 'Moderate', 'Low'
    overall_probability: float  # Bayesian calibrated probability [0.0 - 1.0]
    probability_ci: tuple  # (lower_bound, upper_bound)
    
    # 1. Multi-axis evidence streams
    human_genetic: EvidenceAxis
    transcriptomic_aging: EvidenceAxis
    causal_perturbation: EvidenceAxis
    model_organism: EvidenceAxis
    clinical_translational: EvidenceAxis
    safety_tractability: EvidenceAxis
    
    # 2. Causal & intervention details
    causal_profile: CausalProfile
    
    # 3. Tissue-specific scores (0.0 - 1.0)
    tissue_relevance: Dict[str, float] = field(default_factory=lambda: {
        "brain": 0.0,
        "skeletal_muscle": 0.0,
        "liver": 0.0,
        "immune_cells": 0.0,
        "vascular_endothelium": 0.0,
        "stem_compartments": 0.0
    })
    
    # 4. Actionable recommendation layer
    validation_gap: str = ""
    recommended_next_test: str = ""

    def to_dict(self) -> dict:
        """Serializes the evidence record into a structured dictionary/JSON."""
        return {
            "gene_symbol": self.gene_symbol,
            "overall_priority": self.overall_priority,
            "overall_probability": self.overall_probability,
            "probability_ci": list(self.probability_ci),
            "axes": {
                "human_genetic": self.human_genetic.__dict__,
                "transcriptomic_aging": self.transcriptomic_aging.__dict__,
                "causal_perturbation": self.causal_perturbation.__dict__,
                "model_organism": self.model_organism.__dict__,
                "clinical_translational": self.clinical_translational.__dict__,
                "safety_tractability": self.safety_tractability.__dict__,
            },
            "causal_profile": self.causal_profile.__dict__,
            "tissue_relevance": self.tissue_relevance,
            "validation_gap": self.validation_gap,
            "recommended_next_test": self.recommended_next_test
        }

# --- Пример инстанцирования для FOXO3 (v1.3) ---
def get_sample_foxo3_record() -> TargetEvidenceRecord:
    return TargetEvidenceRecord(
        gene_symbol="FOXO3",
        overall_priority="High",
        overall_probability=0.78,
        probability_ci=(0.64, 0.88),
        human_genetic=EvidenceAxis(
            score=0.90, confidence_grade="A", 
            sources=["GWAS Longevity Cohorts", "Mendelian Randomization PMID:31234567"],
            description="Strong genetic association with extreme human longevity across diverse populations."
        ),
        transcriptomic_aging=EvidenceAxis(
            score=0.82, confidence_grade="B+",
            sources=["GTEx v8", "Age-associated bulk & single-cell RNA-seq"],
            description="Downregulated in multiple aged tissues; regulates stress-response signatures."
        ),
        causal_perturbation=EvidenceAxis(
            score=0.75, confidence_grade="B",
            sources=["CRISPR knockout assays", "Overexpression models"],
            description="Upregulation extends stress resistance and cellular survival."
        ),
        model_organism=EvidenceAxis(
            score=0.88, confidence_grade="A",
            sources=["GenAge Model Organisms", "C. elegans daf-16 ortholog studies"],
            description="Robust lifespan extension across C. elegans, Drosophila, and mice."
        ),
        clinical_translational=EvidenceAxis(
            score=0.65, confidence_grade="B-",
            sources=["Biomarker cohorts", "Metabolic disease trials"],
            description="Correlates with reduced cardiometabolic risk and preserved cognitive function."
        ),
        safety_tractability=EvidenceAxis(
            score=0.70, confidence_grade="B",
            sources=["LOEUF constraint metrics", "DGIdb druggability"],
            description="Moderate genetic constraint; druggable via upstream kinase modulation (e.g., AKT/SGK)."
        ),
        causal_profile=CausalProfile(
            is_causal_driver=True,
            causal_confidence=0.82,
            recommended_modality="activation",
            expected_benefit="Improved stress resilience, enhanced proteostasis, metabolic health",
            known_risks=["Context-dependent tumor suppression vs. progression roles in specific cancer subtypes"]
        ),
        tissue_relevance={
            "brain": 0.85,
            "skeletal_muscle": 0.80,
            "liver": 0.75,
            "immune_cells": 0.90,
            "vascular_endothelium": 0.70,
            "stem_compartments": 0.85
        },
        validation_gap="Lack of direct human cellular perturbation longitudinal data in target tissues.",
        recommended_next_test="CRISPR activation perturbation in human induced pluripotent stem cell (iPSC) derived neurons + multi-omic aging biomarker panel."
    )

if __name__ == "__main__":
    record = get_sample_foxo3_record()
    print(json.dumps(record.to_dict(), indent=4, ensure_ascii=False))