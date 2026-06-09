"""
graph_engine.py — NetworkX graph operations and risk scoring.

Builds a directed supply chain graph, scores each node for risk, identifies
single points of failure, and renders the graph as a PNG image.

This module has NO web or database dependencies — it can be unit-tested
in isolation.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, field

import matplotlib
matplotlib.use("Agg")   # must be called before pyplot is imported; safe for servers
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

from config import (
    FRIENDLY_NATIONS,
    GRAPH_OUTPUT_DIR,
    HIGH_RISK_COUNTRIES,
    MAX_RISK_SCORE,
    RISK_WEIGHTS,
)


@dataclass
class SupplierData:
    name: str
    country: str | None
    tier: int
    component: str | None = None
    is_focal_company: bool = False


@dataclass
class EdgeData:
    supplier: str
    customer: str
    component: str | None = None


@dataclass
class GraphAnalysisResult:
    nodes: list[SupplierData]
    edges: list[EdgeData]
    risk_scores: dict[str, int]          # node name → risk score 0-100
    single_points_of_failure: list[str]  # node names
    graph_image_bytes: bytes
    graph_data_json: dict                # for future JS visualization


def _country_is_high_risk(country: str | None) -> bool:
    if not country:
        return False
    return any(h.lower() in country.lower() for h in HIGH_RISK_COUNTRIES)


def _score_node(
    name: str,
    data: SupplierData,
    G: nx.DiGraph,
    spf_names: set[str],
) -> int:
    score = 0
    if _country_is_high_risk(data.country):
        score += RISK_WEIGHTS["high_risk_country"]
    if name in spf_names:
        score += RISK_WEIGHTS["single_point_of_failure"]
    if G.out_degree(name) >= 3:
        score += RISK_WEIGHTS["high_tier_concentration"]
    if not data.country:
        score += RISK_WEIGHTS["missing_country_data"]
    return min(score, MAX_RISK_SCORE)


def _find_single_points_of_failure(G: nx.DiGraph, focal: str) -> set[str]:
    """
    A non-focal node is a single point of failure if removing it disconnects
    the focal company from any of its upstream suppliers.
    Uses NetworkX's articulation points on an undirected view.
    """
    if focal not in G:
        return set()
    undirected = G.to_undirected()
    try:
        art_points = set(nx.articulation_points(undirected))
    except Exception:
        art_points = set()
    # Only flag non-focal nodes that are NOT in friendly nations
    spf = set()
    for node in art_points:
        if node == focal:
            continue
        node_data = G.nodes[node].get("data")
        if node_data and _country_is_high_risk(node_data.country):
            spf.add(node)
    return spf


def _node_color(data: SupplierData, risk_score: int) -> str:
    if data.is_focal_company:
        return "#2a6496"      # blue — your company
    if risk_score >= 60:
        return "#a02020"      # red — high risk
    if risk_score >= 30:
        return "#c86020"      # orange — medium risk
    country = (data.country or "").strip()
    if any(f.lower() in country.lower() for f in FRIENDLY_NATIONS):
        return "#2d7a3a"      # green — friendly nation
    return "#5a6270"          # grey — unknown / neutral


def build_and_analyze(
    nodes: list[SupplierData],
    edges: list[EdgeData],
    focal_company: str,
    analysis_id: int,
) -> GraphAnalysisResult:
    """Build the NetworkX graph, score all nodes, render PNG, return results."""
    G = nx.DiGraph()

    node_lookup: dict[str, SupplierData] = {}
    for n in nodes:
        G.add_node(n.name, data=n)
        node_lookup[n.name] = n

    for e in edges:
        G.add_edge(e.supplier, e.customer, component=e.component or "")

    # Identify single points of failure
    spf = _find_single_points_of_failure(G, focal_company)

    # Score every node
    risk_scores: dict[str, int] = {}
    for name in G.nodes:
        data = node_lookup.get(name, SupplierData(name=name, country=None, tier=0))
        risk_scores[name] = _score_node(name, data, G, spf)

    # --- Render graph ---
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor("#f4f6f9")
    ax.set_facecolor("#f4f6f9")

    # Layout: group by tier on horizontal axis
    pos: dict[str, tuple] = {}
    tier_groups: dict[int, list[str]] = {}
    for name in G.nodes:
        data = node_lookup.get(name)
        tier = data.tier if data else 0
        tier_groups.setdefault(tier, []).append(name)

    x_spacing = 3.5
    for tier, names in sorted(tier_groups.items()):
        x = tier * x_spacing
        for i, name in enumerate(names):
            y = i - (len(names) - 1) / 2.0
            pos[name] = (x, y * 1.8)

    node_colors = []
    for name in G.nodes:
        data = node_lookup.get(name, SupplierData(name=name, country=None, tier=0))
        node_colors.append(_node_color(data, risk_scores.get(name, 0)))

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#aab8c8",
                           arrows=True, arrowsize=15, width=1.5,
                           connectionstyle="arc3,rad=0.05")

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=2200, alpha=0.92)

    labels = {}
    for name in G.nodes:
        data = node_lookup.get(name)
        country = f"\n({data.country})" if data and data.country else ""
        labels[name] = f"{name}{country}"

    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=7, font_color="white", font_weight="bold")

    # Edge component labels
    edge_labels = {(e.supplier, e.customer): e.component or ""
                   for e in edges if e.component}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                 font_size=6, font_color="#445566")

    # Legend
    legend_items = [
        mpatches.Patch(color="#2a6496", label="Your company"),
        mpatches.Patch(color="#a02020", label="High risk (score ≥ 60)"),
        mpatches.Patch(color="#c86020", label="Medium risk (score 30–59)"),
        mpatches.Patch(color="#2d7a3a", label="Friendly nation"),
        mpatches.Patch(color="#5a6270", label="Unknown / neutral"),
    ]
    ax.legend(handles=legend_items, loc="upper left", fontsize=8,
              framealpha=0.9, facecolor="#f4f6f9")

    ax.set_title("Supply Chain Dependency Graph — FriendShore Risk Analysis",
                 fontsize=11, color="#1a1a2e", pad=12)
    ax.axis("off")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    image_bytes = buf.getvalue()

    # Persist PNG to disk
    os.makedirs(GRAPH_OUTPUT_DIR, exist_ok=True)
    image_path = os.path.join(GRAPH_OUTPUT_DIR, f"graph_{analysis_id}.png")
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    # Build graph JSON for future JS visualization
    graph_json = {
        "nodes": [
            {
                "id": n.name,
                "country": n.country,
                "tier": n.tier,
                "risk_score": risk_scores.get(n.name, 0),
                "is_spf": n.name in spf,
            }
            for n in nodes
        ],
        "edges": [
            {"from": e.supplier, "to": e.customer, "label": e.component or ""}
            for e in edges
        ],
    }

    return GraphAnalysisResult(
        nodes=nodes,
        edges=edges,
        risk_scores=risk_scores,
        single_points_of_failure=list(spf),
        graph_image_bytes=image_bytes,
        graph_data_json=graph_json,
    )
