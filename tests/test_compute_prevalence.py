import pandas as pd
import pytest
from src.compute_prevalence import compute_state_prevalence


def test_compute_state_prevalence_uses_weighted_mean():
    """
    Verify that compute_state_prevalence uses a sample-size weighted mean.

    Given multiple rows for the same year/state/measure, the function should:
    - weight each value by its sample_size
    - aggregate sample sizes
    - compute prevalence as weighted_sum / total_sample_size

    This ensures consistency with the weighted aggregation used elsewhere
    in the pipeline and prevents incorrect unweighted averages.
    """
    df = pd.DataFrame({
        "year": [2023, 2023],
        "state": ["VA", "VA"],
        "measure": ["obesity", "obesity"],
        "value": [10.0, 30.0],
        "sample_size": [100, 300],
    })

    result = compute_state_prevalence(df)

    assert len(result) == 1
    assert result.loc[0, "year"] == 2023
    assert result.loc[0, "state"] == "VA"
    assert result.loc[0, "measure"] == "obesity"
    assert result.loc[0, "sample_size"] == 400
    assert result.loc[0, "prevalence_pct"] == 25.0
