"""Attach observed flood-extent labels to drain-graph nodes/edges.

Requires ingest_flood_extents.py output. Does NOT create SCS-CN synthetic labels.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import INTERIM_DIR, PROCESSED_DIR, ensure_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach observed flood labels to graph")
    parser.add_argument("--storm-id", default="budameru_2024_sep")
    parser.add_argument("--graph-version", default="v1")
    parser.add_argument(
        "--flood-dir",
        type=Path,
        default=None,
        help="Interim flood_extents/<storm_id> directory",
    )
    args = parser.parse_args()
    ensure_dirs()

    flood_dir = args.flood_dir or (
        INTERIM_DIR / "flood_extents" / args.storm_id
    )
    graph_dir = PROCESSED_DIR / "drain_graph" / args.graph_version
    nodes_path = graph_dir / "nodes.geojson"

    if not flood_dir.exists():
        print(
            f"No ingested flood extents at {flood_dir}.\n"
            "1) Obtain NRSC/Sentinel-1/IFI product (see ingest_flood_extents.py --checklist)\n"
            "2) python src/dataset/ingest_flood_extents.py --storm-id "
            f"{args.storm_id} --input <path>\n"
            "3) Re-run this script.\n"
            "Do NOT use SCS-CN synthetic flood maps as ground truth.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not nodes_path.exists():
        print(
            f"Graph nodes missing: {nodes_path}. Run build_drain_graph.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import geopandas as gpd
        import rasterio
        from rasterio.features import geometry_mask
        from shapely.geometry import mapping
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        sys.exit(1)

    nodes = gpd.read_file(nodes_path)
    # Prefer raster flood mask if present, else vector
    rasters = list(flood_dir.glob("*.tif")) + list(flood_dir.glob("*.tiff"))
    vectors = (
        list(flood_dir.glob("*.geojson"))
        + list(flood_dir.glob("*.gpkg"))
        + list(flood_dir.glob("*.shp"))
    )

    flooded = []
    method = None
    if rasters:
        method = "raster_sample"
        with rasterio.open(rasters[0]) as src:
            for _, row in nodes.iterrows():
                lon, lat = row.geometry.x, row.geometry.y
                try:
                    val = list(src.sample([(lon, lat)]))[0][0]
                    nodata = src.nodata
                    is_flood = val is not None and val != nodata and float(val) > 0
                except Exception:  # noqa: BLE001
                    is_flood = False
                flooded.append(bool(is_flood))
        source_file = str(rasters[0])
    elif vectors:
        method = "vector_intersects"
        flood = gpd.read_file(vectors[0]).to_crs(nodes.crs)
        union = flood.unary_union
        flooded = [bool(geom.intersects(union)) for geom in nodes.geometry]
        source_file = str(vectors[0])
    else:
        print(f"No .tif/.geojson/.gpkg/.shp in {flood_dir}", file=sys.stderr)
        sys.exit(1)

    nodes = nodes.copy()
    nodes["flooded"] = flooded
    nodes["label_source"] = "observed_flood_extent"
    nodes["storm_id"] = args.storm_id

    out_dir = PROCESSED_DIR / "labeled" / args.storm_id / args.graph_version
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "nodes_labeled.geojson"
    nodes.to_file(out_path, driver="GeoJSON")
    meta = {
        "labeled_at_utc": datetime.now(timezone.utc).isoformat(),
        "storm_id": args.storm_id,
        "graph_version": args.graph_version,
        "method": method,
        "source_file": source_file,
        "n_nodes": len(nodes),
        "n_flooded": int(sum(flooded)),
        "synthetic_scs_cn": False,
    }
    with open(out_dir / "labels.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Labeled {meta['n_flooded']}/{meta['n_nodes']} nodes flooded → {out_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
