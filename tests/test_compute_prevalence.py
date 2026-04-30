import pandas as pd
import pytest
from src.compute_prevalence import (
    compute_state_prevalence,
    compute_state_prevalence_change,
)


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


def test_compute_state_prevalence_change_fixed_window():
    state_prev = pd.DataFrame(
        {
            "year": [2020, 2020, 2022, 2022],
            "state": ["AA", "BB", "AA", "BB"],
            "measure": ["obesity"] * 4,
            "prevalence_pct": [10.0, 20.0, 12.0, 15.0],
            "sample_size": [100, 100, 100, 100],
        }
    )
    out = compute_state_prevalence_change(
        state_prev, ["AA", "BB"], start_year=2020, end_year=2022
    )
    assert len(out) == 2
    aa = out[out["state"] == "AA"].iloc[0]
    assert aa["total_change"] == 2.0
    bb = out[out["state"] == "BB"].iloc[0]
    assert bb["total_change"] == pytest.approx(-5.0)


def test_compute_state_prevalence_change_per_state_year_range():
    state_prev = pd.DataFrame(
        {
            "year": [2019, 2021, 2020, 2022],
            "state": ["X", "X", "Y", "Y"],
            "prevalence_pct": [30.0, 20.0, 10.0, 11.0],
            "sample_size": [1, 1, 1, 1],
        }
    )
    out = compute_state_prevalence_change(
        state_prev, ["X", "Y"], use_each_states_year_range=True
    )
    assert len(out) == 2
    x = out[out["state"] == "X"].iloc[0]
    assert x["start_year"] == 2019 and x["end_year"] == 2021
    assert x["total_change"] == -10.0


def test_compute_state_prevalence_change_skips_missing_end_year():
    state_prev = pd.DataFrame(
        {
            "year": [2020, 2021],
            "state": ["Z", "Z"],
            "prevalence_pct": [5.0, 6.0],
            "sample_size": [1, 1],
        }
    )
    out = compute_state_prevalence_change(
        state_prev, ["Z"], start_year=2020, end_year=2023
    )
    assert out.empty
