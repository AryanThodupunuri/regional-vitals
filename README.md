# RegionalVitals — BRFSS Prevalence & Trends (2010–2023)

## Overview

RegionalVitals is a collaborative, reproducible data-analysis project to summarize trends in public-health indicators from the CDC BRFSS Prevalence & Trends data (2010–2023). The team will analyze obesity prevalence, health coverage, and selected smoking indicators across five U.S. regions: Northeast, Southeast, Midwest, Southwest, and West. Analyses are descriptive and comparative only; this project does not perform causal inference or provide medical advice.

## Dataset (summary)

- Source: CDC BRFSS Prevalence & Trends Data (2010–2023). Place raw files in `data/raw/`.
- Key indicators: obesity prevalence, insurance coverage (insured/uninsured), smoking prevalence.
- Use state-year prevalence estimates; apply survey weights if microdata are used.

## Research questions

1. How has obesity prevalence changed in each region (2010–2023)?
2. How does health coverage vary across regions and time?
3. Which region experienced the largest change for each indicator?
4. Are regional trends converging or diverging?
5. How did health behaviors shift during and after the COVID period (2019–2023)?

## Approach (brief)

- Standardize and combine BRFSS files across years.
- Map states to five regions (see `data/regions.yaml`).
- Compute state and regional prevalence (population-weighted where appropriate).
- Produce trend tables and visual summaries; flag unreliable estimates.

## Current repository structure

```
README.md
data/
	raw/
	processed/
docs/
notebooks/
outputs/
regional_analysis/
	example_region_run.py   # shared runner for any region/measure
	west/                   # optional per-region notes or custom scripts (empty by default)
	midwest/
	northeast/
	southeast/
	southwest/
src/
	compute_prevalence.py
	trend_analysis.py
	region_mapping.py
	utils.py
tests/
```

## Quickstart: generate outputs for one region/measure

1) Install dependencies and ensure the combined BRFSS CSV exists:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Expect data/processed/brfss_combined_2011_2023.csv to already exist
```

2) Run the shared runner (example: West obesity):

```bash
python -m regional_analysis.example_region_run --region West --measure obesity
```

Outputs land in `outputs/tables/`:
- `{region_lower}_{measure_lower}_state_prevalence.csv`
- `{region_lower}_{measure_lower}_regional_trends.csv`

Figures land in `outputs/figures/`:
- `{region_lower}_{measure_lower}_regional_trend.png`
- `{region_lower}_{measure_lower}_state_trends.png`

Swap `--region`/`--measure` for your assignment (e.g., `--region Midwest --measure coverage`). No code edits are required to produce outputs.

## What belongs in `regional_analysis/`

- `example_region_run.py` is the single shared script everyone should reuse. It reads the combined file, filters by `--region`/`--measure`, and writes per-state prevalence plus regional trend tables.
- Subfolders like `regional_analysis/west/` are optional scratch space for region-specific notes or truly bespoke scripts if needed. Most contributions should come from the generated CSVs in `outputs/tables/`, not by duplicating the runner.

## Key outputs

- `outputs/tables/{region}_{measure}_state_prevalence.csv` — state-level prevalence for the chosen region/measure.
- `outputs/tables/{region}_{measure}_regional_trends.csv` — year-by-year regional prevalence for the chosen region/measure.
- `outputs/figures/{region}_{measure}_regional_trend.png` — regional weighted prevalence line chart.
- `outputs/figures/{region}_{measure}_state_trends.png` — per-state line chart within the region.

## Planned end deliverable (interactive)

The core artifacts are the cleaned CSV outputs above. To make results easy to explore, we can layer one lightweight interactive surface:

- **Option A (fastest):** A Jupyter/Quarto notebook that loads the generated CSVs, shows trend plots, and lets users filter by region/measure with widgets.
- **Option B (light app):** A small Streamlit app that reads the same CSVs, offers dropdowns for region/measure, displays charts and summary stats, and links to download the underlying files.

Both options reuse the existing outputs—no new pipeline work needed. If we pick Option B, we can add a short `streamlit_app.py` in `regional_analysis/` and a `requirements.txt` entry for `streamlit`. Option A can live in `notebooks/` and run entirely offline.

## Limitations

- Descriptive analysis only; avoid causal claims.
- BRFSS methodology changes and self-report bias may affect comparability.
- Some state-year estimates may be unreliable due to small samples and will be flagged.

## Contributors

1. Alhaji Bah
2. Angeline Ngo
3. Andrew Girvin
4. Inmar Chavarria-Ramirez
5. Gabriel Syed
6. Michael Huang
7. Dinah Addisalem
8. Aparna Gana
9. Samuel Fuller
10. Andrew Kohl
11. Aryan Thodupunuri
12. Walif Khan
13. Rhea Sethi
14. Vishal Sai Chindepalli

If you are a contributor, please add your role/affiliation in a `CONTRIBUTORS.md` or update this section.

## Next steps

- (Optional) Add a small batch driver to iterate all region/measure combinations.
- Add plots/notebooks that read the generated CSVs for quick visuals.
- Tighten tests for `compute_prevalence` and `trend_analysis` beyond smoke imports.
- Keep provenance notes updated in `src/preprocessing.py` as new data pulls are added.

---

For any questions or to assign tasks, open an issue or edit the `CONTRIBUTORS.md` file.
