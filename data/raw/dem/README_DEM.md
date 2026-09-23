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
