"""Interactive data explorer (CLI).

Browse BRFSS prevalence data by region, measure, and state.
Generates Plotly HTML charts or Matplotlib PNGs to an output directory.

Usage (from repo root):
    # Launch interactive mode — prompts you for region/measure/state:
    python -m scripts.explore

    # Non-interactive — specify filters on the command line:
    python -m scripts.explore --region West --measure obesity
    python -m scripts.explore --region Midwest --measure coverage --states IL,IN,OH
    python -m scripts.explore --all-regions --measure smoking
    python -m scripts.explore --region Southeast --all-measures

    # Change output format (default: html):
    python -m scripts.explore --region West --measure obesity --fmt png

Outputs are written to outputs/explore/ by default (gitignored).
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.compute_prevalence import compute_state_prevalence
from src.cross_measure import compare_measures_over_time, compute_measure_correlations
from src.region_mapping import REGIONS, STATE_TO_REGION
from src.trend_analysis import compute_region_year_prevalence
from src.utils import safe_read_csv


# ── Helpers ─────────────────────────────────────────────────────────────────

VALID_REGIONS = list(REGIONS.keys())
VALID_MEASURES = ["obesity", "coverage", "smoking"]


def _load(path: Path) -> pd.DataFrame:
    """Load the combined BRFSS CSV and add a region column."""
    df = safe_read_csv(path)
    df = df.assign(region=df["state"].map(STATE_TO_REGION).fillna("Other"))
    return df


# ── Plotly renderers (HTML) ─────────────────────────────────────────────────

def _try_import_plotly():
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        return px, go
    except ImportError:
        return None, None


def _plotly_region_trend(df: pd.DataFrame, region: str, measure: str, out: Path):
    px, _ = _try_import_plotly()
    ts = compute_region_year_prevalence(df[df["region"] == region], measure=measure)
    if ts.empty:
        print(f"  ⚠ No data for {region}/{measure}")
        return
    ts = ts.sort_values("year")
    fig = px.line(
        ts, x="year", y="prevalence_pct",
        title=f"{region} — {measure.title()} (weighted prevalence)",
        markers=True,
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Prevalence (%)")
    fig.write_html(out)
    print(f"  ✓ {out}")


def _plotly_state_trends(df: pd.DataFrame, region: str, measure: str, out: Path,
                         states: list[str] | None = None):
    px, _ = _try_import_plotly()
    subset = df[(df["region"] == region) & (df["measure"] == measure)]
    if states:
        subset = subset[subset["state"].isin(states)]
    prev = compute_state_prevalence(subset)
    if prev.empty:
        print(f"  ⚠ No state data for {region}/{measure}")
        return
    fig = px.line(
        prev, x="year", y="prevalence_pct", color="state",
        title=f"{region} — {measure.title()} by State",
        markers=True,
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Prevalence (%)")
    fig.write_html(out)
    print(f"  ✓ {out}")


def _plotly_cross_measure(df: pd.DataFrame, region: str, out: Path):
    px, _ = _try_import_plotly()
    trends = compare_measures_over_time(df, region)
    if trends.empty:
        print(f"  ⚠ No cross-measure data for {region}")
        return
    fig = px.line(
        trends, x="year", y="prevalence_pct", color="measure",
        title=f"{region} — Cross-Measure Comparison",
        markers=True,
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Prevalence (%)")
    fig.write_html(out)
    print(f"  ✓ {out}")


def _plotly_all_regions(df: pd.DataFrame, measure: str, out: Path):
    px, _ = _try_import_plotly()
    ts = compute_region_year_prevalence(df, measure=measure)
    if ts.empty:
        print(f"  ⚠ No data for {measure}")
        return
    fig = px.line(
        ts, x="year", y="prevalence_pct", color="region",
        title=f"All Regions — {measure.title()}",
        markers=True,
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Prevalence (%)")
    fig.write_html(out)
    print(f"  ✓ {out}")


# ── Matplotlib renderers (PNG) ──────────────────────────────────────────────

def _mpl_region_trend(df: pd.DataFrame, region: str, measure: str, out: Path):
    ts = compute_region_year_prevalence(df[df["region"] == region], measure=measure)
    if ts.empty:
        return
    ts = ts.sort_values("year")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ts["year"], ts["prevalence_pct"], marker="o", color="#1f77b4")
    ax.set_title(f"{region} — {measure.title()} (weighted prevalence)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out}")


def _mpl_state_trends(df: pd.DataFrame, region: str, measure: str, out: Path,
                       states: list[str] | None = None):
    subset = df[(df["region"] == region) & (df["measure"] == measure)]
    if states:
        subset = subset[subset["state"].isin(states)]
    prev = compute_state_prevalence(subset)
    if prev.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    for state, grp in prev.groupby("state"):
        g = grp.sort_values("year")
        ax.plot(g["year"], g["prevalence_pct"], label=state, alpha=0.6)
    ax.set_title(f"{region} — {measure.title()} by State")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.legend(ncol=4, fontsize=7, frameon=False)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out}")


def _mpl_cross_measure(df: pd.DataFrame, region: str, out: Path):
    trends = compare_measures_over_time(df, region)
    if trends.empty:
        return
    colors = {"obesity": "#e74c3c", "coverage": "#2ecc71", "smoking": "#3498db"}
    fig, ax = plt.subplots(figsize=(9, 5))
    for measure, grp in trends.groupby("measure"):
        g = grp.sort_values("year")
        ax.plot(g["year"], g["prevalence_pct"], marker="o", label=measure.title(),
                color=colors.get(measure))
    ax.set_title(f"{region} — Cross-Measure Comparison")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out}")


def _mpl_all_regions(df: pd.DataFrame, measure: str, out: Path):
    ts = compute_region_year_prevalence(df, measure=measure)
    if ts.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    for region, grp in ts.groupby("region"):
        g = grp.sort_values("year")
        ax.plot(g["year"], g["prevalence_pct"], marker="o", label=region)
    ax.set_title(f"All Regions — {measure.title()}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out}")


# ── Main driver ─────────────────────────────────────────────────────────────

def generate(
    df: pd.DataFrame,
    region: str | None,
    measure: str | None,
    states: list[str] | None,
    all_regions: bool,
    all_measures: bool,
    out_dir: Path,
    fmt: str,
):
    """Generate exploration charts based on the chosen filters."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "html" if fmt == "html" else "png"

    # Decide which renderer set to use
    use_plotly = fmt == "html"
    if use_plotly:
        px, _ = _try_import_plotly()
        if px is None:
            print("plotly not installed — falling back to matplotlib (png)")
            use_plotly = False
            ext = "png"

    region_trend = _plotly_region_trend if use_plotly else _mpl_region_trend
    state_trend = _plotly_state_trends if use_plotly else _mpl_state_trends
    cross_meas = _plotly_cross_measure if use_plotly else _mpl_cross_measure
    all_reg = _plotly_all_regions if use_plotly else _mpl_all_regions

    # ── All regions × single measure ────────────────────────────────────
    if all_regions and measure:
        print(f"\n── All regions × {measure} ──")
        all_reg(df, measure, out_dir / f"all_regions_{measure}.{ext}")
        for r in VALID_REGIONS:
            region_trend(df, r, measure, out_dir / f"{r.lower()}_{measure}_trend.{ext}")
        return

    # ── Single region × all measures ────────────────────────────────────
    if region and all_measures:
        print(f"\n── {region} × all measures ──")
        cross_meas(df, region, out_dir / f"{region.lower()}_cross_measure.{ext}")
        for m in VALID_MEASURES:
            region_trend(df, region, m, out_dir / f"{region.lower()}_{m}_trend.{ext}")
            state_trend(df, region, m, out_dir / f"{region.lower()}_{m}_states.{ext}", states)
        return

    # ── Single region × single measure ──────────────────────────────────
    if region and measure:
        tag = region.lower()
        print(f"\n── {region} × {measure} ──")
        region_trend(df, region, measure, out_dir / f"{tag}_{measure}_trend.{ext}")
        state_trend(df, region, measure, out_dir / f"{tag}_{measure}_states.{ext}", states)
        cross_meas(df, region, out_dir / f"{tag}_cross_measure.{ext}")
        return

    # ── Fallback: everything ────────────────────────────────────────────
    print("\n── Full exploration (all regions × all measures) ──")
    for m in VALID_MEASURES:
        all_reg(df, m, out_dir / f"all_regions_{m}.{ext}")
    for r in VALID_REGIONS:
        cross_meas(df, r, out_dir / f"{r.lower()}_cross_measure.{ext}")
        for m in VALID_MEASURES:
            region_trend(df, r, m, out_dir / f"{r.lower()}_{m}_trend.{ext}")


