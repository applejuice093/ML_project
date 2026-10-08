"""Tests for drain-graph construction from waterway lines."""

import math

import pytest

gpd = pytest.importorskip("geopandas")
from shapely.geometry import LineString, MultiLineString  # noqa: E402

from build_drain_graph import graph_from_lines, haversine_m  # noqa: E402


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
