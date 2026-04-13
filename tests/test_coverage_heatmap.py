import pandas as pd
import pytest
from src.coverage_heatmap import generate_region_heatmap

def test_heatmap_file_creation(tmp_path):
    data = {
        'state': ['VA', 'VA', 'MD', 'MD'],
        'year': [2011, 2023, 2011, 2023],
        'prevalence_pct': [85.0, 92.0, 88.0, 94.0]
    }
    df = pd.DataFrame(data)
    test_file = tmp_path / "test_map.png"
    
    generate_region_heatmap(df, "Test Region", test_file)
    
    assert test_file.exists()