# ── Interactive prompt ──────────────────────────────────────────────────────

def interactive_prompt() -> dict:
    """Walk the user through region/measure/state selection."""
    print("\n╔══════════════════════════════════════════════╗")
    print("║   RegionalVitals — Interactive Explorer      ║")
    print("╚══════════════════════════════════════════════╝\n")

    # Region
    print("Available regions:")
    for i, r in enumerate(VALID_REGIONS, 1):
        print(f"  {i}. {r}")
    print(f"  {len(VALID_REGIONS) + 1}. All regions")
    choice = input("\nSelect region (number or name): ").strip()
    all_regions = False
    region = None
    if choice.isdigit():
        idx = int(choice)
        if idx == len(VALID_REGIONS) + 1:
            all_regions = True
        elif 1 <= idx <= len(VALID_REGIONS):
            region = VALID_REGIONS[idx - 1]
    elif choice.lower() == "all":
        all_regions = True
    else:
        # Try to match by name
        for r in VALID_REGIONS:
            if r.lower() == choice.lower():
                region = r
                break

    # Measure
    print("\nAvailable measures:")
    for i, m in enumerate(VALID_MEASURES, 1):
        print(f"  {i}. {m.title()}")
    print(f"  {len(VALID_MEASURES) + 1}. All measures")
    choice = input("\nSelect measure (number or name): ").strip()
    all_measures = False
    measure = None
    if choice.isdigit():
        idx = int(choice)
        if idx == len(VALID_MEASURES) + 1:
            all_measures = True
        elif 1 <= idx <= len(VALID_MEASURES):
            measure = VALID_MEASURES[idx - 1]
    elif choice.lower() == "all":
        all_measures = True
    else:
        for m in VALID_MEASURES:
            if m.lower() == choice.lower():
                measure = m
                break

    # States (optional)
    states = None
    if region and not all_regions:
        avail = REGIONS.get(region, [])
        print(f"\nStates in {region}: {', '.join(avail)}")
        sel = input("Filter to specific states? (comma-separated, or Enter for all): ").strip()
        if sel:
            states = [s.strip().upper() for s in sel.split(",") if s.strip()]
            states = [s for s in states if s in avail] or None

    # Format
    fmt_choice = input("\nOutput format — html (interactive) or png (static)? [html]: ").strip().lower()
    fmt = "png" if fmt_choice == "png" else "html"

    return {
        "region": region,
        "measure": measure,
        "states": states,
        "all_regions": all_regions,
        "all_measures": all_measures,
        "fmt": fmt,
    }


