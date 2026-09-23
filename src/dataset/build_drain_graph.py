"""Build a versioned drain/canal graph from OSM waterways (+ optional DEM attributes).

Phase 1: topology from OSM GeoJSON; node elevation from DEM when available.
Outputs GraphML + node/edge GeoJSON under data/interim/ and data/processed/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from config import INTERIM_DIR, PROCESSED_DIR, RAW_DIR, ensure_dirs

try:
    import geopandas as gpd
    from shapely.geometry import LineString, Point
except ImportError:  # pragma: no cover
    gpd = None  # type: ignore


def load_waterways(path: Path):
    if gpd is None:
        raise SystemExit("geopandas required: pip install -r requirements-dataset.txt")
    return gpd.read_file(path)


def graph_from_lines(gdf) -> nx.Graph:
    G = nx.Graph()
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        lines = [geom] if geom.geom_type == "LineString" else list(geom.geoms)
        props = {k: row[k] for k in gdf.columns if k != "geometry"}
        # JSON-serialize non-primitive props for GraphML later
        clean = {}
        for k, v in props.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            else:
                clean[k] = str(v)
        for line in lines:
            if not isinstance(line, LineString) or len(line.coords) < 2:
                continue
            coords = list(line.coords)
            for i in range(len(coords) - 1):
                u = (round(coords[i][0], 6), round(coords[i][1], 6))
                v = (round(coords[i + 1][0], 6), round(coords[i + 1][1], 6))
                if u not in G:
                    G.add_node(u, lon=u[0], lat=u[1])
                if v not in G:
                    G.add_node(v, lon=v[0], lat=v[1])
                length_deg = (
                    (u[0] - v[0]) ** 2 + (u[1] - v[1]) ** 2
                ) ** 0.5
                if G.has_edge(u, v):
                    continue
                G.add_edge(u, v, length_deg=length_deg, **clean)
    return G


def attach_dem_elevations(G: nx.Graph, dem_path: Path | None) -> int:
    """Sample DEM at nodes if rasterio + DEM exist. Returns count of nodes with z."""
    if dem_path is None or not dem_path.exists():
        return 0
    try:
        import rasterio
        from rasterio.sample import sample_gen
    except ImportError:
        print("rasterio not installed; skipping DEM elevations", file=sys.stderr)
        return 0
    n = 0
    with rasterio.open(dem_path) as src:
        coords = [(G.nodes[nid]["lon"], G.nodes[nid]["lat"]) for nid in G.nodes]
        for nid, val in zip(G.nodes, sample_gen(src, coords)):
            z = None
            if val is not None and len(val):
                z = float(val[0])
                if src.nodata is not None and z == src.nodata:
                    z = None
            if z is not None:
                G.nodes[nid]["elev_m"] = z
                n += 1
    return n


def export_geojson(G: nx.Graph, nodes_path: Path, edges_path: Path) -> None:
    node_features = []
    for nid, data in G.nodes(data=True):
        node_features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [data["lon"], data["lat"]],
                },
                "properties": {
                    k: v for k, v in data.items() if k not in ("lon", "lat")
                },
            }
        )
    edge_features = []
    for u, v, data in G.edges(data=True):
        edge_features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [G.nodes[u]["lon"], G.nodes[u]["lat"]],
                        [G.nodes[v]["lon"], G.nodes[v]["lat"]],
                    ],
                },
                "properties": dict(data),
            }
        )
    nodes_path.parent.mkdir(parents=True, exist_ok=True)
    with open(nodes_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": node_features}, f)
    with open(edges_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": edge_features}, f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build drain graph from OSM")
    parser.add_argument(
        "--osm",
        type=Path,
        default=RAW_DIR / "osm" / "waterways_vijayawada_bbox.geojson",
    )
    parser.add_argument(
        "--dem",
        type=Path,
        default=None,
        help="Optional DEM GeoTIFF for node elevations",
    )
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    ensure_dirs()

    if not args.osm.exists():
        print(f"OSM GeoJSON missing: {args.osm}. Run fetch_osm_drains.py first.", file=sys.stderr)
        sys.exit(1)

    gdf = load_waterways(args.osm)
    print(f"Loaded {len(gdf)} waterway features from {args.osm}")
    G = graph_from_lines(gdf)
    dem_path = args.dem
    if dem_path is None:
        # pick first tif in raw/dem if present
        cands = list((RAW_DIR / "dem").glob("*.tif")) + list(
            (RAW_DIR / "dem").glob("*.tiff")
        )
        dem_path = cands[0] if cands else None
    n_z = attach_dem_elevations(G, dem_path)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges; elev={n_z}")

    out_dir = PROCESSED_DIR / "drain_graph" / args.version
    out_dir.mkdir(parents=True, exist_ok=True)
    graphml = out_dir / "drain_graph.graphml"
    # GraphML needs string node ids
    H = nx.convert_node_labels_to_integers(G, label_attribute="coord")
    for _, d in H.nodes(data=True):
        if "coord" in d:
            d["coord"] = str(d["coord"])
    nx.write_graphml(H, graphml)
    export_geojson(
        G,
        out_dir / "nodes.geojson",
        out_dir / "edges.geojson",
    )
    meta = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": args.version,
        "osm_source": str(args.osm),
        "dem_source": str(dem_path) if dem_path else None,
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "n_nodes_with_elev": n_z,
        "n_osm_features": len(gdf),
    }
    with open(out_dir / "graph.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    # also copy meta to interim
    interim = INTERIM_DIR / "drain_graph" / args.version
    interim.mkdir(parents=True, exist_ok=True)
    with open(interim / "graph.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {graphml}")
    print(f"Meta → {out_dir / 'graph.meta.json'}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
