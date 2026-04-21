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

#Load and Validate
def load_and_validate(file, column_mapping=None):
    """
    Reads CSV and checks all required columns exist.
    If column_mapping is provided, renames columns first.
    Returns the raw DataFrame if valid.
    """
    try:
        df = pd.read_csv(file, na_values=["..","#DIV/0!"])
    except Exception as e:
        return None, False, f"Could not read file: {e}"

    # Apply column mapping if provided
    if column_mapping:
        rename_map = {
            uploaded: required
            for uploaded, required in column_mapping.items()
            if required in REQUIRED_COLUMNS
        }
        df = df.rename(columns=rename_map)

    # Check for missing columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return None, False, f"Missing columns: {missing}"

    # Check file isn't empty
    if df.empty:
        return None, False, "File is empty."

    return df, True, "File loaded successfully."

# ─────────────────────────────────────────────
# 2. CLEAN DATA
# ─────────────────────────────────────────────

SEMESTER_MAP = {
    1: "Wet Season",
    2: "Dry Season"
}

def clean_data(df):
    """
    Standardizes the raw DataFrame:
    - Renames columns to clean snake_case
    - Maps Semester 1/2 to Wet/Dry Season
    - Strips whitespace from text columns
    - Drops duplicates and nulls
    - Ensures correct data types
    """
    # Rename columns to clean snake_case
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

    # Strip whitespace from text columns
    df["ecosystem"] = df["ecosystem"].str.strip()
    df["location"]  = df["location"].str.strip()
    df["level"]     = df["level"].str.strip()

    # Clean up region names
    df["location"] = df["location"].replace(REGION_NAME_MAP)

    # Map semester numbers to readable labels
    df["semester"] = df["semester"].map(SEMESTER_MAP)

    # Drop duplicates
    df = df.drop_duplicates()

    # Drop rows where key numeric columns are null
    df = df.dropna(subset=["yield", "production", "area_harvested"])
    df = df.reset_index(drop=True)

    # Ensure correct data types
    df["year"]          = df["year"].astype(int)
    df["area_harvested"] = df["area_harvested"].astype(float)
    df["production"]    = df["production"].astype(float)
    df["yield"]         = df["yield"].astype(float)

    return df
# ─────────────────────────────────────────────
# 3. SUMMARY STATS
# ─────────────────────────────────────────────

def get_summary_stats(df):
    """
    Extracts key statistics from the cleaned DataFrame.
    Adapts to whatever data is available after filtering.
    """
    # Best available level for national stats
    if "National" in df["level"].unique():
        level_filter = "National"
    elif "Region" in df["level"].unique():
        level_filter = "Region"
    else:
        level_filter = "Province"

    # Best available ecosystem for overall stats
    if "Palay" in df["ecosystem"].unique():
        eco_filter = "Palay"
    else:
        eco_filter = df["ecosystem"].iloc[0]

    # National/overall stats
    national = df[
        (df["level"] == level_filter) &
        (df["ecosystem"] == eco_filter)
    ]

    # Weighted average at province level
    if level_filter == "Province":
        national_avg = national.groupby("year").apply(
            lambda x: (x["yield"] * x["area_harvested"]).sum() /
            x["area_harvested"].sum()
        ).reset_index()
        national_avg.columns = ["year", "yield"]
    else:
        national_avg = national.groupby("year")["yield"].mean().reset_index()

    # Top and bottom provinces
    if "Province" in df["level"].unique():
        provincial = df[
            (df["level"] == "Province") &
            (df["ecosystem"] == eco_filter)
        ]
        province_avg = provincial.groupby("location").apply(
            lambda x: (x["yield"] * x["area_harvested"]).sum() /
            x["area_harvested"].sum()
        ).round(2)
        top_5    = province_avg.nlargest(5).to_dict()
        bottom_5 = province_avg.nsmallest(5).to_dict()
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

    # Safe best/worst year extraction
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

    stats = {
        # General
        "year_range":    f"{df['year'].min()} - {df['year'].max()}",
        "total_records": len(df),
        "provinces":     df[df["level"] == "Province"]["location"].nunique(),
        "regions":       df[df["level"] == "Region"]["location"].nunique(),

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

        # Provincial
        "top_5_provinces":    top_5,
        "bottom_5_provinces": bottom_5,
    }

    return stats