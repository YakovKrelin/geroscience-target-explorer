import streamlit as st
import pandas as pd
import numpy as np

# Импорт модулей вашего проекта
from modules.network_loader import fetch_string_interactions
from modules.scoring import calculate_target_scores
from modules.clustering import perform_clustering
from modules.enrichment import run_enrichment
from modules.pdf_exporter import generate_pdf_report

# Конфигурация страницы Streamlit
st.set_page_config(
    page_title="Geroscience Target Explorer",
    page_icon="🧬",
    layout="wide"
)

def main():
    # --- Global SaaS Header / Hero Section ---
    st.markdown(
        """
        <div style="background-color: #0e1117; padding: 20px; border-radius: 10px; border: 1px solid #262730; margin-bottom: 25px;">
            <h1 style="color: #ffffff; font-family: 'Inter', sans-serif; font-weight: 700; margin-bottom: 5px;">
                🧬 Geroscience Target Explorer
            </h1>
            <p style="color: #a3a8b4; font-size: 18px; font-family: 'Inter', sans-serif; margin-top: 0;">
                AI-driven multi-omic prioritization platform for geroscience and longevity research. 
                Integrating Mendelian Randomization, network topology, and aging hallmarks.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Sidebar: Scoring Weights & Parameters ---
    st.sidebar.header("⚖️ Scoring Weights & Parameters")
    
    w_genetics = st.sidebar.slider("Genetics / Causality (Mendelian Randomization)", 0.0, 1.0, 0.30, 0.05)
    w_network = st.sidebar.slider("Network Centrality & Propagation", 0.0, 1.0, 0.20, 0.05)
    w_expression = st.sidebar.slider("Expression Dynamics (GTEx Age Slope)", 0.0, 1.0, 0.20, 0.05)
    w_hallmarks = st.sidebar.slider("Hallmarks of Aging Coverage", 0.0, 1.0, 0.30, 0.05)
    safety_penalty = st.sidebar.slider("Oncogenic Safety Penalty Multiplier (λ)", 0.0, 1.0, 0.50, 0.05)

    weights = {
        'genetics': w_genetics,
        'network': w_network,
        'expression': w_expression,
        'hallmarks': w_hallmarks,
        'safety_penalty': safety_penalty
    }

    # Dataset для демонстрации и анализа таргетов
    @st.cache_data
    def load_initial_data():
        data = {
            'gene': ['FOXO3', 'AMPK', 'SIRT1', 'MTOR', 'APOE', 'TP53'],
            'mr_p_value': [0.000001, 0.00000001, 0.000001, 0.0001, 0.000005, 0.01],
            'network_score': [78.5, 88.0, 85.0, 92.0, 60.0, 45.0],
            'expression_slope': [-0.03, -0.055, -0.045, 0.015, -0.02, 0.05],
            'hallmarks_count': [12, 11, 10, 8, 6, 4],
            'oncogenic_risk_flag': [0, 0, 0, 0, 0, 1],
            'M_1': [0.4, 0.1, 0.2, 0.6, 0.3699, 0.8],
            'M_2': [0.9654, 0.9903, 0.9827, 1.0, 0.907, 0.8447],
            'M_3': [0.5455, 1.0, 0.8182, 0.2727, 0.3636, 0.9091],
            'M_4': [0.8571, 0.7857, 0.7143, 0.5714, 0.4286, 0.2857]
        }
        return pd.DataFrame(data)

    raw_df = load_initial_data()

    # Расчет скоров и индекса объективности (Hard Evidence Ratio)
    ranked_df = calculate_target_scores(raw_df, weights)

    # --- Navigation Tabs (Global Audience Architecture) ---
    tab_prioritization, tab_network, tab_methodology, tab_pdf = st.tabs([
        "📊 Target Prioritization", 
        "🕸️ PPI Network & Modules", 
        "📚 Methodology & Data",
        "📄 Due Diligence PDF"
    ])

    with tab_prioritization:
        st.subheader("Prioritized Geroscience Targets Ranking")
        
        # Переименование колонок для чистоты интерфейса
        display_df = ranked_df.rename(columns={
            'gene': 'Gene',
            'mr_p_value': 'MR p-value',
            'network_score': 'Network Score',
            'expression_slope': 'GTEx Slope',
            'hallmarks_count': 'Hallmarks',
            'oncogenic_risk_flag': 'Oncogenic Flag',
            'Target_Score': 'Target Score',
            'hard_evidence_ratio': 'Evidence-to-Bias Ratio (1.0 = Pure Data)'
        })

        st.dataframe(display_df, use_container_width=True)

        st.info(
            "💡 **Explanation of 'Evidence-to-Bias Ratio':** Values closer to `1.0` indicate that the target's rank "
            "is driven primarily by hard biological data (Mendelian Randomization & GTEx expression dynamics). "
            "Values closer to `0.0` indicate heavier reliance on network topology and curated annotations (which can carry literature bias)."
        )

    with tab_network:
        st.subheader("Protein-Protein Interaction (PPI) & Functional Modules")
        st.write("Explore network clusters, connectivity degrees, and functional gene groupings.")
        
        selected_gene = st.selectbox("Select Target Gene for Network Neighborhood:", ranked_df['gene'].tolist())
        if st.button("Fetch & Analyze Network"):
            with st.spinner(f"Fetching interactions for {selected_gene} via STRING..."):
                net_data = fetch_string_interactions(selected_gene)
                st.success(f"Successfully loaded network context for {selected_gene}.")

    with tab_methodology:
        st.subheader("Methodological Framework & Data Provenance")
        st.markdown("""
        The **Geroscience Target Explorer** utilizes a multi-layered evidentiary framework designed to bridge the gap between statistical genetics and functional longevity biology, minimizing literature bias.

        ---

        ### 1. Core Scoring Components
        * **Genetics / Causality (Mendelian Randomization):** Derived from large-scale GWAS summary statistics. Evaluates the causal effect of target expression on longevity or healthspan traits, returning robust instrumental variable $p$-values ($mr\_p\_value$).
        * **Expression Dynamics (GTEx Age Slope):** Quantifies age-associated transcriptional changes across human tissues using data from the Genotype-Tissue Expression (GTEx) project. Targets with significant directional shifts in aging tissues are prioritized.
        * **Hallmarks of Aging Coverage:** Evaluates target involvement across established biological hallmarks of aging (e.g., mitochondrial dysfunction, cellular senescence, genomic instability).
        * **Network Centrality & Propagation:** Employs topological metrics (such as PageRank and betweenness centrality) over high-confidence Protein-Protein Interaction (PPI) networks (STRING database).

        ---

        ### 2. Mitigating Literature Bias: The Evidence-to-Bias Ratio
        To counter the common bioinformatics pitfall where heavily studied genes (e.g., *TP53*, *APOE*) dominate rankings due to publication volume rather than biological merit, our platform introduces the **Evidence-to-Bias Ratio**:
        * **Hard Evidence:** Driven strictly by raw statistical genetics (MR) and objective transcriptomic aging slopes.
        * **Annotation/Network Weight:** Reflects topological and curated database context.
        * *Targets with a high ratio ($>0.70$) represent high-confidence, data-driven candidates rather than historical literature favorites.*

        ---

        ### 3. Safety & Clinical Translation Filters
        * **Oncogenic Safety Penalty ($\lambda$):** Implements a strict penalty multiplier for targets with annotated tumor-suppressive or oncogenic dual-roles, ensuring candidates are safe for healthy longevity interventions.
        """)

    with tab_pdf:
        st.subheader("Generate Due Diligence Report")
        st.write("Export a formal PDF dossier summarizing target prioritization, safety profiles, and evidence ratios.")
        
        target_for_pdf = st.selectbox("Select Target for Report:", ranked_df['gene'].tolist(), key="pdf_target")
        if st.button("Generate & Download PDF Report"):
            pdf_file = generate_pdf_report(target_for_pdf, ranked_df)
            st.success(f"Report generated for {target_for_pdf}!")

if __name__ == "__main__":
    main()