import pandas as pd

REQUIRED_COLUMNS = [
    "Ecosystem/Croptype",
    "Geolocation",
    "Year",
    "Semester",
    "Level",
    "AreaHarvested",
    "Production",
    "Yield"
]

REGION_NAME_MAP = {
    "BANGSAMORO AUTONOMOUS REGION IN MUSLIM MINDANAO (BARMM)": "BARMM",
    "CORDILLERA ADMINISTRATIVE REGION (CAR)":                  "CAR",
    "MIMAROPA REGION":                                         "MIMAROPA",
    "REGION I (ILOCOS REGION)":                               "Region I",
    "REGION II (CAGAYAN VALLEY)":                             "Region II",
    "REGION III (CENTRAL LUZON)":                             "Region III",
    "REGION IV-A (CALABARZON)":                               "Region IV-A",
    "REGION V (BICOL REGION)":                                "Region V",
    "REGION VI (WESTERN VISAYAS)":                            "Region VI",
    "REGION VII (CENTRAL VISAYAS)":                           "Region VII",
    "REGION VIII (EASTERN VISAYAS)":                          "Region VIII",
    "REGION IX (ZAMBOANGA PENINSULA)":                        "Region IX",
    "REGION X (NORTHERN MINDANAO)":                           "Region X",
    "REGION XI (DAVAO REGION)":                               "Region XI",
    "REGION XII (SOCCSKSARGEN)":                              "Region XII",
    "REGION XIII (CARAGA)":                                   "Region XIII",
}

# Level hierarchy: coarsest → finest
_COARSE = ("National", "Region", "Province", "Municipal", "Municipality")
_FINE   = ("Municipal", "Municipality", "Province", "Region", "National")

# Human-readable plural labels per level
_LOCATION_PLURAL = {
    "National":    "National Entries",
    "Region":      "Regions",
    "Province":    "Provinces",
    "Municipal":   "Municipalities",
    "Municipality": "Municipalities",
}


def _pick_level(available: set, order: tuple):
    for level in order:
        if level in available:
            return level
    return next(iter(available), None)


# ─────────────────────────────────────────────
# 1. LOAD AND VALIDATE
# ─────────────────────────────────────────────

def load_and_validate(file, column_mapping=None):
    """
    Reads CSV or Excel (.xlsx/.xls) and checks all required columns exist.
    If column_mapping is provided, renames columns first.
    Returns the raw DataFrame if valid.
    """
    try:
        name = getattr(file, "name", "")
        if name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(file, na_values=["..", "#DIV/0!"])
        else:
            df = pd.read_csv(file, na_values=["..", "#DIV/0!"])
    except Exception as e:
        return None, False, f"Could not read file: {e}"

    if column_mapping:
        rename_map = {
            uploaded: required
            for uploaded, required in column_mapping.items()
            if required in REQUIRED_COLUMNS
        }
        df = df.rename(columns=rename_map)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return None, False, f"Missing columns: {missing}"

    if df.empty:
        return None, False, "File is empty."

    return df, True, "File loaded successfully."


# ─────────────────────────────────────────────
# 2. CLEAN DATA
# ─────────────────────────────────────────────

SEMESTER_MAP = {1: "Wet Season", 2: "Dry Season"}


def clean_data(df):
    """
    Standardizes the raw DataFrame:
    - Renames columns to clean snake_case
    - Maps Semester 1/2 to Wet/Dry Season
    - Strips whitespace from text columns
    - Drops duplicates and nulls
    - Ensures correct data types
    """
    df = df.rename(columns={
        "Ecosystem/Croptype": "ecosystem",
        "Geolocation":        "location",
        "Year":               "year",
        "Semester":           "semester",
        "Level":              "level",
        "AreaHarvested":      "area_harvested",
        "Production":         "production",
        "Yield":              "yield"
    })

    df["ecosystem"] = df["ecosystem"].str.strip()
    df["location"]  = df["location"].str.strip()
    df["level"]     = df["level"].str.strip()

    df["location"] = df["location"].replace(REGION_NAME_MAP)
    df["semester"] = df["semester"].map(SEMESTER_MAP)

    df = df.drop_duplicates()
    df = df.dropna(subset=["yield", "production", "area_harvested"])
    df = df.reset_index(drop=True)

    df["year"]           = df["year"].astype(int)
    df["area_harvested"] = df["area_harvested"].astype(float)
    df["production"]     = df["production"].astype(float)
    df["yield"]          = df["yield"].astype(float)

    return df


