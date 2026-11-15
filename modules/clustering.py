import networkx as nx
from networkx.algorithms.community import louvain_communities


def detect_functional_modules(G: nx.Graph) -> dict:
  """Находит функциональные модули в графе с помощью алгоритма Лувена."""
  if G.number_of_nodes() == 0:
    return {}

  communities = louvain_communities(G, weight="weight", seed=42)
  node_to_module = {}
  for module_id, comm in enumerate(communities):
    for node in comm:
      node_to_module[node] = module_id
  return node_to_module