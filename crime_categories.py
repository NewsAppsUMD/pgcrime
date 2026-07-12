"""
Canonical offense categorization for Prince George's County Daily Crime Reports.

Shared by the PDF parser, the timeseries builder, and the alert engine so that
every consumer agrees on which rows are real offenses, which are aggregate
totals, and which are parsing artifacts.
"""

VIOLENT_OFFENSES = [
    "Murder",
    "Sex Offense",
    "Rape",
    "Fondling",
    "Robbery",
    "Commercial Robbery",
    "Residential Robbery",
    "Citizen Robbery",
    "Carjacking",
    "Assault",
    "Non-Fatal Shooting",
    "Assault (Other Weapon)",
    "Assault (No Weapon)",
    "Domestic Violence",
    "DV Non-Fatal Shooting",
    "DV Assault (Other Weapon)",
    "DV Assault (No Weapon)",
]

PROPERTY_OFFENSES = [
    "Burglary",
    "Commercial Burglary",
    "Residential Burglary",
    "Other Burglary",
    "Larceny",
    "Theft from Auto",
    "Other Theft",
    "Stolen Vehicle",
]

# Aggregate rows published in the report (not individual offenses).
TOTAL_ROWS = [
    "Violent Crime Total",
    "Property Crime Total",
    "Total Crime",
]

# Offenses most likely to drive quick-turn stories; alerts treat these as
# higher priority and track streaks for them.
HEADLINE_OFFENSES = [
    "Murder",
    "Non-Fatal Shooting",
    "Carjacking",
    "Robbery",
]

# Granular breakdowns of a parent offense (e.g. "Commercial Robbery" under
# "Robbery"). Alerts about these are informational; the parent category is
# the story.
SUBTYPE_OFFENSES = [
    "Fondling",
    "Commercial Robbery",
    "Residential Robbery",
    "Citizen Robbery",
    "Assault (Other Weapon)",
    "Assault (No Weapon)",
    "DV Non-Fatal Shooting",
    "DV Assault (Other Weapon)",
    "DV Assault (No Weapon)",
    "Commercial Burglary",
    "Residential Burglary",
    "Other Burglary",
    "Theft from Auto",
    "Other Theft",
]


def is_junk_row(offense_type: str) -> bool:
    """The PDF repeats its section-header row mid-table ("DCR Offense -
    NON-VIOLENT"); the parser historically emitted it as a data row whose
    values are day-of-week strings."""
    return offense_type.strip().lower().startswith("dcr offense")


def categorize(offense_type: str) -> str:
    """Return 'violent', 'property', 'total', or 'other' for an offense row."""
    name = offense_type.strip()
    if name in TOTAL_ROWS:
        return "total"
    if name in VIOLENT_OFFENSES:
        return "violent"
    if name in PROPERTY_OFFENSES:
        return "property"
    return "other"


def clean_records(records):
    """Filter a report's crime_statistics down to trustworthy rows.

    Drops the section-header artifact, rows whose numeric fields came through
    as strings, and duplicate offense rows (the PDF repeats "Violent Crime
    Total" at the bottom of the non-violent section). Keeps first occurrence.
    """
    seen = set()
    cleaned = []
    for record in records:
        offense = (record.get("offense_type") or "").strip()
        if not offense or is_junk_row(offense):
            continue
        if not isinstance(record.get("seven_day_total"), int):
            continue
        if offense in seen:
            continue
        seen.add(offense)
        cleaned.append(record)
    return cleaned
