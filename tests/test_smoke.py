"""Smoke tests: verify that every src module can be imported."""
import importlib
import pytest


MODULES = [
    "src.utils",
    "src.region_mapping",
    "src.compute_prevalence",
    "src.trend_analysis",
    "src.preprocessing",
]


@pytest.mark.parametrize("mod", MODULES)
def test_import(mod):
    importlib.import_module(mod)


def test_state_to_region_populated():
    from src.region_mapping import STATE_TO_REGION
    assert len(STATE_TO_REGION) > 0, "STATE_TO_REGION should not be empty"


def test_compute_region_year_prevalence_signature():
    from src.trend_analysis import compute_region_year_prevalence
    import inspect
    sig = inspect.signature(compute_region_year_prevalence)
    assert "df" in sig.parameters
    assert "measure" in sig.parameters