# ─────────────────────────────────────────────
# 3. SUMMARY STATS
# ─────────────────────────────────────────────

def _weighted_avg(group):
    return (group["yield"] * group["area_harvested"]).sum() / group["area_harvested"].sum()


def get_summary_stats(df):
    """
    Extracts key statistics from the cleaned DataFrame.
    Adapts to whatever geographic level is available in the data.
    """
    available = set(df["level"].unique())

    # Coarsest level for overall/national averages
    level_filter = _pick_level(available, _COARSE)

    # Finest level for location rankings
    fine_level = _pick_level(available, _FINE)

    # Best available ecosystem
    eco_filter = "Palay" if "Palay" in df["ecosystem"].unique() else df["ecosystem"].iloc[0]

    # Overall yield trend at the coarsest level
    national = df[
        (df["level"] == level_filter) &
        (df["ecosystem"] == eco_filter)
    ]

    if level_filter in ("Province", "Municipal", "Municipality"):
        national_avg = national.groupby("year").apply(
            _weighted_avg, include_groups=False
        ).reset_index()
        national_avg.columns = ["year", "yield"]
    else:
        national_avg = national.groupby("year")["yield"].mean().reset_index()

    # Top / bottom locations at finest granularity
    if fine_level and fine_level != "National":
        loc_data = df[
            (df["level"] == fine_level) &
            (df["ecosystem"] == eco_filter)
        ]
        if not loc_data.empty:
            location_avg = loc_data.groupby("location").apply(
                _weighted_avg, include_groups=False
            ).round(2)
            top_5    = location_avg.nlargest(5).to_dict()
            bottom_5 = location_avg.nsmallest(5).to_dict()
        else:
            top_5 = {}
            bottom_5 = {}
    else:
        top_5    = {}
        bottom_5 = {}

    # Ecosystem averages
    irrigated = df[df["ecosystem"] == "Irrigated Palay"]
    rainfed   = df[df["ecosystem"] == "Rainfed Palay"]

    irrigated_avg = round(
        (irrigated["yield"] * irrigated["area_harvested"]).sum() /
        irrigated["area_harvested"].sum(), 2
    ) if not irrigated.empty else "N/A"

    rainfed_avg = round(
        (rainfed["yield"] * rainfed["area_harvested"]).sum() /
        rainfed["area_harvested"].sum(), 2
    ) if not rainfed.empty else "N/A"

    # Seasonal averages
    wet = df[df["semester"] == "Wet Season"]
    dry = df[df["semester"] == "Dry Season"]

    wet_avg = round(
        (wet["yield"] * wet["area_harvested"]).sum() /
        wet["area_harvested"].sum(), 2
    ) if not wet.empty else "N/A"

    dry_avg = round(
        (dry["yield"] * dry["area_harvested"]).sum() /
        dry["area_harvested"].sum(), 2
    ) if not dry.empty else "N/A"

    # Best / worst year
    if not national_avg.empty:
        best_year  = int(national_avg.loc[national_avg["yield"].idxmax(), "year"])
        worst_year = int(national_avg.loc[national_avg["yield"].idxmin(), "year"])
        avg_yield  = round(national_avg["yield"].mean(), 2)
        max_yield  = round(national_avg["yield"].max(), 2)
        min_yield  = round(national_avg["yield"].min(), 2)
    else:
        best_year  = "N/A"
        worst_year = "N/A"
        avg_yield  = "N/A"
        max_yield  = "N/A"
        min_yield  = "N/A"

    # Count of finest-level locations
    if fine_level:
        location_count = df[df["level"] == fine_level]["location"].nunique()
    else:
        location_count = 0

    return {
        # General
        "year_range":      f"{df['year'].min()} - {df['year'].max()}",
        "total_records":   len(df),
        "provinces":       location_count,
        "location_label":  _LOCATION_PLURAL.get(fine_level, "Locations"),
        "regions":         df[df["level"] == "Region"]["location"].nunique(),

        # Yield stats
        "national_avg_yield": avg_yield,
        "national_max_yield": max_yield,
        "national_min_yield": min_yield,
        "best_year":          best_year,
        "worst_year":         worst_year,

        # Ecosystem
        "irrigated_avg_yield": irrigated_avg,
        "rainfed_avg_yield":   rainfed_avg,

        # Seasonal
        "wet_season_avg": wet_avg,
        "dry_season_avg": dry_avg,

        # Location rankings
        "top_5_provinces":    top_5,
        "bottom_5_provinces": bottom_5,
    }
