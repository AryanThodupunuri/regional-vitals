"""compute_prevalence.py

Simple helper to compute prevalence summaries from the combined BRFSS dataset.
"""

from pathlib import Path
import pandas as pd


def compute_state_prevalence(df: pd.DataFrame) -> pd.DataFrame:
    """Return a state-year-indicator prevalence table.

    Expects df with columns: year, state, measure, value, sample_size
    and computes a sample-size-weighted prevalence_pct.
    """
    required = ["year", "state", "measure", "value", "sample_size"]
    for r in required:
        if r not in df.columns:
            raise ValueError(f"DataFrame missing required column: {r}")
            
    out = df.copy()
    out["weighted"] = out["value"] * out["sample_size"]

    out = out.groupby(["year", "state", "measure"], as_index=False).agg(
        weighted_sum=("weighted", "sum"),
        sample_size=("sample_size", "sum"),
    )

    out["prevalence_pct"] = out["weighted_sum"] / out["sample_size"]

    out = out[["year", "state", "measure", "prevalence_pct", "sample_size"]]

    return out


def compute_state_prevalence_change(
    state_prev: pd.DataFrame,
    states: list[str],
    *,
    start_year: int | None = None,
    end_year: int | None = None,
    use_each_states_year_range: bool = False,
) -> pd.DataFrame:
    """Change in weighted prevalence between two years for selected states.

    Expects rows from :func:`compute_state_prevalence` (columns include
    ``year``, ``state``, ``prevalence_pct``). Optionally restricts each state
    to its earliest and latest *available* year in the table instead of
    fixed calendar years.

    Parameters
    ----------
    state_prev
        State–year prevalence table (one measure per table is typical).
    states
        State abbreviations in the order rows should appear (e.g. a region list).
    start_year, end_year
        Inclusive comparison window. Ignored if ``use_each_states_year_range``
        is True. If either is omitted (and per-state range is False), the
        table's overall min / max year is used for all states.
    use_each_states_year_range
        If True, use each state's min and max ``year`` in *state_prev* as the
        start and end year for that state.

    Returns
    -------
    DataFrame with columns:
        state, start_year, end_year, start_pct, end_pct, total_change
    States with no usable start/end pair are omitted.
    """
    required = {"year", "state", "prevalence_pct"}
    missing = required - set(state_prev.columns)
    if missing:
        raise ValueError(f"state_prev missing columns: {sorted(missing)}")

    sub = state_prev[state_prev["state"].isin(states)].copy()
    global_min = int(sub["year"].min()) if not sub.empty else None
    global_max = int(sub["year"].max()) if not sub.empty else None

    rows: list[dict] = []
    for state in states:
        g = sub[sub["state"] == state].sort_values("year")
        if g.empty:
            continue

        if use_each_states_year_range:
            sy = int(g["year"].min())
            ey = int(g["year"].max())
        else:
            sy = int(start_year) if start_year is not None else global_min
            ey = int(end_year) if end_year is not None else global_max

        start_row = g[g["year"] == sy]
        end_row = g[g["year"] == ey]
        if start_row.empty or end_row.empty:
            continue

        sv = float(start_row["prevalence_pct"].iloc[-1])
        ev = float(end_row["prevalence_pct"].iloc[-1])
        rows.append(
            {
                "state": state,
                "start_year": sy,
                "end_year": ey,
                "start_pct": round(sv, 2),
                "end_pct": round(ev, 2),
                "total_change": round(ev - sv, 2),
            }
        )

    return pd.DataFrame(rows)


def load_combined(path: Path) -> pd.DataFrame:
    """Load a combined BRFSS CSV into a DataFrame.

    Parameters
    ----------
    path : Path
        Path to the CSV (e.g. ``data/processed/brfss_combined_2011_2023.csv``).

    Returns
    -------
    pd.DataFrame
    """
    return pd.read_csv(path)
