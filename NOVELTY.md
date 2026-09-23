# Novelty statement — DrainSense (honest, dataset-gated)

**Status:** research positioning for the dataset rebuild in this repo.  
**Rule:** claim only what (a) is not already established in the literature below, and (b) can be supported with **publicly obtainable** data for Vijayawada–Budameru.  
**Not claimed yet:** any trained model metrics. Novelty below is the *intended scientific contribution* after the data gate is green.

Last reviewed: 2026-09-23.

---

## 1. One-sentence contribution (use this wording)

We propose a **physics-residual graph learning** setup for urban inundation along an **open-drain / canal graph** built from **OSM + open DEM**, trained on **observed satellite inundation** for the **Vijayawada–Budameru** corridor, evaluated with **leave-one-storm-out** and **siltation / capacity counterfactuals**—not a new general flood-GNN architecture, and not a SWMM surrogate.

---

## 2. What is already published (do not claim these)

| Claim that sounds novel but is **not** | Prior work | Why it kills the claim |
|---|---|---|
| “First GNN for urban drainage” | Garzón et al., *Water Research* 2024; Zhang et al., *Water Research* 2024 (arXiv:2404.10324) | GNN surrogates of SWMM nodal depths / hydraulics already exist |
| “First physics-guided residual drainage ML” | Palmitessa et al., *Water Research* 223:118972 (2022) | Residual nets with physics constraints for UDS hydraulics |
| “First physics-informed flood GNN” | SWE–GNN (Bentivoglio et al., *HESS* 2023); HydroGraphNet (Taghizadeh et al., *CACIE* 2025, DOI 10.1111/mice.13484) | Mesh / SWE-style flood GNNs with mass constraints |
| “First Vijayawada flood AI / alert system” | AP RTGS + APSDMA + IITGN **City Flood Alert** (public reporting, 2025–26) | Operational ward-level flood forecasting already exists for Vijayawada |
| “First Budameru inundation model” | NRSC hydrodynamic Budameru flash-flood simulation (APSAC PDF, Sep 2024) | Physics model + satellite agreement (~90%) already documented |
| “First OSM→drainage network workflow” | SWMManywhere (JOSS / EarthArXiv) | Global synthetic UDM from OSM + DEM already published |

**Wording to avoid in abstracts / slides**

- “Novel GNN architecture for floods”
- “Physics-informed” if physics is only an input feature (prefer **physics-residual** / **physics-guided residual**)
- “Causal proof that desilting reduces flood risk” (prefer **counterfactual sensitivity**)
- “First ML flood model for Vijayawada”

---

## 3. What we actually own (honest intersection)

The contribution is the **combination**, for an **Indian open-drain / canal city** where a complete municipal SWMM pipe inventory is not available:

1. **Graph inductive bias over OSM waterways + open DEM** (Budameru, canals, Krishna reach in bbox), not a free-form grid alone.  
2. **Frozen conceptual physics** \(f_{\mathrm{phys}}\) (SCS-CN runoff + topographic wetness / DEM proxies) used **only as a baseline**, never as the training label \(y\).  
3. **Supervision from observed inundation** (NRSC/APSAC products and/or Sentinel-1-derived extents)—not synthetic SCS-CN labels, not SWMM depth fields.  
4. **Leave-one-storm-out (LOSO)** evaluation across distinct monsoon events (Phase-1 storm: Sep 2024 Budameru).  
5. **Siltation / capacity interventions** as counterfactual sensitivity on edge attributes \(\sigma\), compared against physics-only, graph-MLP, and grid XGBoost ablations.  
6. Grid XGBoost kept **only as an ablation**, not as the scientific headline.

That wedge is still publishable *if* the data gate below is satisfied. It is **weaker** than claiming a new architecture, and that is intentional.

---

## 4. Dataset availability (non-negotiable)

Novelty claims are invalid until these layers exist locally. Sources below are **public or free-with-account**; we do **not** depend on proprietary CARTO 2.5 m DEM used in NRSC’s hydrodynamic PDF, nor on unpublished RTGS model internals.

### 4.1 Layers that are available now (this repo / scripts)

