# Dataset status (2026-10-29)

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

## Pipeline polish (2026-10-16, branch `upgrade/2026-10-16-ml-project-polish`)
- Config: `bbox_center`, `list_storm_ids`, clearer catalog / storm errors
- Rainfall: precip summary helper; uses shared bbox centre
- Graph: skip rounded self-loops; `n_components` / isolated / largest-component in `graph.meta.json`
- OSM: drop ways that still lack `waterway=*` after de-duplication
- Labels: extractable raster/vector listing + sampling helpers
- Ingest: reject unsupported --input extensions
- Offline pytest suite expanded (run `pytest` locally; no CI workflow yet)

## Pipeline safety (2026-10-29, branch `upgrade/2026-10-29-pipeline-safety`)
- Config: storm windows parsed as real dates; `validate_storm` checks every catalog entry; `require_storm` gives a clean CLI error for a bad `--storm-id`
- Rainfall: `--lat/--lon` range check + warning outside the bbox; empty Open-Meteo responses fail instead of writing a 0 mm CSV
- OSM: Overpass `runtime error` remarks (partial results on timeout) now trigger the next mirror
- DEM: atomic `.part` download, API key redacted from errors; DEM auto-pick is sorted / case-insensitive
- Graph: DEM sampled in its own CRS (projected DEMs work); NaN nodata dropped → **rebuild graph v1 if a projected DEM was used**
- Labels: warns when several flood products sit in one interim folder
- Ingest: re-ingesting a file already in interim no longer crashes

## Local checkout
```
git clone https://github.com/applejuice093/ML_project.git C:\A\PROJECT\ML_project
```
