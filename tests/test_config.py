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


def test_bbox_center_is_midpoint():
    lat, lon = config.bbox_center(config.DEFAULT_BBOX)
    assert lat == pytest.approx(16.51)
    assert lon == pytest.approx(80.63)


def test_list_storm_ids_includes_budameru():
    assert "budameru_2024_sep" in config.list_storm_ids()


def test_list_storm_ids_empty_catalog():
    assert config.list_storm_ids({"storms": []}) == []


def test_load_storm_catalog_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        config.load_storm_catalog(tmp_path / "nope.yaml")


def test_get_storm_error_lists_known_ids():
    with pytest.raises(KeyError, match="known"):
        config.get_storm("missing", {"storms": [{"id": "only_one"}]})


def test_parse_iso_date_accepts_string_and_date():
    from datetime import date

    assert config.parse_iso_date("2024-08-31") == date(2024, 8, 31)
    assert config.parse_iso_date(date(2024, 9, 1)) == date(2024, 9, 1)


@pytest.mark.parametrize("bad", [None, "", "31-08-2024", "2024-13-01", 20240831])
def test_parse_iso_date_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        config.parse_iso_date(bad, "start_date")


def test_storm_rainfall_window_prefers_rainfall_fetch():
    storm = config.get_storm("budameru_2024_sep")
    assert config.storm_rainfall_window(storm) == ("2024-08-25", "2024-09-15")


def test_storm_rainfall_window_falls_back_to_storm_dates():
    from datetime import date

    # Unquoted YAML dates arrive as datetime.date objects.
    storm = {"id": "s", "start_date": date(2024, 8, 31), "end_date": "2024-09-09"}
    assert config.storm_rainfall_window(storm) == ("2024-08-31", "2024-09-09")


def test_storm_rainfall_window_rejects_inverted_and_missing():
    with pytest.raises(ValueError, match="after it ends"):
        config.storm_rainfall_window(
            {"id": "s", "start_date": "2024-09-09", "end_date": "2024-08-31"}
        )
    with pytest.raises(ValueError, match="end_date"):
        config.storm_rainfall_window({"id": "s", "start_date": "2024-09-09"})


def test_every_catalog_storm_is_consistent():
    for storm in config.load_storm_catalog()["storms"]:
        config.validate_storm(storm)


@pytest.mark.parametrize(
    "storm, msg",
    [
        ({"start_date": "2024-08-31", "end_date": "2024-09-09"}, "no id"),
        ({"id": "s", "start_date": "2024-09-09", "end_date": "2024-08-31"}, "after"),
        (
            {
                "id": "s",
                "start_date": "2024-08-31",
                "end_date": "2024-09-09",
                "peak_window": {"start": "2024-08-30", "end": "2024-09-01"},
            },
            "outside",
        ),
    ],
)
def test_validate_storm_rejects_inconsistent_entries(storm, msg):
    with pytest.raises(ValueError, match=msg):
        config.validate_storm(storm)


def test_point_in_bbox():
    assert config.point_in_bbox(16.51, 80.63, config.DEFAULT_BBOX)
    assert config.point_in_bbox(16.45, 80.56, config.DEFAULT_BBOX)  # edge counts
    # Swapped lat/lon is the classic mistake this guards against.
    assert not config.point_in_bbox(80.63, 16.51, config.DEFAULT_BBOX)
