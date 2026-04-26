# RegionalVitals

*Analyze CDC public health trends across U.S. regions — obesity, smoking, and healthcare coverage from 2011 to 2023.*

A Python package that analyzes CDC BRFSS health data (2011–2023) across five U.S. regions (Northeast, Southeast, Midwest, Southwest, West). We examine obesity, healthcare coverage, and smoking prevalence trends at both the state and regional level. The package is equiped with various exploratory, analytical, data processing, and visual tools.

---

## Dataset

- **Source:** CDC Behavioral Risk Factor Surveillance System (BRFSS) Prevalence & Trends, hosted on [data.cdc.gov](https://data.cdc.gov) (Socrata resource `dttw-5yxu`).
- **Years covered:** 2011–2023
- **Measures:** Obesity, healthcare coverage, smoking
- **Granularity:** State-level, overall prevalence (no demographic breakdowns)
- **Legal / ethical:** Publicly available U.S. government data; no PII or restricted access.

### Data Pipeline

1. `src/download_data.py` queries the CDC Socrata API (`?$limit=5000&$offset=<n>`) and pages until all rows are retrieved.
2. Rows are filtered to overall state-level prevalence, normalized to a consistent schema (`year, state, locationdesc, measure, value, ci_lower, ci_upper, sample_size`), and written as one CSV per measure to `data/processed/`.
3. `src/preprocessing.py` combines the three CSVs into `brfss_combined_2011_2023.csv`. During combination, rows with missing critical values (`year`, `state`, `measure`, `value`) are dropped, and territory/non-state rows (GU, PR, VI, etc.) are filtered out via `src/region_mapping.py`.

```bash
# Re-download everything from the CDC API
python -m src.download_data --all --overwrite

# Or combine existing CSVs
python -m src.preprocessing --combine
```

---

## Analysis Modules (`src/`)

| Module | What it does |
|---|---|
| `compute_prevalence.py` | Computes sample-size-weighted prevalence per state × year × measure |
| `trend_analysis.py` | Linear trend slopes (`np.polyfit`), rolling averages, regional convergence/divergence, pivot tables, and pre/post-COVID comparison |
| `covid_analysis.py` | Dedicated COVID-era trend-shift analysis: disruption scores, slope shifts before vs after 2020, and recovery trajectory per region |
| `cross_measure.py` | Compares obesity vs. coverage vs. smoking within a region: correlation matrices, ranked changes, cross-region pivot tables |
| `regional_summary.py` | Six formatted summary tables: latest-year snapshot, period change, trend slopes, regional rankings, year-by-region matrix, grand summary statistics |
| `state_rankings.py` | Ranks states by largest increase/decrease in prevalence for each measure over a configurable time window |
| `coverage_heatmap.py` | Generates annotated seaborn heatmaps of prevalence by state × year for a given region |
| `region_mapping.py` | Defines five U.S. regions, state-to-region mapping, territory list, and `filter_states_only()` to drop non-state rows |
| `preprocessing.py` | Copies raw CSVs into `data/processed/`, combines them, handles missing data |
| `download_data.py` | Fetches BRFSS data directly from the CDC Socrata API |
| `utils.py` | `safe_read_csv` / `safe_write_csv` helpers used throughout the project |

---

## Runner Scripts (`scripts/`)

| Script | What it does |
|---|---|
| `example_region_run.py` | Generates tables + figures for a single region × measure |
| `example_all_regions_run.py` | Runs all five regions for a single measure (convergence, COVID comparison, etc.) |
| `covid_analysis_run.py` | Prints full COVID trend-shift results to console and saves CSVs — disruption scores, slope shifts, and recovery trajectories for all regions and measures |
| `run_all.py` | Batch driver: iterates every region × measure combination |
| `cross_measure_run.py` | Cross-measure comparison for one or all regions (CSV tables + PNG figures) |
| `regional_summary_run.py` | Generates cross-region comparison tables (snapshot, period change, slopes) |
| `state_rankings_run.py` | Ranks states by largest increase/decrease and produces bar charts |
| `explore.py` | Interactive CLI-based Plotly explorer — generates HTML charts with hover/zoom/filter |
| `midwest_coverage.py` | Focused analysis of Midwest healthcare coverage trends |

---

## Exploratory Analysis

- **Interactive explorer:** `scripts/explore.py` — a CLI-based tool that generates interactive Plotly HTML charts (hover, zoom, filter) or static PNGs. Supports both interactive prompts and command-line flags. You can drill down by region, measure, or specific states.

```bash
# Interactive mode (prompts you for choices)
python -m scripts.explore

# CLI mode examples
python -m scripts.explore --region West --measure obesity
python -m scripts.explore --region Midwest --measure coverage --states IL,IN,OH
python -m scripts.explore --all-regions --measure smoking
python -m scripts.explore --region Southeast --all-measures
python -m scripts.explore --region West --measure obesity --fmt png
```

Charts are saved to `outputs/explore/` (38 HTML files covering every region × measure combination plus cross-measure views).

---

## Analytical Methods

- **Weighted prevalence:** Sample-size-weighted averages at both state and regional levels (`compute_prevalence.py`, `trend_analysis.py`)
- **Linear trend fitting:** `np.polyfit` degree-1 fit with R² to estimate annual change in percentage points (`trend_analysis.py`)
- **Rolling averages:** Configurable-window smoothing to reduce year-to-year noise (`trend_analysis.py`)
- **Convergence / divergence:** Year-over-year standard deviation across regions to determine if regions are converging or diverging (`trend_analysis.py`)
- **Pre/post-COVID comparison:** Compares mean prevalence in a pre-COVID window (2017–2019) vs. post-COVID window (2021–2023) per region and measure (`trend_analysis.py`)
- **COVID disruption score:** Combines absolute delta and slope shift magnitude to quantify how much COVID altered each region's health trajectory (`covid_analysis.py`)
- **Recovery trajectory:** Projects the pre-COVID trend line forward and measures the gap against actual post-COVID values to assess whether regions are recovering (`covid_analysis.py`)
- **Cross-measure correlations:** Pairwise Pearson correlations between obesity, coverage, and smoking at the state level within a region (`cross_measure.py`)
- **State rankings:** States ranked by absolute and percentage change in prevalence, with top-N increasers and decreasers (`state_rankings.py`)
- **Pivot tables / multi-index grouping:** Region × year, region × measure, and measure × year pivot tables for cross-sectional comparison (`trend_analysis.py`, `regional_summary.py`)
- **Heatmaps:** Annotated state × year heatmaps for visual inspection of patterns (`coverage_heatmap.py`)

---

## Tests

We have 88 tests across six test files:

| Test file | Covers |
|---|---|
| `tests/test_covid_analysis.py` | COVID disruption scores, slope shifts, recovery trajectory, empty input handling (28 tests) |
| `tests/test_cross_measure.py` | Cross-measure comparison functions |
| `tests/test_trend_analysis.py` | Trend slopes, rolling averages, convergence, COVID comparison |
| `tests/test_compute_prevalence.py` | State prevalence computation |
| `tests/test_coverage_heatmap.py` | Heatmap generation |
| `tests/test_smoke.py` | Smoke tests for imports and basic wiring |

**Coverage:** 36% overall, 92% for `src/cross_measure.py`.

```bash
# Run tests
pytest tests/ -v

# Run with coverage report
pytest --cov=src tests/
```
---

## Setup & Usage

**Requirements:** Python **>=3.10**

```bash
# Clone and set up
git clone https://github.com/AryanThodupunuri/regional-vitals.git
cd regional-vitals
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# or: pip install -e ".[dev]"

# Download data from CDC API
python -m src.download_data --all

# Single region + measure analysis
python -m scripts.example_region_run --region West --measure obesity

# All regions for one measure (convergence, COVID comparison)
python -m scripts.example_all_regions_run --measure smoking

# COVID trend-shift analysis (all regions and measures)
python -m scripts.covid_analysis_run
python -m scripts.covid_analysis_run --measure obesity

# Cross-measure comparison (all regions)
python -m scripts.cross_measure_run --all-regions

# Regional summary tables
python -m scripts.regional_summary_run

# State rankings
python -m scripts.state_rankings_run

# Batch run (all region × measure combos)
python -m scripts.run_all

# Interactive Plotly explorer
python -m scripts.explore

# Midwest coverage deep-dive
python -m scripts.midwest_coverage

# Run tests
pytest tests/ -v
```

---
## Quick demo

After installing and downloading the data, run:

```bash
python demo.py
```

This will print:
- **Trend slopes** — obesity prevalence change (per person/year) across all five regions
- **COVID disruption scores** — how much COVID shifted each region's health trajectory
- **State rankings** — top 5 states by obesity increase from 2011–2023

For interactive charts with hover and zoom:

```bash
python -m scripts.explore
```

---

## Repository Structure

```
RegionalVitals/
├── src/                          # Core analysis package
│   ├── __init__.py
│   ├── compute_prevalence.py     # Weighted prevalence calculations
│   ├── covid_analysis.py         # COVID trend-shift and disruption analysis
│   ├── coverage_heatmap.py       # Seaborn heatmaps
│   ├── cross_measure.py          # Cross-measure comparisons
│   ├── download_data.py          # CDC API data fetcher
│   ├── preprocessing.py          # CSV combining + missing data handling
│   ├── region_mapping.py         # Region definitions + territory filtering
│   ├── regional_summary.py       # Six summary table generators
│   ├── state_rankings.py         # State-level change rankings
│   ├── trend_analysis.py         # Slopes, rolling avg, convergence, COVID
│   └── utils.py                  # Shared I/O helpers
├── scripts/                      # CLI runner scripts
│   ├── covid_analysis_run.py     # COVID trend-shift analysis runner
│   ├── cross_measure_run.py
│   ├── example_all_regions_run.py
│   ├── example_region_run.py
│   ├── explore.py                # Interactive Plotly explorer
│   ├── midwest_coverage.py
│   ├── regional_summary_run.py
│   ├── run_all.py
│   └── state_rankings_run.py
├── tests/                        # Unit tests (pytest)
│   ├── test_covid_analysis.py
│   ├── test_compute_prevalence.py
│   ├── test_coverage_heatmap.py
│   ├── test_cross_measure.py
│   ├── test_smoke.py
│   └── test_trend_analysis.py
├── data/
│   ├── processed/                # Cleaned CSVs (source of truth)
│   └── README_DATA.md
├── outputs/                      # Generated locally (gitignored)
│   ├── explore/                  # Interactive HTML charts
│   ├── figures/                  # PNG figures
│   └── tables/                   # CSV summary tables
├── docs/
│   └── NO_OUTPUTS.md
├── pyproject.toml                # pip install -e ".[dev]"
├── requirements.txt              # Pinned dependencies
├── CONTRIBUTING.md
└── README.md
```
