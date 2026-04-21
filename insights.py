import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

client = Groq(api_key=os.getenv("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"))
MODEL  = "llama-3.3-70b-versatile"


def build_filter_context(stats, filters):
    """
    Builds a human readable filter context string
    that gets injected into every AI prompt.
    """
    lines = [
        f"- Year range: {filters.get('year_range', stats['year_range'])}",
        f"- Ecosystem: {', '.join(filters.get('ecosystems', ['All ecosystems']))}",
        f"- Season: {', '.join(filters.get('semesters', ['All seasons']))}",
    ]
    return "\n".join(lines)
# ─────────────────────────────────────────────
# CORE FUNCTION — ASK GROQ
# ─────────────────────────────────────────────

def ask_groq(prompt, filter_context=""):
    """
    Sends a prompt to Groq and returns the response text.
    Injects filter context into system prompt if provided.
    """
    system_content = (
        "You are a senior agricultural data analyst and researcher "
        "specializing in Philippine rice production with deep knowledge "
        "of Philippine agricultural history, climate patterns, and policy. "
        "\n\n"
        "When analyzing data you must: \n"
        "1. Explain not just WHAT happened but WHY it happened\n"
        "2. Identify specific possible factors — climate events, "
        "policy changes, infrastructure, technology adoption\n"
        "3. Reference real events where relevant — typhoons, "
        "El Niño/La Niña episodes, government programs\n"
        "4. Cite only these verified sources when referencing "
        "external information: PSA (Philippine Statistics Authority), "
        "PhilRice (Philippine Rice Research Institute), "
        "IRRI (International Rice Research Institute), "
        "PAGASA (Philippine weather agency), "
        "DA (Department of Agriculture), "
        "FAO (Food and Agriculture Organization)\n"
        "5. Write in 4-6 sentences in a professional but accessible tone\n"
        "6. Never use bullet points — always write in paragraph form\n"
        "7. Always refer to yield in MT/ha units\n"
        "8. Always acknowledge the active filters at the start of "
        "your analysis so the reader knows what data was analyzed"
    )

    if filter_context:
        system_content += f"\n\nActive filters applied to this analysis:\n{filter_context}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Insight unavailable: {e}"
    
# ─────────────────────────────────────────────
# 1. YIELD TREND — FULL REPORT
# ─────────────────────────────────────────────

