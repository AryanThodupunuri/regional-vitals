"""State-level rankings runner.

Generates tables and figures ranking states by largest increase/decrease
in prevalence for each health measure (obesity, coverage, smoking).

Usage (from repo root):
    python -m regional_analysis.state_rankings_run

Outputs:
    outputs/tables/state_rankings_all_measures.csv
    outputs/tables/state_rankings_obesity.csv
    outputs/tables/state_rankings_coverage.csv
    outputs/tables/state_rankings_smoking.csv
    outputs/figures/state_rankings_obesity.png
    outputs/figures/state_rankings_coverage.png
    outputs/figures/state_rankings_smoking.png

Author: Andrew Kohl
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.state_rankings import compute_state_change, rank_states, rank_all_measures
from src.utils import safe_read_csv, safe_write_csv


def plot_state_rankings(
    changes: pd.DataFrame,
    measure: str,
    top_n: int,
    out_path: Path,
):
    """Create a horizontal bar chart showing top increasers and decreasers."""
    if changes.empty:
        return

    # Top N increasers and decreasers
    top_inc = changes.nlargest(top_n, "abs_change")
    top_dec = changes.nsmallest(top_n, "abs_change")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Top increasers ---
    colors_inc = plt.cm.Reds(np.linspace(0.4, 0.85, len(top_inc)))
    bars1 = ax1.barh(
        top_inc["state"], top_inc["abs_change"],
        color=colors_inc[::-1], edgecolor="white", linewidth=0.5,
    )
    ax1.set_xlabel("Change (percentage points)")
    ax1.set_title(f"Top {top_n} Largest Increases — {measure.title()}")
    ax1.invert_yaxis()
    for bar, val in zip(bars1, top_inc["abs_change"]):
        ax1.text(
            bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
            f"+{val:.1f}", va="center", fontsize=9,
        )

    # --- Top decreasers ---
    colors_dec = plt.cm.Greens(np.linspace(0.4, 0.85, len(top_dec)))
    dec_values = top_dec["abs_change"].abs()
    bars2 = ax2.barh(
        top_dec["state"], dec_values,
        color=colors_dec[::-1], edgecolor="white", linewidth=0.5,
    )
    ax2.set_xlabel("Change (percentage points, absolute)")
    ax2.set_title(f"Top {top_n} Largest Decreases — {measure.title()}")
    ax2.invert_yaxis()
    for bar, val in zip(bars2, top_dec["abs_change"]):
        ax2.text(
            bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va="center", fontsize=9,
        )

    fig.suptitle(
        f"State-Level Rankings: {measure.title()} ({int(changes['start_year'].iloc[0])}–{int(changes['end_year'].iloc[0])})",
        fontsize=13, fontweight="bold", y=1.02,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run(
    combined_path: Path,
    tables_dir: Path,
    figures_dir: Path,
    top_n: int = 10,
):
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    df = safe_read_csv(combined_path)

    measures = ["obesity", "coverage", "smoking"]

    # Combined rankings table across all measures
    all_rankings = rank_all_measures(df, measures=measures, top_n=top_n)
    all_out = tables_dir / "state_rankings_all_measures.csv"
    safe_write_csv(all_rankings, all_out)
    print(f"Wrote {all_out} (rows={len(all_rankings)})")

    # Per-measure rankings + figures
    for measure in measures:
        changes = compute_state_change(df, measure)

        # Save per-measure ranking CSV
        csv_out = tables_dir / f"state_rankings_{measure}.csv"
        safe_write_csv(changes, csv_out)
        print(f"Wrote {csv_out} (rows={len(changes)})")

        # Save per-measure bar chart
        fig_out = figures_dir / f"state_rankings_{measure}.png"
        plot_state_rankings(changes, measure, top_n, fig_out)
        print(f"Wrote {fig_out}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate state-level rankings by largest increase/decrease."
    )
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS long-format CSV",
    )
    parser.add_argument(
        "--out-dir", default="outputs/tables",
        help="Directory for output tables",
    )
    parser.add_argument(
        "--fig-dir", default="outputs/figures",
        help="Directory for output figures",
    )
    parser.add_argument(
        "--top-n", type=int, default=10,
        help="Number of top states per direction (default 10)",
    )
    args = parser.parse_args()

    run(
        combined_path=Path(args.combined),
        tables_dir=Path(args.out_dir),
        figures_dir=Path(args.fig_dir),
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
