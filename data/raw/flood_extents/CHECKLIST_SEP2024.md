Sep 2024 Budameru flood extents — manual checklist
==================================================
Goal: observed inundation for storm_id=budameru_2024_sep
      (31 Aug – 9 Sep 2024; peak ~31 Aug–2 Sep).

Option A — NRSC / Bhuvan / ISRO flood maps
  1. Search Bhuvan / NRSC flood products for Andhra Pradesh / Krishna /
     NTR district around early September 2024.
  2. Download GeoTIFF or vector inundation layer for Vijayawada–Budameru.
  3. Place file under: data/raw/flood_extents/
  4. Run ingest_flood_extents.py

Option B — Sentinel-1 (Google Earth Engine)
  1. AOI bbox [80.56,16.45]–[80.70,16.57]
  2. Date range: 2024-08-25 to 2024-09-15
  3. Export GeoTIFF; place under data/raw/flood_extents/

FORBIDDEN: Do NOT generate ground-truth from SCS-CN / synthetic runoff.
