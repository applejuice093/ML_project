"""Tests for flood-extent ingest helpers."""

from pathlib import Path

from ingest_flood_extents import copy_with_sidecars, is_allowed_flood_input


def test_copy_with_sidecars_copies_shapefile_parts(tmp_path):
    src_dir = tmp_path / "raw"
    dest = tmp_path / "interim"
    src_dir.mkdir()
    dest.mkdir()
    for ext in (".shp", ".shx", ".dbf", ".prj"):
        (src_dir / f"flood{ext}").write_bytes(b"x")
    (src_dir / "unrelated.txt").write_text("nope")

    copied = copy_with_sidecars(src_dir / "flood.shp", dest)

    assert copied[0].name == "flood.shp"
    assert sorted(p.name for p in dest.iterdir()) == [
        "flood.dbf",
        "flood.prj",
        "flood.shp",
        "flood.shx",
    ]


def test_copy_with_sidecars_single_file_for_geotiff(tmp_path):
    src = tmp_path / "flood.tif"
    src.write_bytes(b"x")
    (tmp_path / "flood.dbf").write_bytes(b"x")  # ignored for non-.shp inputs
    dest = tmp_path / "out"
    dest.mkdir()
    copied = copy_with_sidecars(src, dest)
    assert [p.name for p in copied] == ["flood.tif"]


def test_is_allowed_flood_input_extensions():
    assert is_allowed_flood_input(Path("flood.tif"))
    assert is_allowed_flood_input(Path("flood.TIFF"))
    assert is_allowed_flood_input(Path("flood.geojson"))
    assert is_allowed_flood_input(Path("flood.shp"))
    assert not is_allowed_flood_input(Path("flood.csv"))
    assert not is_allowed_flood_input(Path("notes.md"))


def test_copy_with_sidecars_is_noop_for_file_already_in_dest(tmp_path):
    dest = tmp_path / "interim"
    dest.mkdir()
    for ext in (".shp", ".dbf"):
        (dest / f"flood{ext}").write_bytes(b"x")
    copied = copy_with_sidecars(dest / "flood.shp", dest)
    assert [p.name for p in copied] == ["flood.shp", "flood.dbf"]
    assert (dest / "flood.shp").read_bytes() == b"x"
