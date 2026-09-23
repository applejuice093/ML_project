# ML_project — DrainSense (dataset phase)

Thesis work: **drain-graph GNN + physics residual** for urban/drain flooding in the **Vijayawada–Budameru** corridor (Andhra Pradesh).

This repository currently contains the **dataset-only** pipeline:

- Study bbox, storm catalog (Sep 2024 Budameru event first)
- OSM waterway fetch, Open-Meteo rainfall, DEM helpers
- Observed flood-extent ingest stubs (NRSC / Sentinel-1 / IFI)
- Drain-graph build + label attachment (no synthetic SCS-CN labels)

See **[README_DATASET.md](README_DATASET.md)** for layout, sources, and commands.

GNN training is intentionally not implemented yet.
