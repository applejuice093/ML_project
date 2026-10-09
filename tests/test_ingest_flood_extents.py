"""Tests for flood-extent ingest helpers."""

from ingest_flood_extents import copy_with_sidecars


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
