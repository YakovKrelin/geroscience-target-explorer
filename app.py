import networkx as nx
import pandas as pd
import streamlit as st

# Импорт наших модулей из папки modules
from modules.clustering import detect_functional_modules
from modules.enrichment import run_go_enrichment
from modules.net_loader import fetch_string_interactions
from modules.pdf_exporter import generate_due_diligence_pdf
from modules.scoring import calculate_target_scores

# Настройка страницы Streamlit
st.set_page_config(
    page_title="Geroscience Target Explorer", page_icon="🧬", layout="wide"
)

st.title("🧬 Geroscience Target Explorer")
st.markdown(
    "Interactive multi-omic platform for geroscience target prioritization,"
    " PPI network analysis, and Due Diligence reporting."
)

# Боковая панель: настройка весов модели скоринга
st.sidebar.header("⚖️ Scoring Weights & Parameters")
w_genetics = st.sidebar.slider(
    "Genetics / Causality (Mendelian Randomization)", 0.0, 1.0, 0.3
)
w_network = st.sidebar.slider("Network Centrality & Propagation", 0.0, 1.0, 0.2)
w_expression = st.sidebar.slider(
    "Expression Dynamics (GTEx Age Slope)", 0.0, 1.0, 0.2
)
w_hallmarks = st.sidebar.slider(
    "Hallmarks of Aging Coverage", 0.0, 1.0, 0.3
)

# Нормализация весов, чтобы в сумме давали 1.0
total_w = w_genetics + w_network + w_expression + w_hallmarks
if total_w > 0:
  weights = {
      "genetics": w_genetics / total_w,
      "network": w_network / total_w,
      "expression": w_expression / total_w,
      "hallmarks": w_hallmarks / total_w,
  }
else:
  weights = {
      "genetics": 0.25,
      "network": 0.25,
      "expression": 0.25,
      "hallmarks": 0.25,
  }

lambda_penalty = st.sidebar.slider(
    "Oncogenic Safety Penalty Multiplier (λ)", 0.0, 1.0, 0.5
)

# Загрузка демонстрационного набора данных (Master Dataset)
@st.cache_data
def load_master_data():
  data = {
      "gene": ["SIRT1", "FOXO3", "MTOR", "TP53", "APOE", "AMPK"],
      "mr_p_value": [1e-8, 1e-6, 1e-4, 1e-2, 5e-7, 1e-9],
      "network_score": [85.0, 78.5, 92.0, 45.0, 60.0, 88.0],
      "expression_slope": [-0.045, -0.030, 0.015, 0.050, -0.020, -0.055],
      "hallmarks_count": [10, 12, 8, 4, 6, 11],
      "oncogenic_risk_flag": [0, 0, 0, 1, 0, 0],
  }
  return pd.DataFrame(data)


df_raw = load_master_data()

# Вычисление скоров с помощью модуля скоринга
df_scored = calculate_target_scores(df_raw, weights, lambda_penalty)

# Основные вкладки приложения
tab1, tab2, tab3 = st.tabs(
    ["📊 Target Prioritization", "🕸️ PPI Network & Modules", "📄 Due Diligence PDF"]
)

with tab1:
  st.subheader("Prioritized Geroscience Targets Ranking")
  st.dataframe(df_scored, use_container_width=True)

with tab2:
  st.subheader("Protein-Protein Interaction (PPI) & Functional Clusters")
  selected_gene = st.selectbox(
      "Select Target Asset for Network Analysis", df_scored["gene"].tolist()
  )

  if st.button("Fetch STRING PPI & Run Clustering"):
    with st.spinner("Connecting to STRING DB and running Louvain clustering..."):
      gene_list = df_scored["gene"].tolist()
      G = fetch_string_interactions(gene_list)
      if G.number_of_nodes() > 0:
        modules = detect_functional_modules(G)
        st.success(
            f"Successfully built network with {G.number_of_nodes()} nodes and"
            f" {G.number_of_edges()} edges."
        )
        st.write("Detected Functional Modules mapping:", modules)
      else:
        st.warning(
            "Could not fetch network from STRING API or empty graph returned."
        )

with tab3:
  st.subheader("Automated Due Diligence Report Generation")
  target_to_export = st.selectbox(
      "Choose Target for PDF Export", df_scored["gene"].tolist()
  )

  selected_row = df_scored[df_scored["gene"] == target_to_export].iloc[0]

  if st.button("Generate Due Diligence PDF"):
    pdf_bytes = generate_due_diligence_pdf(
        target_name=target_to_export, score=selected_row["Target_Score"]
    )
    st.download_button(
        label=f"📥 Download Report for {target_to_export}",
        data=pdf_bytes,
        file_name=f"{target_to_export}_Due_Diligence.pdf",
        mime="application/pdf",
    )