def insight_yield_trend(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    prompt = f"""
    Write a full analytical report section on national rice
    yield trends in the Philippines from {stats['year_range']}.

    Data:
    - Period average yield: {stats['national_avg_yield']} MT/ha
    - Peak yield: {stats['national_max_yield']} MT/ha
      in {stats['best_year']}
    - Lowest yield: {stats['national_min_yield']} MT/ha
      in {stats['worst_year']}

    Write exactly 4 detailed paragraphs:

    Paragraph 1 — Overall trend:
    Describe the upward trajectory from {stats['worst_year']}
    to {stats['best_year']}. Quantify the improvement percentage.
    Explain the key drivers — adoption of high yielding varieties
    developed by PhilRice and IRRI, expansion of irrigation
    infrastructure by NIA, and government programs like the
    Rice Competitiveness Enhancement Fund (RCEF).

    Paragraph 2 — The 2009 dip:
    Explain Typhoon Ondoy in detail — date of landfall
    September 26 2009, areas flooded, timing during grain
    filling stage, estimated agricultural damage, and why
    Central Luzon was most affected. Explain why dry season
    2010 was also suppressed due to damaged irrigation
    infrastructure and lost farmer capital.

    Paragraph 3 — Peak performance {stats['best_year']}:
    Explain what contributed to the peak year — favorable
    climate conditions, widespread adoption of improved seed
    varieties, expanded irrigation coverage, and the impact
    of DA agricultural support programs.

    Paragraph 4 — Policy implications:
    What does this trend mean for Philippine food security,
    rice import dependency, and future agricultural investment
    priorities? Reference the Rice Tariffication Law of 2019
    and its implications.

    Cite PSA, DA, PAGASA, PhilRice, IRRI where relevant.
    Write in formal analytical tone suitable for a government report.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)


# ─────────────────────────────────────────────
# 2. ECOSYSTEM — FULL REPORT
# ─────────────────────────────────────────────

def insight_ecosystem(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    irrigated = stats['irrigated_avg_yield']
    rainfed   = stats['rainfed_avg_yield']

    if irrigated != "N/A" and rainfed != "N/A":
        gap = round(irrigated - rainfed, 2)
        gap_line = f"Yield gap: {gap} MT/ha ({round((gap/rainfed)*100, 1)}% advantage)"
    elif irrigated == "N/A":
        gap_line = "Irrigated Palay data not available in current filters"
    elif rainfed == "N/A":
        gap_line = "Rainfed Palay data not available in current filters"
    else:
        gap_line = "Both ecosystem types unavailable in current filters"

    prompt = f"""
    Write a full analytical report section on the yield
    difference between irrigated and rainfed rice farming
    in the Philippines from {stats['year_range']}.

    Data:
    - Irrigated Palay average yield: {irrigated} MT/ha
    - Rainfed Palay average yield: {rainfed} MT/ha
    - {gap_line}

    Write exactly 4 detailed paragraphs:

    Paragraph 1 — The yield gap:
    Quantify and contextualize the gap between irrigated
    and rainfed systems. Explain why this gap exists —
    water control enabling precise nutrient management,
    ability to plant multiple cropping cycles per year,
    and reduced climate risk exposure.

    Paragraph 2 — Geographic vulnerability:
    Identify which Philippine regions are most dependent
    on rainfed farming — Visayas, parts of Mindanao,
    upland areas. Discuss how this dependence creates
    food security vulnerability during drought years
    and El Niño episodes.

    Paragraph 3 — Infrastructure investment:
    Discuss the role of NIA irrigation systems in driving
    irrigated farm productivity. Explain why Central Luzon
    leads — it has the most developed irrigation network.
    Cite specific NIA coverage statistics where possible.

    Paragraph 4 — Policy recommendations:
    What investments would most effectively close the gap?
    Discuss small scale irrigation, AWD (Alternate Wetting
    and Drying) technology from IRRI, and DA support programs
    for rainfed farmers.

    Cite IRRI, PhilRice, NIA, DA where relevant.
    Write in formal analytical tone suitable for a government report.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)


# ─────────────────────────────────────────────
# 3. SEASONAL — FULL REPORT
# ─────────────────────────────────────────────

def insight_seasonal(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    prompt = f"""
    Write a full analytical report section on wet season
    vs dry season rice yield patterns in the Philippines
    from {stats['year_range']}.

    Data:
    - Wet season average: {stats['wet_season_avg']} MT/ha
    - Dry season average: {stats['dry_season_avg']} MT/ha
    - Note: N/A means that season was excluded by filters

    Write exactly 4 detailed paragraphs:

    Paragraph 1 — Seasonal patterns overview:
    Describe the surprisingly close performance between
    wet and dry seasons. Explain the Philippine rice
    calendar — wet season June to November, dry season
    December to May. Discuss why dry season slightly
    outperforms despite no rainfall.

    Paragraph 2 — Role of irrigation in dry season:
    Explain how irrigation infrastructure compensates
    for absent rainfall in dry season. Discuss why
    irrigated provinces maintain high yields year round
    while rainfed provinces show dramatic seasonal drops.

    Paragraph 3 — Climate variability impacts:
    Explain how El Niño suppresses wet season yields
    through drought during flowering stage, while
    La Niña causes flooding damage during harvest.
    Reference specific PAGASA documented episodes
    — 2010 La Niña, 2016 El Niño.

    Paragraph 4 — Seasonal risk management:
    What strategies do farmers and DA use to manage
    seasonal risk? Discuss crop insurance, early warning
    systems from PAGASA, and stress tolerant varieties
    from PhilRice.

    Cite PAGASA, IRRI, PhilRice, DA where relevant.
    Write in formal analytical tone suitable for a government report.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)


# ─────────────────────────────────────────────
# 4. REGIONAL — FULL REPORT
# ─────────────────────────────────────────────

def insight_regional(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    prompt = f"""
    Write a full analytical report section on regional
    rice yield performance across the Philippines
    from {stats['year_range']}.

    Data:
    - Regions analyzed: {stats['regions']}
    - Top 5 provinces: {stats['top_5_provinces']}
    - Bottom 5 provinces: {stats['bottom_5_provinces']}

    Write exactly 4 detailed paragraphs:

    Paragraph 1 — Central Luzon dominance:
    Explain specifically why Central Luzon consistently
    leads — NIA irrigation systems covering the Pampanga
    River basin, flat fertile plains ideal for mechanized
    farming, proximity to Manila markets, strong agricultural
    extension services, and concentration of PhilRice
    research stations.

    Paragraph 2 — High performing regions:
    Discuss Cagayan Valley and Ilocos Region as strong
    performers. Explain their geographic and infrastructural
    advantages — river systems, irrigation coverage,
    farming culture.

    Paragraph 3 — Underperforming regions:
    Explain the persistently low yields in BARMM —
    conflict history limiting infrastructure investment,
    geographic isolation of island provinces like
    Sulu and Tawi-Tawi, limited irrigation coverage,
    and fragmented landholdings. Discuss the Davao
    Occidental anomaly as a data artifact from
    its recent creation as a province in 2013.

    Paragraph 4 — Closing the regional gap:
    What targeted investments would most effectively
    improve yields in underperforming regions?
    Discuss DA regional programs, peace and development
    initiatives in BARMM, and island connectivity.

    Cite PSA, DA, NIA, IRRI where relevant.
    Write in formal analytical tone suitable for a government report.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)


