"""Shared config for DrainSense dataset scripts (bbox, CRS, paths)."""

from __future__ import annotations

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
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_bbox(catalog: dict[str, Any] | None = None) -> dict[str, float]:
    if catalog is None:
        catalog = load_storm_catalog()
    return dict(catalog.get("study_area", {}).get("bbox", DEFAULT_BBOX))


def get_storm(storm_id: str, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    if catalog is None:
        catalog = load_storm_catalog()
    for s in catalog.get("storms", []) or []:
        if s.get("id") == storm_id:
            return s
    raise KeyError(f"Storm not found: {storm_id}")


def bbox_overpass(bbox: dict[str, float]) -> str:
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
        INTERIM_DIR,
        PROCESSED_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    cat = load_storm_catalog()
    print("REPO_ROOT", REPO_ROOT)
    print("bbox", get_bbox(cat))
    print("storms", [s["id"] for s in cat.get("storms", [])])
