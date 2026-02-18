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
    "SouthEast": [
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
