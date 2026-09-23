# Dataset guide — Vijayawada / Budameru

## Principle
**Observed inundation only.** SCS-CN / TWI may be used later as a frozen physics baseline feature, never as `y`.

## Pipeline order
1. `python src/dataset/fetch_osm_drains.py`
2. `python src/dataset/fetch_rainfall.py --storm-id budameru_2024_sep`
3. `python src/dataset/download_dem.py`
4. Drop observed flood extent → `ingest_flood_extents.py`
5. `python src/dataset/build_drain_graph.py --version v1`
6. `python src/dataset/attach_labels.py --storm-id budameru_2024_sep --graph-version v1`

Storm: **budameru_2024_sep** (2024-08-31 → 2024-09-09).

Local path: `C:\A\PROJECT\ML_project`.