# ─────────────────────────────────────────────
# 5. AREA VS YIELD — FULL REPORT
# ─────────────────────────────────────────────

def insight_area_vs_yield(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    prompt = f"""
    Write a full analytical report section on the
    relationship between farm area harvested and rice
    yield in the Philippines from {stats['year_range']}.

    Data:
    - Most provinces: 0 to 20,000 hectares
    - Irrigated average yield: {stats['irrigated_avg_yield']} MT/ha
    - Rainfed average yield: {stats['rainfed_avg_yield']} MT/ha

    Write exactly 4 detailed paragraphs:

    Paragraph 1 — Farm size distribution:
    Describe the clustering of Philippine rice farms
    in the 0 to 20,000 hectare range. Explain the
    historical context — land reform programs, the
    Comprehensive Agrarian Reform Program (CARP),
    and how landholding fragmentation came to define
    Philippine rice agriculture.

    Paragraph 2 — Scale vs productivity:
    Explain why farm size does not strongly predict yield.
    Discuss how small irrigated farms in Nueva Ecija
    consistently outperform large rainfed farms elsewhere.
    The key determinant is water access and input quality,
    not scale.

    Paragraph 3 — Mechanization challenges:
    Discuss how fragmented smallholder farms limit
    mechanization adoption. Explain DA's farm consolidation
    and mechanization programs and their challenges.
    Reference IRRI research on optimal farm size for
    mechanized rice production.

    Paragraph 4 — Future of farm structure:
    Discuss the tension between land reform social goals
    and agricultural productivity goals. What models —
    cooperative farming, contract growing, farm clusters —
    could improve productivity while respecting land rights?

    Cite IRRI, DA, PSA Census of Agriculture where relevant.
    Write in formal analytical tone suitable for a government report.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)


# ─────────────────────────────────────────────
# 6. TOP PROVINCES — FULL REPORT
# ─────────────────────────────────────────────

def insight_top_provinces(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    prompt = f"""
    Write a full analytical report section on top and
    bottom performing provinces for rice yield in the
    Philippines from {stats['year_range']}.

    Data:
    - Top 5 provinces: {stats['top_5_provinces']}
    - Bottom 5 provinces: {stats['bottom_5_provinces']}
    - Total provinces: {stats['provinces']}

    Write exactly 4 detailed paragraphs:

    Paragraph 1 — Top performers:
    Analyze what makes the top provinces excel. Focus on
    Nueva Ecija as the undisputed leader — explain its
    NIA irrigation coverage, soil quality in the Cagayan
    and Pampanga river basins, strong farming cooperatives,
    and proximity to PhilRice research stations. Discuss
    other top performers and their specific advantages.

    Paragraph 2 — Bottom performers:
    Analyze the bottom provinces with nuance. Distinguish
    between genuinely low productivity provinces —
    Sulu, Tawi-Tawi due to conflict and isolation —
    and data artifacts like Davao Occidental which was
    only created as a province in 2013 giving it fewer
    data years and artificially low averages.

    Paragraph 3 — The productivity gap:
    Quantify the gap between top and bottom performers.
    Discuss whether this gap has widened or narrowed
    over the 20 year period. Explain what structural
    factors make it persistent — geography, peace and
    order, infrastructure investment history.

    Paragraph 4 — Targeted interventions:
    What specific investments would most help bottom
    performing provinces? Discuss small scale irrigation,
    seed subsidy programs, agricultural extension services,
    and peace and development programs for conflict
    affected areas.

    Cite PSA provincial data, DA, NIA where relevant.
    Write in formal analytical tone suitable for a government report.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)


