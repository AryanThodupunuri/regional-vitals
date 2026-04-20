"""region_mapping.py

Provides a simple mapping of U.S. Census-style regions used by the project.
Adjust as needed for your project's definitions.
"""

REGIONS = {
    "Northeast": [
        "CT","ME","MA","NH","RI","VT","NJ","NY","PA"
    ],
    "Midwest": [
        "IL","IN","MI","OH","WI","IA","KS","MN","MO","NE","ND","SD"
    ],
    "Southeast": [
        "DE","DC","FL","GA","MD","NC","SC","VA","WV","AL","KY","MS","TN","AR","LA"
    ],
    "Southwest": [
        "AZ","NM","OK","TX"
    ],
    "West": [
        "AK","CA","CO","HI","ID","MT","NV","OR","UT","WA","WY"
    ]
}

# Reverse lookup: state -> region
STATE_TO_REGION = {}
for region, states in REGIONS.items():
    for s in states:
        STATE_TO_REGION[s] = region

# U.S. territories / non-state codes that appear in BRFSS data but should be
# excluded from state-level analyses.
TERRITORIES = {"GU", "PR", "VI", "AS", "MP", "US"}

# All valid state abbreviations (union of every region list)
VALID_STATES = set(STATE_TO_REGION.keys())


def filter_states_only(df, state_col="state"):
    """Remove rows whose state code is a territory or not in VALID_STATES.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with a column containing two-letter state/territory codes.
    state_col : str
        Name of the column that holds state abbreviations.

    Returns
    -------
    pandas.DataFrame
        Copy of *df* with territory / non-state rows dropped.
    """
    return df[df[state_col].isin(VALID_STATES)].copy()
