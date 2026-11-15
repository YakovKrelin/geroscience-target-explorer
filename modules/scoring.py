import numpy as np
import pandas as pd


def calculate_target_scores(
    df: pd.DataFrame, weights: dict, lambda_penalty: float
) -> pd.DataFrame:
  """Вычисляет интегральный скор мишеней на основе математической модели."""
  df_scored = df.copy()

  # Нормализация метрик M_1 ... M_4
  df_scored["M_1"] = 1.0 - np.minimum(
      1.0, -np.log10(df_scored["mr_p_value"]) / 10.0
  )

  max_net = df_scored["network_score"].max()
  df_scored["M_2"] = np.log(1 + df_scored["network_score"]) / np.log(
      1 + (max_net if max_net > 0 else 1)
  )

  abs_slope = np.abs(df_scored["expression_slope"])
  max_slope = abs_slope.max()
  df_scored["M_3"] = abs_slope / (max_slope if max_slope > 0 else 1.0)

  df_scored["M_4"] = df_scored["hallmarks_count"] / 14.0

  # Аддитивная линейная комбинация
  linear_comb = (
      weights["genetics"] * df_scored["M_1"]
      + weights["network"] * df_scored["M_2"]
      + weights["expression"] * df_scored["M_3"]
      + weights["hallmarks"] * df_scored["M_4"]
  )

  # Штраф за онкогенный риск
  safety_multiplier = 1.0 - (lambda_penalty * df_scored["oncogenic_risk_flag"])

  df_scored["Target_Score"] = linear_comb * safety_multiplier * 100.0
  return df_scored.sort_values(by="Target_Score", ascending=False).reset_index(
      drop=True
  )