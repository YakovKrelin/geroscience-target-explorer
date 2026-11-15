import pandas as pd


def run_go_enrichment(gene_list: list):
  """Заглушка или обертка для GSEapy GO Biological Process Enrichment."""
  # В продакшене здесь вызывается gseapy.enrichr()
  # Возвращает датафрейм с колонками: Term, Adjusted P-value, Overlap, Combined Score
  if not gene_list:
    return pd.DataFrame()

  # Возвращаем структуру для теста/интеграции
  return pd.DataFrame({
      "Term": [
          "Regulation of cellular response to stress (GO:0080334)",
          "Autophagy (GO:0006914)",
          "Aging (GO:0007568)",
      ],
      "Adjusted P-value": [1e-12, 1e-9, 1e-7],
      "Overlap": ["12/45", "8/30", "10/50"],
      "Combined Score": [250.5, 180.2, 140.0],
  })