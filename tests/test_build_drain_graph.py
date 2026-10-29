"""Tests for drain-graph construction from waterway lines."""

import math

import pytest

gpd = pytest.importorskip("geopandas")
from shapely.geometry import LineString, MultiLineString  # noqa: E402

from build_drain_graph import (  # noqa: E402
    clean_elevation,
    find_default_dem,
    graph_component_stats,
    graph_from_lines,
    haversine_m,
    lonlat_to_crs,
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


def test_find_default_dem_is_sorted_and_case_insensitive(tmp_path):
    for name in ("z_dem.tif", "A_DEM.TIF", "notes.txt", "b_dem.tiff"):
        (tmp_path / name).write_bytes(b"x")
    assert find_default_dem(tmp_path).name == "A_DEM.TIF"


def test_find_default_dem_none_when_missing(tmp_path):
    assert find_default_dem(tmp_path) is None
    assert find_default_dem(tmp_path / "absent") is None


@pytest.mark.parametrize(
    "value, nodata, expected",
    [
        (12.5, None, 12.5),
        (-9999.0, -9999, None),
        (float("nan"), None, None),
        (float("nan"), float("nan"), None),
        (float("inf"), None, None),
        (None, None, None),
        ("bad", None, None),
    ],
)
def test_clean_elevation(value, nodata, expected):
    assert clean_elevation(value, nodata) == expected


def test_lonlat_to_crs_passthrough_for_wgs84_and_none():
    pts = [(80.63, 16.51)]
    assert lonlat_to_crs(pts, None) == pts
    assert lonlat_to_crs(pts, "EPSG:4326") == pts


def test_lonlat_to_crs_projects_to_utm44n():
    pytest.importorskip("pyproj")
    (x, y), = lonlat_to_crs([(80.63, 16.51)], "EPSG:32644")
    # Vijayawada is ~40 km west of the UTM 44N central meridian (81°E),
    # whose false easting is 500 km.
    assert 440_000 < x < 480_000
    assert 1_800_000 < y < 1_850_000