| Layer | Source | License / access | Status in `applejuice093/ML_project` |
|---|---|---|---|
| Study bbox + storm catalog | Project-defined | — | `data/storms/storm_catalog.yaml` (`budameru_2024_sep`) |
| Drain / canal polylines | OpenStreetMap via Overpass (`waterway=*`) | ODbL | Fetch script + local GeoJSON; regenerate after clone |
| Daily rainfall | Open-Meteo Archive API | Free, no key | CSV/JSON committed for Sep 2024 window (~486 mm over fetch days) |
| Drain graph builder | This repo | — | `src/dataset/build_drain_graph.py` (GraphML gitignored; rebuild locally) |

### 4.2 Layers that are publicly obtainable but not yet in-repo

| Layer | Source | How to obtain | Notes |
|---|---|---|---|
| DEM | **Copernicus GLO-30** via OpenTopography COP30 or CDSE | Free account / API key; see `data/raw/dem/README_DEM.md` and `download_dem.py` | 30 m DSM (not bare-earth). **Do not** claim CARTO 2.5 m accuracy. |
| Observed flood extents (labels) | **NRSC / APSAC Sep 2024 inundation maps** for NTR / Vijayawada; optional **Sentinel-1** own processing | APSAC catalogue: https://apsac.ap.gov.in/?page_id=7156 and https://apsac.ap.gov.in/?page_id=7308 ; Sentinel-1 via Copernicus / Google Earth Engine | Maps exist for **1, 3, 5, 6 Sep 2024** (Sentinel-1A / TerraSAR-X products cited by APSAC). Many products are **PDF maps**—vectorize or re-derive from SAR. Urban inundation under dense canopy is hard; document uncertainty. |
| Extra storms (≥2) for LOSO | Same stack for other monsoon windows | Open-Meteo + OSM (static) + new SAR/NRSC extents | **LOSO novelty requires ≥3 labeled storms.** One storm supports dataset paper / pilot only. |

### 4.3 Useful open references (methods / transfer, not Budameru labels)

| Resource | Use |
|---|---|
| Sen1Floods11 (Cloud to Street / UN-SPIDER) | Benchmark methods for Sentinel-1 flood segmentation; **not** a substitute for Vijayawada labels |
| NRSC Budameru modelling PDF | Context and independent physics baseline; cite, do not re-upload as our labels without source attribution |

### 4.4 Explicitly unavailable / out of scope for this novelty claim

- Full municipal **SWMM** inventory for Vijayawada (not open).  
- **CARTODEM 2.5 m** used in NRSC’s published Budameru hydrodynamic run (not our training DEM).  
- RTGS **City Flood Alert** internal features, ward polygons, or 30-year proprietary training set.  
- Synthetic SCS-CN / TWI maps as \(y\) (forbidden; circular with \(f_{\mathrm{phys}}\)).

---

## 5. Data gate before any “novelty results” sentence

Do **not** write “we achieve …” until all are checked:

- [ ] Real DEM derivatives on graph nodes (elevation, slope, flow accumulation / TWI)—no random elevations.  
- [ ] Versioned OSM–DEM drain graph for the VJA bbox (`build_drain_graph.py --version v1`).  
- [ ] \(f_{\mathrm{phys}}\) computed and stored as a **feature / baseline**, never as `flood_label`.  
- [ ] ≥1 **observed** inundation extent attached as node labels (`attach_labels.py`).  
- [ ] Target ≥3 storms with extents for leave-one-storm-out.  
- [ ] Reported metrics under LOSO: CSI, POD, FAR, Brier (and flooded-area error if applicable).  
- [ ] One siltation counterfactual figure (\(\Delta\) flooded area vs \(\sigma\)).  
- [ ] No inflated AUC≈1.0 from synthetic-label leakage in any paper draft.

---

## 6. Positioning vs local operational systems

| System | Relation to this work |
|---|---|
| AP **City Flood Alert** (RTGS / APSDMA / IITGN) | Operational early warning for Vijayawada. We are a **research prototype** on open data; we do not claim to replace or exceed it without a fair, documented comparison on shared observed extents. |
| **NRSC** Budameru hydro + hydrodynamic inundation | High-fidelity physics + satellite check for Sep 2024. We cite it as context; our ML path is residual correction of a **cheap** conceptual \(f_{\mathrm{phys}}\) on an OSM graph toward observed extents when SWMM is unavailable. |

