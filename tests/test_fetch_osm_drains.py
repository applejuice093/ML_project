"""Tests for the Overpass JSON -> GeoJSON conversion (no network)."""

import pytest

import fetch_osm_drains
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


def test_elements_to_geojson_drops_ways_without_waterway_tag():
    data = {
        "elements": [
            {"type": "node", "id": 1, "lon": 80.60, "lat": 16.50},
            {"type": "node", "id": 2, "lon": 80.61, "lat": 16.51},
            # Only a skeleton copy — no tags at all.
            {"type": "way", "id": 20, "nodes": [1, 2]},
            # Tagged non-waterway attribute should still be dropped.
            {"type": "way", "id": 21, "nodes": [1, 2], "tags": {"highway": "path"}},
        ]
    }
    assert elements_to_geojson(data)["features"] == []


class _FakeResponse:
    def __init__(self, payload, status_ok=True):
        self._payload = payload
        self._ok = status_ok

    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("HTTP 429")

    def json(self):
        return self._payload


def test_overpass_runtime_error_detects_partial_results():
    assert fetch_osm_drains.overpass_runtime_error({"elements": []}) is None
    assert fetch_osm_drains.overpass_runtime_error({"remark": "note"}) is None
    remark = "runtime error: Query timed out in \"query\" at line 3 after 181 seconds."
    assert fetch_osm_drains.overpass_runtime_error({"remark": remark}) == remark


def test_overpass_fetch_falls_through_failed_and_partial_mirrors(monkeypatch):
    responses = iter(
        [
            _FakeResponse({}, status_ok=False),  # HTTP error
            _FakeResponse({"elements": [1], "remark": "runtime error: out of memory"}),
            _FakeResponse({"elements": [1, 2, 3]}),
        ]
    )
    urls = []

    def fake_post(url, data, headers, timeout):
        urls.append(url)
        return next(responses)

    monkeypatch.setattr(fetch_osm_drains.requests, "post", fake_post)
    out = fetch_osm_drains.overpass_fetch("q", retry_delay_s=0)
    assert out == {"elements": [1, 2, 3]}
    assert urls == fetch_osm_drains.OVERPASS_URLS[:3]


def test_overpass_fetch_raises_when_every_mirror_fails(monkeypatch):
    monkeypatch.setattr(
        fetch_osm_drains.requests,
        "post",
        lambda *a, **k: _FakeResponse({}, status_ok=False),
    )
    with pytest.raises(RuntimeError, match="All Overpass endpoints failed"):
        fetch_osm_drains.overpass_fetch("q", retry_delay_s=0)
