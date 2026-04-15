# RegionalVitals

A Python package that analyzes CDC BRFSS health data (2011–2023) across five U.S. regions. We look at obesity, health-care coverage, and smoking prevalence trends at both the state and regional level.

---

## Main Deliverables

Here's where the main deliverables live and what each one does:

### 1. Cross-Measure Comparison (`src/cross_measure.py`)
This is the core analysis piece. It compares obesity vs. coverage vs. smoking trends **within** a single region. You can see how the three health indicators move together (or diverge) over time, check correlations between them at the state level, and rank which measure changed the most over a given period. The functions here are:
- `compare_measures_over_time()` — weighted prevalence for each measure per year in a region
- `compute_measure_correlations()` — pairwise correlation matrix between the three measures
- `rank_measure_changes()` — ranks measures by how much they changed between two years
- `generate_cross_measure_summary()` — pulls everything into one summary dict
- `compare_all_regions_cross_measure()` — pivot table comparing all regions side by side for a given year

To generate the cross-measure outputs:
```bash
python -m scripts.cross_measure_run --all-regions
```
This writes CSV tables to `outputs/tables/` and PNG figures to `outputs/figures/`.

### 2. Interactive Explorer (`scripts/explore.py`)
Instead of static notebooks, we built a CLI-based explorer that generates interactive Plotly charts (HTML files you can open in a browser: hover, zoom, filter, etc.). You can also get static PNGs if you prefer. It lets you drill down by region, measure, or specific states.

To generate all the interactive charts:
 
# RegionalVitals — quick snapshot

For Dr. Brown (short, top-level — what I want you to look at first):

- Cross-measure comparison: `src/cross_measure.py` + runner `scripts/cross_measure_run.py` — compares obesity vs coverage vs smoking within a region, reports correlations and ranked changes, and produces CSV + PNG summaries (written locally to `outputs/`).
- Interactive explorer (no notebooks): `python -m scripts.explore` generates interactive Plotly HTML charts in `outputs/explore/` so you can quickly filter by region, measure, and state.
- Core trend logic: `src/trend_analysis.py` — linear slopes, rolling averages, convergence metrics, and the COVID-period comparison.
- Tests: `pytest tests/ -v` — covers cross-measure and trend utilities; I ran the test suite and it passes.

If you open just two things, look at:
1. `outputs/explore/<region>_cross_measure.html` (or `outputs/explore/all_regions_<measure>.html`) — interactive charts for quick inspection.
2. `src/cross_measure.py` + `scripts/cross_measure_run.py` — concise code that produced the CSV/PNG summaries.

---

What I changed (brief):
- Replaced notebook-centered exploration with a CLI Plotly explorer (HTML output) to keep the repo clean and reproducible.
- Added a tested cross-measure module and runner so the assignment is repeatable.
- Tidied project structure and README so the main files are obvious.

---

Exactly how I pulled the data (detailed, reproducible):

1. Source: CDC BRFSS Prevalence & Trends on data.cdc.gov (Socrata resource `dttw-5yxu`).
2. Script: `src/download_data.py` queries the Socrata endpoint `https://data.cdc.gov/resource/dttw-5yxu.json` using HTTP GET. The script pages results using `?$limit=5000&$offset=<n>` until no rows remain.
3. Filtering: for each measure I request only the overall prevalence rows (no demographic breakdowns) by matching the `topic` and `question` fields in the Socrata rows. This keeps rows where the location is a U.S. state (we drop national/territory rows).
4. Cleaning: the script normalizes column names and types, keeps `year, state, locationdesc, measure, value, ci_lower, ci_upper, sample_size`, and writes one CSV per measure to `data/processed/`.
5. Combining: we combine the three measure CSVs into `data/processed/brfss_combined_2011_2023.csv`, which is the single source-of-truth used by the scripts.

To re-download everything:

```bash
python -m src.download_data --all --overwrite
```

---

Where to find the important files

```
RegionalVitals/
├── src/
│   ├── cross_measure.py
│   ├── trend_analysis.py
│   ├── compute_prevalence.py
│   └── download_data.py
├── scripts/
│   ├── cross_measure_run.py
│   └── explore.py
├── outputs/
│   ├── explore/    # interactive HTML charts
│   └── tables/      # CSV summaries (local only)
├── tests/
└── data/processed/
```

---

How to run (short)

```bash
# setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# single region + measure
python -m scripts.example_region_run --region West --measure obesity

# cross-measure (all regions)
python -m scripts.cross_measure_run --all-regions

# interactive explorer
python -m scripts.explore

# tests
pytest tests/ -v
```

---

If you'd like I can push this README and the other small changes to a new branch and share the link here.