---

## 7. Suggested paper framing (short paragraph)

> DrainSense targets short-horizon inundation risk along open drains and canals in the Vijayawada–Budameru corridor. Prior GNN work either metamodels complete SWMM networks (Garzón; Zhang) or solves mesh-based shallow-water surrogates (SWE–GNN; HydroGraphNet). Indian cities often lack open pipe inventories; operational systems such as Andhra Pradesh’s City Flood Alert are closed. We therefore construct a publicly reproducible OSM–DEM drain graph, freeze a conceptual SCS-CN/TWI baseline as \(f_{\mathrm{phys}}\), and train a graph residual toward **observed** NRSC/Sentinel-1 inundation, judging skill with leave-one-storm-out and siltation counterfactuals. The contribution is a data-realistic residual-graph formulation for open-drain cities—not a claim of inventing flood GNNs.

---

## 8. Key citations (verify before camera-ready)

1. Garzón A. et al. (2024). Graph neural network-based surrogate modelling for real-time hydraulic prediction of urban drainage networks. *Water Research* 266:122396. https://doi.org/10.1016/j.watres.2024.122396  
2. Zhang et al. (2024). Related GNN urban-drainage surrogate (*Water Research* / arXiv:2404.10324).  
3. Palmitessa R. et al. (2022). Accelerating hydrodynamic simulations of urban drainage systems with physics-guided machine learning. *Water Research* 223:118972. https://doi.org/10.1016/j.watres.2022.118972  
4. Bentivoglio R. et al. (2023). Rapid spatio-temporal flood modelling via hydraulics-based graph neural networks (SWE–GNN). *HESS* 27:4227–4246. https://doi.org/10.5194/hess-27-4227-2023  
5. Taghizadeh M. et al. (2025). Interpretable physics-informed graph neural networks for flood forecasting (HydroGraphNet). *Computer-Aided Civil and Infrastructure Engineering*. https://doi.org/10.1111/mice.13484  
6. SWMManywhere — synthetic urban drainage from OSM + DEM (JOSS / EarthArXiv).  
7. NRSC (2024). Hydrological & Hydrodynamic Modelling: The Budameru River Flash Floods Simulation. APSAC-hosted PDF.  
8. APSAC / NRSC Sep 2024 inundation map catalogue. https://apsac.ap.gov.in/?page_id=7156  
9. Public reporting on AP RTGS City Flood Alert for Vijayawada (The Hindu Business Line and related coverage).

---

## 9. Honest novelty score (self-assessment)

| Aspect | Score (1–10) | Comment |
|---|---|---|
| Architectural novelty | **3** | GraphSAGE/GAT residual is standard; do not sell architecture |
| Problem + data formulation | **7** | Open-drain OSM graph + observed labels + cheap \(f_{\mathrm{phys}}\) residual + LOSO + siltation CF is a real, defensible wedge *if* multi-storm labels land |
| Local impact / case study | **6–8** | Budameru Sep 2024 is scientifically and socially relevant; NRSC already modelled it physically |
| Reproducibility | **8** (target) | All layers above are public or free-with-account |
| Overall scientific novelty (after data gate) | **~6.5–7.5** | Strong enough for a solid methods + case paper; not a “10/10 first-ever GNN” story |

If SCS-CN labels leak into \(y\), or only one storm exists, the honest score drops to **≤4**.

---

## 10. Next concrete steps (dataset, not marketing)

1. Download Copernicus GLO-30 for the project bbox → `data/raw/dem/`.  
2. Acquire or digitize **observed** Sep 2024 extent (APSAC/NRSC or Sentinel-1) → `data/raw/flood_extents/`.  
3. Run `attach_labels.py` for `budameru_2024_sep`.  
4. Add ≥2 more labeled storms before any LOSO novelty claim.  
5. Only then implement \(f_{\mathrm{phys}}\) + residual GNN and ablations.

See also: `README_DATASET.md`, `STATUS.md`, `docs/DATASET.md`.
