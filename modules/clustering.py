import networkx as nx
import pandas as pd
import numpy as np

# Safe import of community algorithms with a fallback option
try:
    from networkx.algorithms.community import louvain_communities
except ImportError:
    try:
        from networkx.algorithms.community import greedy_modularity_communities as louvain_communities
    except ImportError:
        louvain_communities = None

def perform_clustering(data, threshold=0.3):
    """
    Performs clustering and network analysis based on the transferred data or matrix. 

    Parameters: 
    - data: pandas DataFrame or matrix of connections/features. 
    - threshold: edge filtering threshold for constructing a graph. 

    Returns: 
    - G: constructed NetworkX graph 
    - communities: found communities 
    - metrics: dictionary with basic graph metrics     
    """
    # Create a graph based on the input data
    G = nx.Graph()
    
    if isinstance(data, pd.DataFrame):
        # If a DataFrame containing correlations or features is provided, we construct a graph.
        # Example: we assume that this is a square matrix of correlations/weights
        if data.shape[0] == data.shape[1]:
            for i in range(len(data.columns)):
                for j in range(i + 1, len(data.columns)):
                    weight = data.iloc[i, j]
                    if abs(weight) >= threshold:
                        G.add_edge(data.columns[i], data.columns[j], weight=float(weight))
        else:
            # Alternative: correlation between rows/columns
            corr_matrix = data.corr(numeric_only=True)
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    weight = corr_matrix.iloc[i, j]
                    if not np.isnan(weight) and abs(weight) >= threshold:
                        G.add_edge(corr_matrix.columns[i], corr_matrix.columns[j], weight=float(weight))
    
    # If the graph is empty (no edges satisfying the threshold), add a basic structure to avoid crashes
    if G.number_of_edges() == 0 and isinstance(data, pd.DataFrame) and len(data.columns) > 0:
        cols = list(data.columns[:5]) # Take the first few columns for example
        for i in range(len(cols) - 1):
            G.add_edge(cols[i], cols[i+1], weight=1.0)

    # Search for communities
    communities = []
    if G.number_of_nodes() > 0 and louvain_communities is not None:
        try:
            # For the Louvain algorithm, it is desirable to have weights.
            communities = list(louvain_communities(G, weight='weight'))
        except Exception:
            try:
                communities = list(nx.algorithms.community.greedy_modularity_communities(G))
            except Exception:
                communities = [set(G.nodes())]
    elif G.number_of_nodes() > 0:
        communities = [set(G.nodes())]

    # Basic graph metrics
    metrics = {
        "nodes_count": G.number_of_nodes(),
        "edges_count": G.number_of_edges(),
        "communities_count": len(communities)
    }

    return G, communities, metrics