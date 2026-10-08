"""Tests for the Overpass JSON -> GeoJSON conversion (no network)."""

from fetch_osm_drains import build_query, elements_to_geojson


def _sample():
    return {
        "elements": [
            {"type": "node", "id": 1, "lon": 80.60, "lat": 16.50},
            {"type": "node", "id": 2, "lon": 80.61, "lat": 16.51},
            {"type": "node", "id": 3, "lon": 80.62, "lat": 16.52},
            {"type": "way", "id": 10, "nodes": [1, 2, 3], "tags": {"waterway": "drain"}},
            # Same way again as an untagged skeleton (relation recursion).
            {"type": "way", "id": 10, "nodes": [1, 2, 3]},
            # Way with a single resolvable node is dropped.
            {"type": "way", "id": 11, "nodes": [1, 999], "tags": {"waterway": "ditch"}},
        ]
    }


def test_build_query_contains_bbox_and_waterway_filter():
    q = build_query("16.45,80.56,16.57,80.7")
    assert '["waterway"](16.45,80.56,16.57,80.7)' in q
    assert q.startswith("[out:json]")


def test_elements_to_geojson_dedupes_ways_and_keeps_tags():
    gj = elements_to_geojson(_sample())
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == 1
    feat = gj["features"][0]
    assert feat["properties"]["osm_id"] == 10
    assert feat["properties"]["waterway"] == "drain"
    assert feat["geometry"]["coordinates"] == [[80.60, 16.50], [80.61, 16.51], [80.62, 16.52]]


def test_elements_to_geojson_empty():
    assert elements_to_geojson({})["features"] == []
