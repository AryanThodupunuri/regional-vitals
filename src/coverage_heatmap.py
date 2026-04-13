import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def generate_region_heatmap(df, region_name, output_path, color_map="viridis"):
    """
    Creates a high-contrast heatmap for any region's healthcare data.
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