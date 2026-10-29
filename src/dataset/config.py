"""Shared config for DrainSense dataset scripts (bbox, CRS, paths)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
STORMS_PATH = DATA_DIR / "storms" / "storm_catalog.yaml"

DEFAULT_BBOX = {
    "min_lat": 16.45,
    "max_lat": 16.57,
    "min_lon": 80.56,
    "max_lon": 80.70,
}

CRS_GEOGRAPHIC = "EPSG:4326"
CRS_PROJECTED = "EPSG:32644"


def load_storm_catalog(path: Path | None = None) -> dict[str, Any]:
    p = path or STORMS_PATH
    if not p.is_file():
        raise FileNotFoundError(f"storm catalog not found: {p}")
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"storm catalog must be a mapping, got {type(data).__name__}")
    return data


BBOX_KEYS = ("min_lat", "max_lat", "min_lon", "max_lon")


def validate_bbox(bbox: dict[str, Any]) -> dict[str, float]:
    """Return a float-typed copy of ``bbox`` or raise ValueError if malformed."""
    missing = [k for k in BBOX_KEYS if k not in bbox]
    if missing:
        raise ValueError(f"bbox missing keys: {missing}")
    out = {k: float(bbox[k]) for k in BBOX_KEYS}
    if not (-90 <= out["min_lat"] < out["max_lat"] <= 90):
        raise ValueError(f"invalid latitude range: {out['min_lat']}..{out['max_lat']}")
    if not (-180 <= out["min_lon"] < out["max_lon"] <= 180):
        raise ValueError(f"invalid longitude range: {out['min_lon']}..{out['max_lon']}")
    return out


def get_bbox(catalog: dict[str, Any] | None = None) -> dict[str, float]:
    """Study-area bbox from the storm catalog (falls back to DEFAULT_BBOX)."""
    if catalog is None:
        catalog = load_storm_catalog()
    return validate_bbox(catalog.get("study_area", {}).get("bbox", DEFAULT_BBOX))


def bbox_center(bbox: dict[str, float]) -> tuple[float, float]:
    """Return ``(lat, lon)`` at the centre of a validated bbox."""
    b = validate_bbox(bbox)
    lat = (b["min_lat"] + b["max_lat"]) / 2.0
    lon = (b["min_lon"] + b["max_lon"]) / 2.0
    return lat, lon


def list_storm_ids(catalog: dict[str, Any] | None = None) -> list[str]:
    """Return storm ids from the catalog (empty list if none)."""
    if catalog is None:
        catalog = load_storm_catalog()
    return [s["id"] for s in (catalog.get("storms") or []) if s.get("id")]


def get_storm(storm_id: str, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    if catalog is None:
        catalog = load_storm_catalog()
    for s in catalog.get("storms", []) or []:
        if s.get("id") == storm_id:
            return s
    known = list_storm_ids(catalog)
    raise KeyError(f"Storm not found: {storm_id!r} (known: {known})")


def parse_iso_date(value: Any, field: str = "date") -> date:
    """Parse ``YYYY-MM-DD`` (string or YAML-native date) into a ``date``.

    Unquoted dates in YAML load as ``datetime.date`` while quoted ones load as
    strings, so both are accepted. Raises ValueError with the field name.
    """
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a YYYY-MM-DD date, got {value!r}")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as e:
        raise ValueError(f"{field} must be a YYYY-MM-DD date, got {value!r}") from e


def storm_rainfall_window(storm: dict[str, Any]) -> tuple[str, str]:
    """Return the ``(start, end)`` ISO dates to fetch rainfall for ``storm``.

    Uses ``rainfall_fetch`` when present, else the storm window itself, and
    rejects missing, malformed or inverted dates.
    """
    rf = storm.get("rainfall_fetch") or {}
    sid = storm.get("id", "?")
    start = parse_iso_date(
        rf.get("start_date") or storm.get("start_date"), f"{sid} start_date"
    )
    end = parse_iso_date(rf.get("end_date") or storm.get("end_date"), f"{sid} end_date")
    if start > end:
        raise ValueError(f"{sid}: rainfall window starts after it ends ({start} > {end})")
    return start.isoformat(), end.isoformat()


def validate_storm(storm: dict[str, Any]) -> None:
    """Raise ValueError if a catalog storm entry is inconsistent.

    Checks that it has an id, that ``start_date <= end_date``, that the
    optional ``peak_window`` lies inside the storm window, and that the
    rainfall fetch window is valid.
    """
    sid = storm.get("id")
    if not sid:
        raise ValueError(f"storm entry has no id: {storm!r}")
    start = parse_iso_date(storm.get("start_date"), f"{sid} start_date")
    end = parse_iso_date(storm.get("end_date"), f"{sid} end_date")
    if start > end:
        raise ValueError(f"{sid}: start_date {start} is after end_date {end}")
    peak = storm.get("peak_window")
    if peak:
        p_start = parse_iso_date(peak.get("start"), f"{sid} peak_window.start")
        p_end = parse_iso_date(peak.get("end"), f"{sid} peak_window.end")
        if not (start <= p_start <= p_end <= end):
            raise ValueError(
                f"{sid}: peak_window {p_start}..{p_end} is outside {start}..{end}"
            )
    storm_rainfall_window(storm)


def bbox_overpass(bbox: dict[str, float]) -> str:
    """Format a bbox as Overpass expects: ``south,west,north,east``."""
    return (
        f"{bbox['min_lat']},{bbox['min_lon']},"
        f"{bbox['max_lat']},{bbox['max_lon']}"
    )


def ensure_dirs() -> None:
    for d in (
        RAW_DIR / "dem",
        RAW_DIR / "osm",
        RAW_DIR / "rainfall",
        RAW_DIR / "flood_extents",
        INTERIM_DIR / "flood_extents",
        INTERIM_DIR / "drain_graph",
        PROCESSED_DIR / "drain_graph",
        PROCESSED_DIR / "labeled",
    ):
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    cat = load_storm_catalog()
    print("REPO_ROOT", REPO_ROOT)
    print("bbox", get_bbox(cat))
    print("storms", list_storm_ids(cat))