# ─────────────────────────────────────────────
# 7. 3D SURFACE — FULL REPORT
# ─────────────────────────────────────────────

def insight_3d_surface(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    prompt = f"""
    Write a full analytical report section on the 3D
    rice yield surface showing regional performance
    across the Philippines from {stats['year_range']}.

    Data:
    - Regions analyzed: {stats['regions']}
    - Peak yield: {stats['national_max_yield']} MT/ha
      in {stats['best_year']}
    - Top 5 provinces: {stats['top_5_provinces']}
    - Bottom 5 provinces: {stats['bottom_5_provinces']}

    Write exactly 4 detailed paragraphs:

    Paragraph 1 — The yield landscape:
    Describe the overall shape of the Philippine rice
    yield landscape as seen in the 3D surface. Identify
    the prominent peaks — Central Luzon ridge — and
    the persistent valleys — BARMM, island provinces.
    Explain what this landscape reveals about agricultural
    inequality that flat charts cannot show.

    Paragraph 2 — Temporal dimension:
    Describe the upward slope from left to right —
    the overall improvement from 2000 to 2019.
    Identify the 2009 valley visible across most regions
    from Typhoon Ondoy. Discuss how the slope steepness
    varies by region — some regions improved rapidly
    while others stagnated.

    Paragraph 3 — Regional divergence:
    Discuss whether regions are converging or diverging
    in yield performance over time. Are top regions
    pulling further ahead or are lagging regions
    catching up? What does this mean for regional
    inequality in Philippine agriculture?

    Paragraph 4 — Policy implications:
    What does the 3D yield landscape tell policymakers
    about where to prioritize investment? Discuss
    targeted regional programs, infrastructure gaps,
    and the potential for yield improvement in
    currently underperforming regions.

    Cite PSA, DA, IRRI where relevant.
    Write in formal analytical tone suitable for a government report.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)


# ─────────────────────────────────────────────
# 8. EXECUTIVE SUMMARY — FULL REPORT
# ─────────────────────────────────────────────

def insight_executive_summary(stats, filters={}):
    filter_context = build_filter_context(stats, filters)
    prompt = f"""
    Write a professional executive summary of Philippine
    rice production performance from {stats['year_range']}.

    Data:
    - {stats['provinces']} provinces, {stats['regions']} regions
    - National average yield: {stats['national_avg_yield']} MT/ha
    - Yield range: {stats['national_min_yield']} to
      {stats['national_max_yield']} MT/ha
    - Best year: {stats['best_year']}
    - Worst year: {stats['worst_year']}
    - Irrigated vs Rainfed: {stats['irrigated_avg_yield']}
      vs {stats['rainfed_avg_yield']} MT/ha
    - Top province: Nueva Ecija at
      {list(stats['top_5_provinces'].values())[0]
        if stats['top_5_provinces'] else 'N/A'} MT/ha

    Write exactly 5 detailed paragraphs:

    Paragraph 1 — Filter context and scope:
    Clearly state what data was analyzed — year range,
    ecosystems, seasons, and geographic levels included.
    State the total records and coverage.

    Paragraph 2 — Overall performance:
    Summarize the national yield trajectory. Quantify
    improvement. Identify best and worst years with causes.
    Reference the Rice Tariffication Law and RCEF program.

    Paragraph 3 — Key disparities:
    Summarize the two most important gaps found —
    irrigated vs rainfed yield gap and regional disparity
    between Central Luzon and underperforming regions.

    Paragraph 4 — Climate vulnerability:
    Discuss the 2009 Typhoon Ondoy impact and what it
    reveals about climate vulnerability. Reference
    El Niño and La Niña effects on seasonal yields.

    Paragraph 5 — Recommendations:
    Provide 3 specific forward looking recommendations
    for improving Philippine rice production — irrigation
    expansion, targeted provincial programs, and
    climate resilient variety adoption.

    Write in formal executive tone suitable for senior
    government officials. Cite PSA, DA, IRRI, PhilRice,
    FAO where relevant.
    Never use bullet points — full paragraphs only.
    """
    return ask_groq(prompt, filter_context)
# ─────────────────────────────────────────────
# COLUMN MAPPING
# ─────────────────────────────────────────────

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

def map_columns(uploaded_columns: list) -> dict:
    """
    Sends uploaded CSV column names to Groq and asks it
    to map them to the required column names.
    Returns a dictionary mapping uploaded → required.
    """
    prompt = f"""
    I have a CSV file with these columns:
    {uploaded_columns}

    I need to map them to these required columns:
    {REQUIRED_COLUMNS}

    Rules:
    - Match based on meaning, not exact spelling
    - Every required column must be mapped to exactly
      one uploaded column
    - If a required column has no reasonable match,
      map it to null
    - Return ONLY a valid JSON object
    - No explanation, no markdown, no backticks
    - Format: {{"uploaded_column": "Required_Column"}}

    Example output:
    {{
        "Eco_Type": "Ecosystem/Croptype",
        "Province": "Geolocation",
        "Yr": "Year",
        "Sem": "Semester",
        "level": "Level",
        "Area": "AreaHarvested",
        "Prod": "Production",
        "Yld": "Yield"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a data engineering assistant. "
                        "You only respond with valid JSON. "
                        "Never include markdown, backticks, "
                        "or explanations of any kind."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        import json
        raw = response.choices[0].message.content.strip()
        mapping = json.loads(raw)
        return mapping

    except Exception as e:
        return None
    

# ─────────────────────────────────────────────
# MASTER FUNCTION — GET FULL SECTION
# Combines AI narrative + institutional sources
# ─────────────────────────────────────────────

def get_full_section(chart_key, stats, filters={}, fig=None):
    """
    Returns a complete report section containing:
    - Full AI narrative (3-4 paragraphs)
    - Institutional sources from sources.py

    If fig is provided and detected as empty,
    returns a not available message instead.
    """
    from sources import SOURCES
    from visualizations import is_chart_empty

    # Check if chart has real data
    if fig is not None and is_chart_empty(fig):
        return {
            "narrative": (
                f"This analysis is not available for the current filters. "
                f"The chart could not be generated because the selected filters "
                f"— {filters.get('level', 'selected level')}, "
                f"{', '.join(filters.get('ecosystems', ['selected ecosystems']))}, "
                f"{filters.get('year_range', 'selected year range')} "
                f"— do not contain sufficient data for this visualization. "
                f"Please adjust your filters to include the required data."
            ),
            "institutional": []
        }

    # Map chart keys to insight functions
    insight_functions = {
        "yield_trend":       insight_yield_trend,
        "ecosystem":         insight_ecosystem,
        "seasonal":          insight_seasonal,
        "regional":          insight_regional,
        "area_vs_yield":     insight_area_vs_yield,
        "top_provinces":     insight_top_provinces,
        "3d_surface":        insight_3d_surface,
        "executive_summary": insight_executive_summary,
    }

    # Get AI narrative
    narrative = insight_functions[chart_key](stats, filters)

    # Get institutional sources
    institutional = SOURCES.get(chart_key, [])

    return {
        "narrative":     narrative,
        "institutional": institutional
    }