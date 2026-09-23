# DrainSense — Dataset pipeline (Phase 1)

**Scope:** dataset assembly only (no GNN training).  
**Study area:** Vijayawada–Budameru, Andhra Pradesh  
**Bbox:** lat 16.45–16.57, lon 80.56–80.70 (EPSG:4326)  
**Projected CRS:** EPSG:32644 (UTM 44N)

Ground-truth flood labels must be **observed extents** (NRSC / Sentinel-1 / IFI).  
**Do not** use SCS-CN or other synthetic runoff maps as labels.

## Layout

```
data/
  raw/
    dem/              # Copernicus/SRTM GeoTIFF (often gitignored)
    osm/              # waterways GeoJSON from Overpass
    rainfall/         # Open-Meteo daily CSV/JSON
    flood_extents/    # user-dropped NRSC/S1 products + checklist
  interim/            # normalized intermediates
  processed/          # versioned drain graph + labeled nodes
  storms/
    storm_catalog.yaml
src/dataset/
  config.py
  download_dem.py
  fetch_osm_drains.py
  fetch_rainfall.py
  ingest_flood_extents.py
  build_drain_graph.py
  attach_labels.py
```

## Phase 1 order

1. **Storm window** — `budameru_2024_sep` (2024-08-31 → 2024-09-09; rainfall fetch 2024-08-25 → 2024-09-15). See `data/storms/storm_catalog.yaml`.
2. **OSM drain/canal graph** — Overpass `waterway=*`.
3. **DEM** — Copernicus GLO-30 preferred; OpenTopography if API key set.
4. **Rainfall** — Open-Meteo Archive (free, no key).
5. **Flood extents** — manual NRSC / GEE Sentinel-1 / IFI drop-in.
6. **Build graph** → **attach labels** (observed only).

## Setup

```bash
cd ML_project
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements-dataset.txt
```

## Commands

```bash
python src/dataset/fetch_osm_drains.py
python src/dataset/fetch_rainfall.py --storm-id budameru_2024_sep
python src/dataset/download_dem.py
python src/dataset/ingest_flood_extents.py --checklist
python src/dataset/ingest_flood_extents.py --storm-id budameru_2024_sep --input data/raw/flood_extents/YOUR_FILE.tif
python src/dataset/build_drain_graph.py --version v1
python src/dataset/attach_labels.py --storm-id budameru_2024_sep --graph-version v1
```

## Clone onto Windows

```powershell
cd C:\A\PROJECT
git clone https://github.com/applejuice093/ML_project.git ML_project
cd ML_project
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dataset.txt
```
