"""Ingest observed flood extents (NRSC / Sentinel-1 / IFI) — NO synthetic SCS-CN labels.

Most NRSC / Bhuvan products require interactive download. This script accepts a
user-dropped GeoTIFF or GeoJSON/Shapefile path and normalizes it into
data/interim/ for later attach_labels.py.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import INTERIM_DIR, RAW_DIR, ensure_dirs, get_storm

CHECKLIST = """
Sep 2024 Budameru flood extents — manual checklist
==================================================
Goal: observed inundation for storm_id=budameru_2024_sep
      (31 Aug – 9 Sep 2024; peak ~31 Aug–2 Sep).

Option A — NRSC / Bhuvan / ISRO flood maps
  1. Search Bhuvan / NRSC flood products for Andhra Pradesh / Krishna /
     NTR district around early September 2024.
  2. Download GeoTIFF or vector inundation layer for Vijayawada–Budameru.
  3. Place file under: data/raw/flood_extents/
     Suggested: budameru_2024_sep_nrsc.tif  (or .geojson)
  4. Run:
       python src/dataset/ingest_flood_extents.py \\
         --storm-id budameru_2024_sep \\
         --input data/raw/flood_extents/budameru_2024_sep_nrsc.tif

Option B — Sentinel-1 flood mapping (Google Earth Engine)
  1. Open GEE Code Editor; use a Sentinel-1 GRD change-detection / Otsu
     flood script for AOI bbox [80.56,16.45]–[80.70,16.57].
  2. Date range: 2024-08-25 to 2024-09-15 (compare pre vs peak/post).
  3. Export GeoTIFF to Drive, download, place under data/raw/flood_extents/.
  4. Run ingest_flood_extents.py as above.

Option C — NASA/JRC IFI or similar observed flood products
  1. Download product covering the AOI for the storm window.
  2. Clip to study bbox; place under data/raw/flood_extents/.
  3. Ingest with this script.

FORBIDDEN
  Do NOT generate ground-truth flood labels from SCS-CN / synthetic runoff.
  Physics residual / SCS-CN may appear later as model features or physics
  terms — never as observed labels.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest observed flood extent files (manual drop)"
    )
    parser.add_argument("--storm-id", default="budameru_2024_sep")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to GeoTIFF / GeoJSON / GPKG already downloaded by user",
    )
    parser.add_argument(
        "--checklist",
        action="store_true",
        help="Print manual acquisition checklist and exit",
    )
    args = parser.parse_args()
    ensure_dirs()

    checklist_path = RAW_DIR / "flood_extents" / "CHECKLIST_SEP2024.md"
    checklist_path.write_text(CHECKLIST.strip() + "\n", encoding="utf-8")

    if args.checklist or args.input is None:
        print(CHECKLIST)
        print(f"Checklist also written → {checklist_path}")
        if args.input is None and not args.checklist:
            print(
                "\nNo --input provided. Drop a file then re-run with --input.",
                file=sys.stderr,
            )
            sys.exit(0 if args.checklist else 2)
        return

    storm = get_storm(args.storm_id)
    src = args.input
    if not src.exists():
        print(f"Input not found: {src}", file=sys.stderr)
        sys.exit(1)

    dest_dir = INTERIM_DIR / "flood_extents" / args.storm_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    meta = {
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "storm_id": args.storm_id,
        "storm_window": {
            "start": storm.get("start_date"),
            "end": storm.get("end_date"),
        },
        "source_path": str(src),
        "interim_path": str(dest),
        "label_type": "observed_flood_extent",
        "synthetic_scs_cn": False,
    }
    meta_path = dest_dir / "ingest.meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Copied → {dest}")
    print(f"Meta → {meta_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
