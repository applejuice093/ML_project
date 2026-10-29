"""Fetch historical daily rainfall from Open-Meteo Archive API for a storm window."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import (
    RAW_DIR,
    bbox_center,
    ensure_dirs,
    get_bbox,
    get_storm,
    load_storm_catalog,
    storm_rainfall_window,
)

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


def summarize_daily_precip(daily: dict) -> tuple[int, float]:
    """Return ``(n_days, total_precip_mm)`` from an Open-Meteo ``daily`` block."""
    times = daily.get("time") or []
    precip = daily.get("precipitation_sum") or []
    total = sum(x for x in precip if x is not None)
    return len(times), float(total)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Open-Meteo rainfall")
    parser.add_argument("--storm-id", default="budameru_2024_sep")
    parser.add_argument(
        "--lat",
        type=float,
        default=None,
        help="Override latitude (default: bbox center)",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=None,
        help="Override longitude (default: bbox center)",
    )
    args = parser.parse_args()
    ensure_dirs()
    catalog = load_storm_catalog()
    storm = get_storm(args.storm_id, catalog)
    bbox = get_bbox(catalog)
    center_lat, center_lon = bbox_center(bbox)
    lat = args.lat if args.lat is not None else center_lat
    lon = args.lon if args.lon is not None else center_lon
    try:
        start, end = storm_rainfall_window(storm)
    except ValueError as e:
        raise SystemExit(f"Invalid rainfall window: {e}") from e

    print(f"Storm {args.storm_id}: {start} → {end} @ ({lat:.4f}, {lon:.4f})")
    data = fetch_open_meteo(lat, lon, start, end)
    daily = data.get("daily") or {}
    out_csv = RAW_DIR / "rainfall" / f"{args.storm_id}_openmeteo_daily.csv"
    out_json = RAW_DIR / "rainfall" / f"{args.storm_id}_openmeteo_daily.json"
    n_days, total_mm = summarize_daily_precip(daily)
    n = write_csv(daily, out_csv)
    if n != n_days:
        # Defensive: CSV writer and summarizer should always agree on day count.
        n_days = n
    meta = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "storm_id": args.storm_id,
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "source": ARCHIVE_URL,
        "timezone": "Asia/Kolkata",
        "n_days": n_days,
        "total_precip_mm": total_mm,
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
