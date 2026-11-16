import networkx as nx
import pandas as pd
import requests


def fetch_string_interactions(gene_list: list, species_taxid: int = 9606):
  """Retrieves the PPI network from the STRING API for a list of genes."""
  string_api_url = "https://string-db.org/api/json/network"
  params = {
      "identifiers": "\r".join(gene_list),
      "species": species_taxid,
      "required_score": 400,
      "add_nodes": 0,
  }
  try:
    response = requests.post(string_api_url, data=params)
    if response.status_code == 200:
      data = response.json()
      edges = [
          (item["preferredName_A"], item["preferredName_B"], item["score"])
          for item in data
      ]
      G = nx.Graph()
      for u, v, w in edges:
        G.add_edge(u, v, weight=float(w) / 1000.0)
      return G
  except Exception as e:
    print(f"Error while requesting the STRING API: {e}")
  return nx.Graph()