# ── CLI entry point ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Explore BRFSS prevalence data interactively.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python -m scripts.explore                                    # interactive mode
  python -m scripts.explore --region West --measure obesity    # direct
  python -m scripts.explore --all-regions --measure smoking    # all regions
  python -m scripts.explore --region Midwest --all-measures    # all measures
  python -m scripts.explore --region Southeast --measure coverage --states FL,GA
""",
    )
    parser.add_argument("--region", choices=VALID_REGIONS, help="Region to explore")
    parser.add_argument("--measure", choices=VALID_MEASURES, help="Health measure")
    parser.add_argument("--states", help="Comma-separated state abbreviations to filter")
    parser.add_argument("--all-regions", action="store_true", help="Compare across all regions")
    parser.add_argument("--all-measures", action="store_true", help="Compare all measures for a region")
    parser.add_argument("--fmt", choices=["html", "png"], default="html",
                        help="Output format (default: html)")
    parser.add_argument("--combined", default="data/processed/brfss_combined_2011_2023.csv",
                        help="Path to combined BRFSS CSV")
    parser.add_argument("--out-dir", default="outputs/explore",
                        help="Directory for generated charts")
    args = parser.parse_args()

    # If no filters specified, enter interactive mode
    if not args.region and not args.measure and not args.all_regions and not args.all_measures:
        opts = interactive_prompt()
    else:
        states = [s.strip().upper() for s in args.states.split(",")] if args.states else None
        opts = {
            "region": args.region,
            "measure": args.measure,
            "states": states,
            "all_regions": args.all_regions,
            "all_measures": args.all_measures,
            "fmt": args.fmt,
        }

    combined_path = Path(args.combined)
    out_dir = Path(args.out_dir)

    if not combined_path.exists():
        print(f"Error: combined file not found: {combined_path}")
        sys.exit(1)

    df = _load(combined_path)
    generate(df, **opts, out_dir=out_dir)
    print(f"\nDone. Charts saved to {out_dir}/")


if __name__ == "__main__":
    main()
