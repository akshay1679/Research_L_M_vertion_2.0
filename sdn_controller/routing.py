# sdn_controller/routing.py

import networkx as nx
import math


class RoutingEngine:
    """
    Delay-aware routing engine.
    Implements Section V-B and Eq. (1) of the paper.
    """

    def __init__(self, of_db):
        self.of_db = of_db

    # ---------------------------------------
    # Cost Function (Paper Eq. 1)
    # ---------------------------------------
    @staticmethod
    def link_cost(link):
        utilization = min(link.utilization, 0.99)
        base_delay = (
            link.propagation_delay +
            link.switching_delay +
            link.processing_delay
        )
        return base_delay / (1.0 - utilization)

    # ---------------------------------------
    # Graph Construction
    # ---------------------------------------
    def _build_graph(self):
        G = nx.DiGraph()
        for link in self.of_db.links.values():
            cost = self.link_cost(link)
            G.add_edge(link.src, link.dst, weight=cost, link=link)
        return G

    # ---------------------------------------
    # RP Selection (Paper-defined)
    # ---------------------------------------
    def select_rp(self, dsts):
        """
        Select RP that minimizes maximum distance to all subscribers.
        """
        G = self._build_graph()
        candidates = list(self.of_db.switches.keys())

        best_rp = None
        best_cost = math.inf

        for rp in candidates:
            try:
                distances = [
                    nx.shortest_path_length(G, rp, d, weight="weight")
                    for d in dsts
                ]
                cost = max(distances)
                if cost < best_cost:
                    best_cost = cost
                    best_rp = rp
            except nx.NetworkXNoPath:
                continue

        return best_rp

    # ---------------------------------------
    # Multicast Path Calculation
    # ---------------------------------------
    def compute_multicast_tree(self, src, dsts):
        """
        Implements src → RP → subscribers (no Steiner shortcut).
        """
        G = self._build_graph()
        rp = self.select_rp(dsts)

        if rp is None:
            return []

        links = []

        # Source → RP
        path = nx.shortest_path(G, src, rp, weight="weight")
        links.extend(self._path_to_links(G, path))

        # RP → Subscribers
        for d in dsts:
            path = nx.shortest_path(G, rp, d, weight="weight")
            links.extend(self._path_to_links(G, path))

        return list(set(links))

    def _path_to_links(self, G, path):
        links = []
        for i in range(len(path) - 1):
            links.append(G[path[i]][path[i+1]]["link"])
        return links
