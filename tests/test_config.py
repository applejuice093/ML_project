"""Tests for the shared dataset config helpers."""

import pytest

import config


def test_storm_catalog_loads_and_has_budameru():
    cat = config.load_storm_catalog()
    ids = [s["id"] for s in cat["storms"]]
    assert "budameru_2024_sep" in ids


def test_get_bbox_matches_catalog():
    bbox = config.get_bbox()
    assert bbox == {
        "min_lat": 16.45,
        "max_lat": 16.57,
        "min_lon": 80.56,
        "max_lon": 80.70,
    }


def test_get_bbox_falls_back_to_default():
    assert config.get_bbox({"study_area": {}}) == config.DEFAULT_BBOX


def test_get_storm_unknown_raises():
    with pytest.raises(KeyError):
        config.get_storm("does_not_exist", {"storms": []})


def test_bbox_overpass_order_is_south_west_north_east():
    assert config.bbox_overpass(config.DEFAULT_BBOX) == "16.45,80.56,16.57,80.7"


@pytest.mark.parametrize(
    "bad",
    [
        {"min_lat": 16.57, "max_lat": 16.45, "min_lon": 80.56, "max_lon": 80.70},
        {"min_lat": 16.45, "max_lat": 16.57, "min_lon": 80.70, "max_lon": 80.56},
        {"min_lat": 16.45, "max_lat": 95.0, "min_lon": 80.56, "max_lon": 80.70},
        {"min_lat": 16.45, "max_lat": 16.57, "min_lon": 80.56},
    ],
)
def test_validate_bbox_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        config.validate_bbox(bad)
