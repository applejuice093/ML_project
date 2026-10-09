# Dataset status (2026-09-23)

## Done
- Repo scaffold (dataset-only)
- Storm catalog: `budameru_2024_sep` (2024-08-31 → 2024-09-09)
- OSM waterways: 201 features → `data/raw/osm/waterways_vijayawada_bbox.geojson`
- Open-Meteo rainfall: 22 days, ~485.8 mm total → `data/raw/rainfall/budameru_2024_sep_openmeteo_daily.*`
- Drain graph v1 built locally: 11042 nodes / 11042 edges (regenerate with `build_drain_graph.py`; large GraphML not committed)

## Blocked / manual
- DEM GeoTIFF → `data/raw/dem/budameru_dem.tif` (see `download_dem.py`)
- Observed flood extent → `data/raw/flood_extents/` (NRSC/Sentinel-1; never SCS-CN)

## Pipeline hardening (2026-10-08, branch `upgrade/2026-10-08-dataset-hardening`)
- Edges now carry `length_m` (haversine); NaN OSM tags no longer exported → **rebuild graph v1** to pick these up
- OSM ways de-duplicated (relation recursion produced duplicate tagless copies)
- Flood rasters sampled in their own CRS; CRS-less vectors handled; shapefile sidecars copied on ingest
- Offline pytest suite (`pytest`); CI workflow not yet added

## Local checkout
```
git clone https://github.com/applejuice093/ML_project.git C:\A\PROJECT\ML_project
```
