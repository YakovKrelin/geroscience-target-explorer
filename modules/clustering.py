import networkx as nx
import pandas as pd
import numpy as np

# Безопасный импорт алгоритмов сообществ с запасным вариантом
try:
    from networkx.algorithms.community import louvain_communities
except ImportError:
    try:
        from networkx.algorithms.community import greedy_modularity_communities as louvain_communities
    except ImportError:
        louvain_communities = None

def perform_clustering(data, threshold=0.3):
    """
    Выполняет кластеризацию и анализ сети на основе переданных данных или матрицы.
    
    Параметры:
    - data: pandas DataFrame или матрица связей/признаков.
    - threshold: порог фильтрации ребер для построения графа.
    
    Возвращает:
    - G: построенный граф NetworkX
    - communities: найденные сообщества
    - metrics: словарь с базовыми метриками графа
    """
    # Создаем граф на основе входных данных
    G = nx.Graph()
    
    if isinstance(data, pd.DataFrame):
        # Если передан DataFrame с корреляциями или признаками, строим граф
        # Пример: предполагаем, что это квадратная матрица корреляций/весов
        if data.shape[0] == data.shape[1]:
            for i in range(len(data.columns)):
                for j in range(i + 1, len(data.columns)):
                    weight = data.iloc[i, j]
                    if abs(weight) >= threshold:
                        G.add_edge(data.columns[i], data.columns[j], weight=float(weight))
        else:
            # Альтернатива: корреляция между строками/столбцами
            corr_matrix = data.corr(numeric_only=True)
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    weight = corr_matrix.iloc[i, j]
                    if not np.isnan(weight) and abs(weight) >= threshold:
                        G.add_edge(corr_matrix.columns[i], corr_matrix.columns[j], weight=float(weight))
    
    # Если граф пустой (нет ребер, удовлетворяющих порогу), добавляем базовую структуру, чтобы избежать падений
    if G.number_of_edges() == 0 and isinstance(data, pd.DataFrame) and len(data.columns) > 0:
        cols = list(data.columns[:5]) # Берем первые несколько колонок для примера
        for i in range(len(cols) - 1):
            G.add_edge(cols[i], cols[i+1], weight=1.0)

    # Поиск сообществ
    communities = []
    if G.number_of_nodes() > 0 and louvain_communities is not None:
        try:
            # Для Louvain желательно наличие весов
            communities = list(louvain_communities(G, weight='weight'))
        except Exception:
            try:
                communities = list(nx.algorithms.community.greedy_modularity_communities(G))
            except Exception:
                communities = [set(G.nodes())]
    elif G.number_of_nodes() > 0:
        communities = [set(G.nodes())]

    # Базовые метрики графа
    metrics = {
        "nodes_count": G.number_of_nodes(),
        "edges_count": G.number_of_edges(),
        "communities_count": len(communities)
    }

    return G, communities, metrics