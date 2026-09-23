"""Fetch historical daily rainfall from Open-Meteo Archive API for a storm window."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import RAW_DIR, ensure_dirs, get_bbox, get_storm, load_storm_catalog

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_open_meteo(
    lat: float,
    lon: float,
    start: str,
    end: str,
) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "precipitation_sum,rain_sum,precipitation_hours",
        "timezone": "Asia/Kolkata",
    }
    r = requests.get(ARCHIVE_URL, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def write_csv(daily: dict, path: Path) -> int:
    times = daily.get("time", [])
    precip = daily.get("precipitation_sum", [])
    rain = daily.get("rain_sum", [])
    hours = daily.get("precipitation_hours", [])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "precipitation_sum_mm", "rain_sum_mm", "precipitation_hours"])
        for i, t in enumerate(times):
            w.writerow(
                [
                    t,
                    precip[i] if i < len(precip) else None,
                    rain[i] if i < len(rain) else None,
                    hours[i] if i < len(hours) else None,
                ]
            )
    return len(times)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Open-Meteo rainfall")
    parser.add_argument("--storm-id", default="budameru_2024_sep")
    parser.add_argument("--lat", type=float, default=None)
    parser.add_argument("--lon", type=float, default=None)
    args = parser.parse_args()
    ensure_dirs()
    catalog = load_storm_catalog()
    storm = get_storm(args.storm_id, catalog)
    bbox = get_bbox(catalog)
    lat = args.lat if args.lat is not None else (bbox["min_lat"] + bbox["max_lat"]) / 2
    lon = args.lon if args.lon is not None else (bbox["min_lon"] + bbox["max_lon"]) / 2
    rf = storm.get("rainfall_fetch") or {}
    start = rf.get("start_date") or storm["start_date"]
    end = rf.get("end_date") or storm["end_date"]

    print(f"Storm {args.storm_id}: {start} → {end} @ ({lat:.4f}, {lon:.4f})")
    data = fetch_open_meteo(lat, lon, start, end)
    daily = data.get("daily") or {}
    out_csv = RAW_DIR / "rainfall" / f"{args.storm_id}_openmeteo_daily.csv"
    out_json = RAW_DIR / "rainfall" / f"{args.storm_id}_openmeteo_daily.json"
    n = write_csv(daily, out_csv)
    meta = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "storm_id": args.storm_id,
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "source": ARCHIVE_URL,
        "timezone": "Asia/Kolkata",
        "n_days": n,
        "total_precip_mm": sum(
            x for x in (daily.get("precipitation_sum") or []) if x is not None
        ),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "daily": daily}, f, indent=2)
    with open(out_csv.with_suffix(".meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {n} days → {out_csv}")
    print(f"Total precip (sum): {meta['total_precip_mm']:.1f} mm")
    print(f"JSON → {out_json}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
