"""Download / document DEM for Vijayawada–Budameru bbox.

Primary: OpenTopography Global DEM API (SRTM / Copernicus) if OPENTOPOGRAPHY_API_KEY
is set. Fallback: documented Copernicus GLO-30 / SRTM manual steps + optional
elevation package clip.

No paid API required for the manual path.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import RAW_DIR, ensure_dirs, get_bbox, load_storm_catalog

OPENTOPO_URL = "https://portal.opentopography.org/API/globaldem"

COPERNICUS_NOTES = """
Manual Copernicus DEM (GLO-30) — preferred for thesis quality
=============================================================
1. Create a free account at https://dataspace.copernicus.eu/
2. Open Copernicus Browser / DEM download, or use CDSE S3/STAC for
   Copernicus DEM GLO-30 tiles covering lon 80.56–80.70, lat 16.45–16.57
   (approx. tiles around E080N16 / similar naming depending on product).
3. Download GeoTIFF(s), place under:
     data/raw/dem/
   Suggested filename:
     copernicus_glo30_vijayawada_bbox.tif
4. Record product id / download date in dem_source.meta.json (this script
   can write a stub meta file with --document-only).

Alternative free sources
------------------------
- OpenTopography Global DEM API (SRTMGL1 / COP30) — needs free API key:
    export OPENTOPOGRAPHY_API_KEY=...
    python download_dem.py --dataset COP30
- USGS EarthExplorer / NASA Earthdata SRTM 1-arcsec
- `pip install elevation` then:
    eio clip -o data/raw/dem/srtm_bbox.tif --bounds 80.56 16.45 80.70 16.57
  (requires GDAL; may need local install on Windows)
"""


def try_opentopo(bbox: dict, dataset: str, api_key: str, out: Path) -> bool:
    params = {
        "demtype": dataset,
        "south": bbox["min_lat"],
        "north": bbox["max_lat"],
        "west": bbox["min_lon"],
        "east": bbox["max_lon"],
        "outputFormat": "GTiff",
        "API_Key": api_key,
    }
    print(f"Requesting OpenTopography {dataset} …")
    r = requests.get(OPENTOPO_URL, params=params, timeout=300, stream=True)
    if r.status_code != 200:
        print(f"OpenTopography HTTP {r.status_code}: {r.text[:500]}", file=sys.stderr)
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            if chunk:
                f.write(chunk)
    print(f"Wrote DEM → {out} ({out.stat().st_size} bytes)")
    return True


def write_meta(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download or document DEM")
    parser.add_argument(
        "--dataset",
        default="COP30",
        choices=["COP30", "SRTMGL1", "SRTMGL3", "AW3D30"],
        help="OpenTopography demtype",
    )
    parser.add_argument(
        "--document-only",
        action="store_true",
        help="Only write README + meta stub (no download)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
    )
    args = parser.parse_args()
    ensure_dirs()
    catalog = load_storm_catalog()
    bbox = get_bbox(catalog)
    dem_dir = RAW_DIR / "dem"
    readme = dem_dir / "README_DEM.md"
    readme.write_text(COPERNICUS_NOTES.strip() + "\n", encoding="utf-8")
    print(f"Wrote {readme}")

    out = args.out or (dem_dir / f"opentopo_{args.dataset.lower()}_vijayawada_bbox.tif")
    meta_path = dem_dir / "dem_source.meta.json"
    meta = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "bbox": bbox,
        "preferred": "Copernicus GLO-30 (manual CDSE)",
        "opentopo_dataset": args.dataset,
        "status": "pending",
    }

    if args.document_only:
        meta["status"] = "document_only"
        write_meta(meta_path, meta)
        print(COPERNICUS_NOTES)
        return

    api_key = os.environ.get("OPENTOPOGRAPHY_API_KEY", "").strip()
    if not api_key:
        meta["status"] = "no_api_key"
        meta["message"] = (
            "Set OPENTOPOGRAPHY_API_KEY or place a GeoTIFF manually; see README_DEM.md"
        )
        write_meta(meta_path, meta)
        print("No OPENTOPOGRAPHY_API_KEY — wrote documentation only.")
        print(COPERNICUS_NOTES)
        return

    ok = try_opentopo(bbox, args.dataset, api_key, out)
    meta["status"] = "downloaded" if ok else "download_failed"
    meta["path"] = str(out) if ok else None
    write_meta(meta_path, meta)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
