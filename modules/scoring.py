import pandas as pd
import numpy as np

def calculate_target_scores(df, weights):
    """
    Computes weighted geroscience target scores and an Objectivity/Hard Evidence ratio
    to filter out literature/network bias.
    """
    # Create a copy to avoid modifying original dataframe
    scored_df = df.copy()
    
    # Normalizing weights just in case
    total_weight = sum(weights.values())
    if total_weight > 0:
        w_gen = weights.get('genetics', 0.3) / total_weight
        w_net = weights.get('network', 0.2) / total_weight
        w_exp = weights.get('expression', 0.2) / total_weight
        w_hal = weights.get('hallmarks', 0.3) / total_weight
    else:
        w_gen, w_net, w_exp, w_hal = 0.25, 0.25, 0.25, 0.25

    # 1. Genetics component (lower p-value -> higher score, e.g., -log10(p))
    # Handling potential zeros or very small numbers
    p_vals = scored_df['mr_p_value'].replace(0, 1e-300)
    gen_score = -np.log10(p_vals)
    gen_score_norm = (gen_score - gen_score.min()) / (gen_score.max() - gen_score.min() + 1e-9) * 100

    # 2. Network component
    net_score_norm = scored_df['network_score'] # assumed 0-100 scale

    # 3. Expression slope magnitude (absolute change with age)
    exp_score = scored_df['expression_slope'].abs()
    exp_score_norm = (exp_score - exp_score.min()) / (exp_score.max() - exp_score.min() + 1e-9) * 100

    # 4. Hallmarks coverage
    max_hallmarks = scored_df['hallmarks_count'].max() if 'hallmarks_count' in scored_df else 14
    hal_score_norm = (scored_df['hallmarks_count'] / max(max_hallmarks, 1)) * 100

    # Base weighted score before safety penalty
    base_score = (
        w_gen * gen_score_norm +
        w_net * net_score_norm +
        w_exp * exp_score_norm +
        w_hal * hal_score_norm
    )

    # 5. Oncogenic Safety Penalty
    # If oncogenic_risk_flag == 1, apply penalty multiplier based on user setting
    penalty_multiplier = weights.get('safety_penalty', 0.5)
    safety_penalty = scored_df['oncogenic_risk_flag'].apply(lambda x: penalty_multiplier if x == 1 else 1.0)

    final_score = base_score * safety_penalty

    scored_df['Target_Score'] = final_score.round(4)

    # --- NEW: Hard Evidence vs Network/Literature Bias Metric ---
    # Hard evidence relies on Genetics (MR) + Expression Dynamics (GTEx)
    hard_evidence_component = (w_gen * gen_score_norm) + (w_exp * exp_score_norm)
    # Total positive components before penalty
    total_components = hard_evidence_component + (w_net * net_score_norm) + (w_hal * hal_score_norm) + 1e-9
    
    # Ratio of objective/hard data vs network/annotation weight (0.0 to 1.0)
    scored_df['hard_evidence_ratio'] = (hard_evidence_component / total_components).round(2)

    # Sort by final score descending
    scored_df = scored_df.sort_values(by='Target_Score', ascending=False).reset_index(drop=True)
    
    return scored_df