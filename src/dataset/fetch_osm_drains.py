"""Fetch OSM waterway / drain / canal features via Overpass for the study bbox."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import (
    RAW_DIR,
    bbox_overpass,
    ensure_dirs,
    get_bbox,
    load_storm_catalog,
)

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

HEADERS = {
    "User-Agent": "DrainSenseML/0.1 (dataset build; research; contact: local)",
    "Accept": "application/json",
}


def build_query(bbox_str: str) -> str:
    # waterway=* covers river, stream, canal, drain, ditch, etc.
    return f"""
[out:json][timeout:180];
(
  way["waterway"]({bbox_str});
  relation["waterway"]({bbox_str});
);
out body;
>;
out skel qt;
""".strip()


def overpass_fetch(query: str, timeout: int = 200) -> dict:
    import time

    last_err: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            r = requests.post(
                url,
                data={"data": query},
                headers=HEADERS,
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"Overpass failed at {url}: {e}", file=sys.stderr)
            time.sleep(5)
    raise RuntimeError(f"All Overpass endpoints failed: {last_err}")


def elements_to_geojson(data: dict) -> dict:
    """Minimal OSM JSON → GeoJSON (LineStrings for ways)."""
    nodes = {
        el["id"]: (el["lon"], el["lat"])
        for el in data.get("elements", [])
        if el.get("type") == "node" and "lon" in el and "lat" in el
    }
    features = []
    for el in data.get("elements", []):
        if el.get("type") != "way":
            continue
        coords = []
        for nid in el.get("nodes", []):
            if nid in nodes:
                coords.append(list(nodes[nid]))
        if len(coords) < 2:
            continue
        tags = el.get("tags", {}) or {}
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "osm_id": el["id"],
                    "osm_type": "way",
                    **{k: v for k, v in tags.items()},
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OSM drains/waterways")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output GeoJSON path",
    )
    args = parser.parse_args()
    ensure_dirs()
    catalog = load_storm_catalog()
    bbox = get_bbox(catalog)
    bbox_str = bbox_overpass(bbox)
    out = args.out or (RAW_DIR / "osm" / "waterways_vijayawada_bbox.geojson")

    print(f"Bbox (S,W,N,E): {bbox_str}")
    query = build_query(bbox_str)
    data = overpass_fetch(query)
    n_el = len(data.get("elements", []))
    print(f"Overpass elements: {n_el}")

    gj = elements_to_geojson(data)
    n_feat = len(gj["features"])
    meta = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "bbox": bbox,
        "overpass_element_count": n_el,
        "feature_count": n_feat,
        "query_note": "way/relation waterway=* in study bbox",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(gj, f)
    meta_path = out.with_suffix(".meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {n_feat} features → {out}")
    print(f"Meta → {meta_path}")


if __name__ == "__main__":
    # Allow running as script from src/dataset or via python -m
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
