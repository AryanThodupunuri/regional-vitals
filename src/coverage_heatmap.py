"""coverage_heatmap.py

Generate annotated heatmaps of healthcare coverage prevalence by state and year
for a given region.
"""

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


def generate_region_heatmap(df, region_name, output_path, color_map="viridis"):
    """Create and save a heatmap of prevalence by state × year for one region.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns ``state``, ``year``, and ``prevalence_pct``.
    region_name : str
        Label used in the chart title (e.g. "Northeast").
    output_path : str or Path
        File path for the saved PNG.
    color_map : str
        Matplotlib / seaborn colormap name.
    """
    if df.empty:
        print(f"Skipping {region_name}: No data found.")
        return

    pivot_df = df.pivot(index="state", columns="year", values="prevalence_pct")
    
    plt.figure(figsize=(12, 8))
    
    sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap=color_map, linewidths=.5)
    
    plt.title(f"Healthcare Coverage Prevalence: {region_name} Region (2011-2023)")
    plt.xlabel("Year")
    plt.ylabel("State")
    plt.tight_layout()
    
    plt.savefig(output_path)
    plt.close()
    print(f"Success! Heatmap saved to {output_path}")