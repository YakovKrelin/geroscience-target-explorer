import pandas as pd
import numpy as np

def robust_z_score_normalize(series: pd.Series, config: dict) -> pd.Series:
    """
    Performs robust Z-score normalization using Median Absolute Deviation (MAD).
    Enforces deterministic fallback rules according to v1.2.1-Implementation-Freeze:
    1. If MAD == 0, evaluates valid data coverage ratio.
    2. If coverage >= threshold (default 40%), applies rank percentile normalization.
    3. If coverage < threshold, sets values to NaN (set_null).
    """
    norm_cfg = config.get("normalization", {})
    scale_factor = norm_cfg.get("mad_scale_factor", 1.4826)
    clip_min, clip_max = norm_cfg.get("clip_range", [-5.0, 5.0])
    
    fallback_rules = norm_cfg.get("fallback_rules", {})
    coverage_threshold = fallback_rules.get("mad_zero_valid_coverage_threshold", 0.40)
    fallback_action = fallback_rules.get("fallback_action_if_valid", "rank_percentile_normalization")

    # Drop NaNs for intermediate statistical calculations
    valid_data = series.dropna()
    total_count = len(series)
    
    if total_count == 0:
        return series

    valid_coverage = len(valid_data) / total_count

    # Check against minimum valid data coverage threshold
    if valid_coverage < coverage_threshold:
        return pd.Series(np.nan, index=series.index)

    median = valid_data.median()
    mad = (valid_data - median).abs().median() * scale_factor

    # Handle MAD == 0 edge case (identical or nearly identical values)
    if mad == 0.0 or np.isclose(mad, 0.0):
        if fallback_action == "rank_percentile_normalization":
            return series.rank(pct=True, na_option='keep')
        else:
            return pd.Series(np.nan, index=series.index)

    # Standard robust Z-score calculation
    robust_z = scale_factor * (series - median) / mad

    # Apply clipping to control extreme outliers
    clipped_z = robust_z.clip(lower=clip_min, upper=clip_max)
    
    # Smooth sigmoid mapping to scale values into the [0, 1] range
    normalized = 1.0 / (1.0 + np.exp(-clipped_z))
    
    return normalized