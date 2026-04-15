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
```bash
# Interactive mode (walks you through selection prompts):
python -m scripts.explore

# Or specify directly:
python -m scripts.explore --region West --measure obesity
python -m scripts.explore --region Southeast --all-measures
python -m scripts.explore --all-regions --measure smoking
```
Charts go to `outputs/explore/`. Open any `.html` file in a browser.

### 3. Trend Analysis Functions (`src/trend_analysis.py`)
All the trend computation logic lives here — linear slopes, rolling averages, regional convergence metrics, and pre-vs-post COVID comparisons. Every other script builds on top of these functions.

### 4. Region & State Mapping (`src/region_mapping.py`)
Defines the five regions (Northeast, Southeast, Midwest, Southwest, West) and maps every state to its region. This is what everything else references.

### 5. State Rankings (`src/state_rankings.py`)
Ranks states by largest increase or decrease in a given measure over the full time range. Runner: `python -m scripts.state_rankings_run`.

### 6. Tests (`tests/`)
59 unit tests covering cross-measure functions, trend analysis, prevalence computation, and import smoke tests. Run with `pytest tests/ -v`.

---

## How We Got the Data

All of our data comes from the **CDC Behavioral Risk Factor Surveillance System (BRFSS) Prevalence & Trends** dataset. Here's exactly how we pulled it:

1. The CDC publishes BRFSS data on their open data portal at [data.cdc.gov](https://data.cdc.gov). The specific dataset is **"Behavioral Risk Factor Surveillance System (BRFSS) Prevalence Data (2011 to present)"** — Socrata resource ID `dttw-5yxu`.

2. We wrote a Python script (`src/download_data.py`) that hits the CDC's Socrata API endpoint at `https://data.cdc.gov/resource/dttw-5yxu.json`. It pages through the API in chunks of 5,000 rows at a time.

3. For each of our three measures, we filter the API query by the BRFSS topic and question:
   - **Obesity**: Topic = "Overweight and Obesity (BMI)", question contains "obese"
   - **Coverage**: Topic = "Health Care Access/Coverage", question contains "health care coverage"
   - **Smoking**: Topic = "Tobacco Use", question contains "current smoker"

4. We only keep the "Overall" breakout (no demographic sub-groups), and we drop territory/national rows — so the final data is 50 states + DC, years 2011–2023.

5. The raw API response gets cleaned and standardized into our project schema: `year, state, locationdesc, measure, value, ci_lower, ci_upper, sample_size`. Each measure gets saved as its own CSV in `data/processed/`, and then we combine them into one file (`brfss_combined_2011_2023.csv`) that every script reads from.

To re-download from scratch:
```bash
python -m src.download_data --all --overwrite
```

---

## Where Everything Lives

```
RegionalVitals/
├── src/                            # All reusable functions (the actual package)
│   ├── cross_measure.py            #   Cross-measure comparison (obesity vs coverage vs smoking)
│   ├── trend_analysis.py           #   Trend slopes, rolling avg, convergence, COVID comparison
│   ├── compute_prevalence.py       #   Weighted state-level prevalence calculation
│   ├── region_mapping.py           #   5-region definitions + state-to-region lookup
│   ├── state_rankings.py           #   State change rankings
│   ├── coverage_heatmap.py         #   Region heatmap generation
│   ├── download_data.py            #   CDC Socrata API data downloader
│   ├── preprocessing.py            #   CSV combining helpers
│   └── utils.py                    #   safe_read_csv, safe_write_csv
│
├── scripts/                        # CLI runners — these call src/ functions and write outputs
│   ├── cross_measure_run.py        #   Run cross-measure analysis for any/all regions
│   ├── explore.py                  #   Interactive data explorer (Plotly HTML or Matplotlib PNG)
│   ├── example_region_run.py       #   Single region + measure → tables + figures
│   ├── example_all_regions_run.py  #   All-region convergence & COVID comparison
│   ├── state_rankings_run.py       #   State ranking charts
│   ├── run_all.py                  #   Batch driver (every region × every measure)
│   └── midwest_coverage.py         #   Midwest-specific coverage script
│
├── tests/                          # 59 unit tests
│   ├── test_cross_measure.py       #   31 tests for cross-measure functions
│   ├── test_trend_analysis.py      #   Trend analysis tests
│   ├── test_coverage_heatmap.py
│   ├── test_compute_prevalence/
│   └── test_smoke.py               #   Import smoke tests
│
├── data/processed/                 # Combined BRFSS CSV (input data)
├── docs/                           # Extra documentation
├── outputs/                        # Generated tables/figures (local only, gitignored)
├── requirements.txt
├── CONTRIBUTING.md
└── .gitignore
```

**Note:** Generated outputs (CSVs, PNGs, HTMLs) are written to `outputs/` locally but are **not committed** to the repo. Just run the scripts to reproduce anything.

---

## Setup & Running

```bash
# 1. Clone and set up
git clone <repo-url> && cd RegionalVitals
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Run a single region + measure
python -m scripts.example_region_run --region West --measure obesity

# 3. Run cross-measure comparison for all regions
python -m scripts.cross_measure_run --all-regions

# 4. Generate interactive explorer charts
python -m scripts.explore --all-regions --measure obesity
python -m scripts.explore --region Midwest --all-measures

# 5. Run all-region convergence & COVID comparison
python -m scripts.example_all_regions_run --all

# 6. State rankings
python -m scripts.state_rankings_run

# 7. Run everything at once
python -m scripts.run_all
```

## Running Tests

```bash
pytest tests/ -v
```

## Limitations

- This is descriptive analysis only — we're not making any causal claims.
- BRFSS methodology has changed over the years, so comparisons across the full time range should be interpreted carefully.
- Some state-year estimates have small sample sizes and may not be super reliable.
