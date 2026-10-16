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

## Drain graph schema (`data/processed/drain_graph/<version>/`)

| Element | Attribute | Meaning |
| --- | --- | --- |
| node | `lon`, `lat` | Vertex coordinate (EPSG:4326, rounded to 6 dp ≈ 0.1 m) |
| node | `elev_m` | DEM elevation, only when a DEM GeoTIFF is present |
| edge | `length_m` | Great-circle segment length in metres (use this one) |
| edge | `length_deg` | Euclidean length in degrees (legacy; not a physical distance) |
| edge | OSM tags | `waterway`, `name`, `osm_id`, … copied from the source way; missing tags are omitted |

Labeled nodes (`data/processed/labeled/<storm>/<version>/nodes_labeled.geojson`) add
`flooded` (bool), `label_source` (always `observed_flood_extent`) and `storm_id`.

`graph.meta.json` also records connectivity after each build:

| Field | Meaning |
| --- | --- |
| `n_components` | Connected-component count in the undirected drain graph |
| `n_isolated_nodes` | Nodes with degree 0 (should stay rare for waterway lines) |
| `largest_component_nodes` | Node count of the biggest component |

Local path: `C:\A\PROJECT\ML_project`.


## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `OSM GeoJSON missing` from `build_drain_graph.py` | Fetch not run | `python src/dataset/fetch_osm_drains.py` |
| Graph builds but `elev_m` is absent / `n_nodes_with_elev=0` | No DEM GeoTIFF or no rasterio | Place a `.tif` under `data/raw/dem/` and optionally `pip install rasterio` |
| `attach_labels.py` exits 2 | No ingested flood extents | Drop an observed product and run `ingest_flood_extents.py --input …` |
| `Unsupported input extension` on ingest | Wrong file type | Use `.tif`/`.tiff`/`.geojson`/`.gpkg`/`.shp` only |
| Overpass timeouts | Mirror busy | Script retries several mirrors; re-run later |
| Tests need network | They must not | Suite is offline; if a test hits the network, that is a bug |

## Rebuild checklist

After pulling graph/OSM fixes, regenerate locally (large GraphML is gitignored):

```bash
python src/dataset/build_drain_graph.py --version v1
# Inspect data/processed/drain_graph/v1/graph.meta.json for n_components
```
