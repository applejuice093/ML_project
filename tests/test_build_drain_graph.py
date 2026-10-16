"""Tests for drain-graph construction from waterway lines."""

import math

import pytest

gpd = pytest.importorskip("geopandas")
from shapely.geometry import LineString, MultiLineString  # noqa: E402

from build_drain_graph import (  # noqa: E402
    graph_component_stats,
    graph_from_lines,
    haversine_m,
)


def test_haversine_one_degree_latitude_is_about_111km():
    d = haversine_m(80.6, 16.0, 80.6, 17.0)
    assert d == pytest.approx(111_195, rel=1e-3)


def test_haversine_zero_distance():
    assert haversine_m(80.6, 16.5, 80.6, 16.5) == 0.0


def test_graph_joins_shared_vertices_and_skips_nan_tags():
    gdf = gpd.GeoDataFrame(
        {
            "waterway": ["drain", "canal"],
            "name": ["Budameru", float("nan")],
        },
        geometry=[
            LineString([(80.60, 16.50), (80.61, 16.50)]),
            MultiLineString([[(80.61, 16.50), (80.61, 16.51)]]),
        ],
        crs="EPSG:4326",
    )
    G = graph_from_lines(gdf)
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 2
    canal = G.edges[(80.61, 16.5), (80.61, 16.51)]
    assert canal["waterway"] == "canal"
    assert "name" not in canal
    assert canal["length_m"] == pytest.approx(1112, rel=1e-2)
    assert not any(
        isinstance(v, float) and math.isnan(v)
        for _, _, d in G.edges(data=True)
        for v in d.values()
    )


def test_graph_ignores_empty_geometries():
    gdf = gpd.GeoDataFrame(
        {"waterway": ["drain"]}, geometry=[LineString()], crs="EPSG:4326"
    )
    assert graph_from_lines(gdf).number_of_nodes() == 0


def test_graph_skips_self_loops_from_rounding():
    # Nearly identical vertices that round to the same 6-dp coordinate.
    gdf = gpd.GeoDataFrame(
        {"waterway": ["drain"]},
        geometry=[
            LineString(
                [
                    (80.6000001, 16.5000001),
                    (80.6000004, 16.5000002),  # collapses with first after round(6)
                    (80.6100000, 16.5000000),
                ]
            )
        ],
        crs="EPSG:4326",
    )
    G = graph_from_lines(gdf)
    assert G.number_of_nodes() == 2
    assert G.number_of_edges() == 1
    assert all(u != v for u, v in G.edges())


def test_graph_component_stats_empty():
    import networkx as nx

    assert graph_component_stats(nx.Graph()) == {
        "n_components": 0,
        "n_isolated_nodes": 0,
        "largest_component_nodes": 0,
    }


def test_graph_component_stats_two_components():
    gdf = gpd.GeoDataFrame(
        {"waterway": ["drain", "canal"]},
        geometry=[
            LineString([(80.60, 16.50), (80.61, 16.50)]),
            LineString([(80.70, 16.55), (80.71, 16.55)]),
        ],
        crs="EPSG:4326",
    )
    stats = graph_component_stats(graph_from_lines(gdf))
    assert stats["n_components"] == 2
    assert stats["largest_component_nodes"] == 2
    assert stats["n_isolated_nodes"] == 0
