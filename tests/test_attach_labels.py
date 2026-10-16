"""Tests for flood-label discovery helpers (no rasterio required)."""

from pathlib import Path

from attach_labels import list_flood_rasters, list_flood_vectors


def test_list_flood_rasters_finds_tif_and_tiff(tmp_path: Path):
    (tmp_path / "a.tif").write_bytes(b"x")
    (tmp_path / "b.tiff").write_bytes(b"x")
    (tmp_path / "skip.txt").write_text("nope")
    names = [p.name for p in list_flood_rasters(tmp_path)]
    assert names == ["a.tif", "b.tiff"]


def test_list_flood_vectors_finds_geojson_gpkg_shp(tmp_path: Path):
    for name in ("flood.geojson", "flood.gpkg", "flood.shp", "noise.csv"):
        (tmp_path / name).write_bytes(b"x")
    names = [p.name for p in list_flood_vectors(tmp_path)]
    assert names == ["flood.geojson", "flood.gpkg", "flood.shp"]


def test_list_helpers_empty_dir(tmp_path: Path):
    assert list_flood_rasters(tmp_path) == []
    assert list_flood_vectors(tmp_path) == []
