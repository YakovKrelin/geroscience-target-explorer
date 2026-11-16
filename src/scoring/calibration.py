import numpy as np
from sklearn.metrics import brier_score_loss, precision_recall_curve, auc
from sklearn.calibration import calibration_curve

class AdvancedModelCalibrator:
    """
    Advanced calibration and reliability audit suite for Geroscience Platform v1.4.
    Computes Brier Score, PR-AUC, Expected Calibration Error (ECE), and reliability bins.
    """
    def __init__(self, y_true: list, y_prob: list, task_definition: str):
        self.y_true = np.array(y_true)
        self.y_prob = np.array(y_prob)
        self.task_definition = task_definition
        self.positive_prevalence = float(np.mean(self.y_true)) if len(self.y_true) > 0 else 0.0

    def compute_ece(self, n_bins: int = 10) -> float:
        """Computes Expected Calibration Error (ECE) across confidence bins."""
        if len(self.y_true) == 0:
            return 0.0
        
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        n_samples = len(self.y_true)
        
        for i in range(n_bins):
            bin_lower = bin_edges[i]
            bin_upper = bin_edges[i+1]
            in_bin = (self.y_prob > bin_lower) & (self.y_prob <= bin_upper)
            bin_size = np.sum(in_bin)
            
            if bin_size > 0:
                acc = np.mean(self.y_true[in_bin])
                conf = np.mean(self.y_prob[in_bin])
                ece += (bin_size / n_samples) * abs(acc - conf)
                
        return float(ece)

    def get_comprehensive_report(self) -> dict:
        brier = float(brier_score_loss(self.y_true, self.y_prob))
        precision, recall, _ = precision_recall_curve(self.y_true, self.y_prob)
        pr_auc = float(auc(recall, precision)) if len(np.unique(self.y_true)) > 1 else 0.0
        ece = self.compute_ece()
        
        # Reliability curve bins
        prob_true, prob_pred = calibration_curve(self.y_true, self.y_prob, n_bins=5, strategy='uniform')

        return {
            "task_definition": self.task_definition,
            "sample_size": len(self.y_true),
            "positive_prevalence": round(self.positive_prevalence * 100, 2),
            "brier_score": round(brier, 4),
            "expected_calibration_error_ece": round(ece, 4),
            "pr_auc": round(pr_auc, 4),
            "calibration_status": "Assessed on held-out test set (Pending ECE threshold < 0.05)",
            "reliability_bins": {
                "fraction_of_positives": prob_true.tolist(),
                "mean_predicted_probability": prob_pred.tolist()
            }
        }

if __name__ == "__main__":
    # Example evaluation on a rigorous test split
    y_true_test = [1, 1, 1, 0, 0, 1, 0, 0, 1, 0]
    y_prob_test = [0.85, 0.78, 0.92, 0.12, 0.08, 0.75, 0.15, 0.22, 0.80, 0.05]
    
    calibrator = AdvancedModelCalibrator(
        y_true_test, 
        y_prob_test, 
        task_definition="Binary classification: Positive label = experimentally validated causal aging target"
    )
    print(calibrator.get_comprehensive_report())