import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def is_chart_empty(fig):
    """
    Checks if a Plotly figure is an empty state chart
    by looking for the 'not available' or 'insufficient'
    annotations we add when data is missing.
    Returns True if chart has no real data.
    """
    if not fig.data:
        return True

    # Check annotations for empty state messages
    empty_keywords = [
        "unavailable",
        "insufficient",
        "not available",
        "requires",
        "not enough"
    ]

    for annotation in fig.layout.annotations:
        text = annotation.text.lower()
        if any(keyword in text for keyword in empty_keywords):
            return True

    return False

# ─────────────────────────────────────────────
# 1. NATIONAL YIELD TREND OVER TIME
# ─────────────────────────────────────────────

def plot_yield_trend(df):
    """
    Line chart showing average rice yield per year.
    Adapts to available geographic levels in filtered data.
    Falls back from National → Region → Province automatically.
    """
    # Smart fallback — use best available level
    if "National" in df["level"].unique():
        level_filter = "National"
        label = "National Average"
    elif "Region" in df["level"].unique():
        level_filter = "Region"
        label = "Regional Average"
    else:
        level_filter = "Province"
        label = "Provincial Average"

    # Filter to best available level, Palay only
    # If Palay not available use whatever ecosystem is present
    if "Palay" in df["ecosystem"].unique():
        eco_filter = "Palay"
    else:
        eco_filter = df["ecosystem"].iloc[0]

    filtered = df[
    (df["level"] == level_filter) &
    (df["ecosystem"] == eco_filter)
    ]

    # Use weighted average when at province level

    if level_filter == "Province":
        filtered = filtered.groupby("year").apply(
            lambda x: (x["yield"] * x["area_harvested"]).sum() /
            x["area_harvested"].sum()
        ).reset_index()
        filtered.columns = ["year", "yield"]
    else:
        filtered = filtered.groupby("year")["yield"].mean().reset_index()

    # Final fallback if still empty
    
    if filtered.empty:
        filtered = df.groupby("year").apply(
            lambda x: (x["yield"] * x["area_harvested"]).sum() /
            x["area_harvested"].sum()
        ).reset_index()
        filtered.columns = ["year", "yield"]
        label = "Weighted Average"

    # Identify best and worst years
    best_year  = filtered.loc[filtered["yield"].idxmax()]
    worst_year = filtered.loc[filtered["yield"].idxmin()]

    # Build line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=filtered["year"],
        y=filtered["yield"],
        mode="lines+markers",
        name=label,
        line=dict(color="#2ecc71", width=3),
        marker=dict(size=7)
    ))

    # Annotate best year
    fig.add_annotation(
        x=best_year["year"],
        y=best_year["yield"],
        text=f"Peak: {best_year['yield']:.2f} MT/ha ({int(best_year['year'])})",
        showarrow=True,
        arrowhead=2,
        bgcolor="#2ecc71",
        font=dict(color="white"),
        arrowcolor="#2ecc71"
    )

    # Annotate worst year
    fig.add_annotation(
        x=worst_year["year"],
        y=worst_year["yield"],
        text=f"Lowest: {worst_year['yield']:.2f} MT/ha ({int(worst_year['year'])})",
        showarrow=True,
        arrowhead=2,
        bgcolor="#e74c3c",
        font=dict(color="white"),
        arrowcolor="#e74c3c"
    )

    fig.update_layout(
        title=f"Rice Yield Trend — {label} ({filtered['year'].min()}-{filtered['year'].max()})",
        xaxis_title="Year",
        yaxis_title="Yield (MT/ha)",
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=False
    )

    return fig
# ─────────────────────────────────────────────
# 2. ECOSYSTEM COMPARISON
# ─────────────────────────────────────────────

def plot_ecosystem_comparison(df):
    """
    Box plot comparing yield distributions across
    Irrigated Palay and Rainfed Palay.
    Adapts to available geographic levels.
    Excludes aggregate Palay to avoid double counting.
    """
    # Exclude aggregate Palay
    filtered = df[
        df["ecosystem"].isin(["Irrigated Palay", "Rainfed Palay"])
    ]

    # Smart fallback — use best available level
    if "Province" in filtered["level"].unique():
        filtered = filtered[filtered["level"] == "Province"]
        label = "Province Level"
    elif "Region" in filtered["level"].unique():
        filtered = filtered[filtered["level"] == "Region"]
        label = "Region Level"
    else:
        label = "All Levels"

    # Check if both ecosystems still exist after filtering
    available_ecosystems = filtered["ecosystem"].unique().tolist()

    if filtered.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            title="Ecosystem Comparison — Insufficient Data",
            annotations=[dict(
                text="No ecosystem data available for current filters.",
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    color_map = {
        "Irrigated Palay": "#2ecc71",
        "Rainfed Palay":   "#e67e22"
    }

    fig = px.box(
        filtered,
        x="ecosystem",
        y="yield",
        color="ecosystem",
        color_discrete_map=color_map,
        title=f"Yield Distribution — Irrigated vs Rainfed ({label})",
        labels={
            "yield":     "Yield (MT/ha)",
            "ecosystem": "Crop Type"
        },
        points="outliers"
    )

    fig.update_layout(
        plot_bgcolor="white",
        showlegend=False
    )

    return fig
# ─────────────────────────────────────────────
# 3. WET VS DRY SEASON ANALYSIS
# ─────────────────────────────────────────────

def plot_seasonal_analysis(df):
    """
    Line chart comparing Wet Season vs Dry Season
    average yield per year.
    Adapts to available geographic levels.
    Shows message if only one season is available.
    """
    # Smart fallback — use best available level
    if "National" in df["level"].unique():
        level_filter = "National"
        label = "National"
    elif "Region" in df["level"].unique():
        level_filter = "Region"
        label = "Regional"
    else:
        level_filter = "Province"
        label = "Provincial"

    # Use Palay if available, otherwise use whatever is present
    if "Palay" in df["ecosystem"].unique():
        eco_filter = "Palay"
    else:
        eco_filter = df["ecosystem"].iloc[0]

    filtered = df[
        (df["level"] == level_filter) &
        (df["ecosystem"] == eco_filter)
    ]

    # Weighted average at province level
    if level_filter == "Province":
        seasonal = filtered.groupby(
            ["year", "semester"]
        ).apply(
            lambda x: (x["yield"] * x["area_harvested"]).sum() /
            x["area_harvested"].sum()
        ).reset_index()
        seasonal.columns = ["year", "semester", "yield"]
    else:
        seasonal = filtered.groupby(
            ["year", "semester"]
        )["yield"].mean().reset_index()

    # Check if empty
    if seasonal.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Seasonal Analysis — Insufficient Data",
            annotations=[dict(
                text="No seasonal data available for current filters.",
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Check available seasons
    available_seasons = seasonal["semester"].unique().tolist()

    if len(available_seasons) == 1:
        title_note = f"({available_seasons[0]} only)"
    else:
        title_note = "(Wet vs Dry)"

    fig = px.line(
        seasonal,
        x="year",
        y="yield",
        color="semester",
        markers=True,
        color_discrete_map={
            "Wet Season": "#3498db",
            "Dry Season": "#e74c3c"
        },
        title=f"Seasonal Yield Analysis {title_note} — {label} Level",
        labels={
            "yield":    "Yield (MT/ha)",
            "year":     "Year",
            "semester": "Season"
        }
    )

    fig.update_layout(
        plot_bgcolor="white",
        hovermode="x unified"
    )

    return fig
# ─────────────────────────────────────────────
# 4. REGIONAL YIELD HEATMAP
# ─────────────────────────────────────────────

def plot_regional_heatmap(df):
    """
    Heatmap showing average yield per region per year.
    Requires Region level data to render properly.
    Shows informative message if Region data unavailable.
    """
    # Check if Region level data exists
    if "Region" not in df["level"].unique():
        fig = go.Figure()
        fig.update_layout(
            title="Regional Yield Heatmap — Unavailable",
            annotations=[dict(
                text=(
                    "This chart requires Region level data. "
                    "Please include Region in your filters."
                ),
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Use Palay if available, otherwise use whatever is present
    if "Palay" in df["ecosystem"].unique():
        eco_filter = "Palay"
    else:
        eco_filter = df["ecosystem"].iloc[0]

    regional = df[
        (df["level"] == "Region") &
        (df["ecosystem"] == eco_filter)
    ].groupby(["location", "year"])["yield"].mean().reset_index()

    if regional.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Regional Yield Heatmap — Insufficient Data",
            annotations=[dict(
                text="No regional data available for current filters.",
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Pivot to matrix format
    pivot = regional.pivot(
        index="location",
        columns="year",
        values="yield"
    )

    fig = px.imshow(
        pivot,
        color_continuous_scale="YlGn",
        aspect="auto",
        title="Regional Rice Yield Heatmap",
        labels=dict(
            x="Year",
            y="Region",
            color="Yield (MT/ha)"
        )
    )

    fig.update_layout(
        plot_bgcolor="white",
        xaxis_nticks=20
    )

    return fig
# ─────────────────────────────────────────────
# 5. AREA HARVESTED VS YIELD
# ─────────────────────────────────────────────

def plot_area_vs_yield(df):
    """
    Scatter plot of Area Harvested vs Yield.
    Adapts to available geographic levels.
    Excludes aggregate Palay to avoid double counting.
    """
    # Exclude aggregate Palay
    filtered = df[
        df["ecosystem"].isin(["Irrigated Palay", "Rainfed Palay"])
    ]

    # Smart fallback — use best available level
    if "Province" in filtered["level"].unique():
        filtered = filtered[filtered["level"] == "Province"]
        label = "Province Level"
    elif "Region" in filtered["level"].unique():
        filtered = filtered[filtered["level"] == "Region"]
        label = "Region Level"
    else:
        label = "All Levels"

    # Check if empty
    if filtered.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Area Harvested vs Yield — Insufficient Data",
            annotations=[dict(
                text=(
                    "No data available for current filters. "
                    "Please include Irrigated or Rainfed Palay "
                    "in your ecosystem filter."
                ),
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Check available ecosystems for color mapping
    available = filtered["ecosystem"].unique().tolist()
    color_map = {}
    if "Irrigated Palay" in available:
        color_map["Irrigated Palay"] = "#2ecc71"
    if "Rainfed Palay" in available:
        color_map["Rainfed Palay"] = "#e67e22"

    fig = px.scatter(
        filtered,
        x="area_harvested",
        y="yield",
        color="ecosystem",
        color_discrete_map=color_map,
        opacity=0.5,
        title=f"Area Harvested vs Yield — {label}",
        labels={
            "area_harvested": "Area Harvested (ha)",
            "yield":          "Yield (MT/ha)",
            "ecosystem":      "Crop Type"
        },
        hover_data=["location", "year"]
    )

    fig.update_traces(marker=dict(size=5))

    fig.update_layout(
        plot_bgcolor="white",
        hovermode="closest"
    )

    return fig
# ─────────────────────────────────────────────
# 6. TOP 10 PROVINCES RANKING
# ─────────────────────────────────────────────

def plot_top_provinces(df):
    """
    Horizontal bar chart ranking top 10 and bottom 10
    provinces by average yield.
    Requires Province level data to render properly.
    Uses weighted average by area harvested.
    """
    # Check if Province level data exists
    if "Province" not in df["level"].unique():
        fig = go.Figure()
        fig.update_layout(
            title="Top & Bottom Provinces — Unavailable",
            annotations=[dict(
                text=(
                    "This chart requires Province level data. "
                    "Please include Province in your filters."
                ),
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Use Palay if available, otherwise use whatever is present
    if "Palay" in df["ecosystem"].unique():
        eco_filter = "Palay"
    else:
        eco_filter = df["ecosystem"].iloc[0]

    filtered = df[
        (df["level"] == "Province") &
        (df["ecosystem"] == eco_filter)
    ]

    if filtered.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Top & Bottom Provinces — Insufficient Data",
            annotations=[dict(
                text="No provincial data available for current filters.",
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Weighted average by area harvested per province
    province_avg = filtered.groupby("location").apply(
        lambda x: (x["yield"] * x["area_harvested"]).sum() /
        x["area_harvested"].sum()
    ).round(2).reset_index()
    province_avg.columns = ["location", "yield"]

    # Need at least 10 provinces for top/bottom 10
    # otherwise just show what's available
    n = min(10, len(province_avg) // 2)

    if n == 0:
        fig = go.Figure()
        fig.update_layout(
            title="Top & Bottom Provinces — Insufficient Data",
            annotations=[dict(
                text="Not enough provinces to rank. Please widen your filters.",
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Get top and bottom n provinces
    top_n    = province_avg.nlargest(n, "yield")
    bottom_n = province_avg.nsmallest(n, "yield")

    top_n["rank"]    = f"Top {n}"
    bottom_n["rank"] = f"Bottom {n}"

    combined = pd.concat([top_n, bottom_n]).sort_values(
        "yield", ascending=True
    )

    fig = px.bar(
        combined,
        x="yield",
        y="location",
        color="rank",
        orientation="h",
        color_discrete_map={
            f"Top {n}":    "#2ecc71",
            f"Bottom {n}": "#e74c3c"
        },
        title=f"Top & Bottom {n} Provinces by Average Yield",
        labels={
            "yield":    "Average Yield (MT/ha)",
            "location": "Province",
            "rank":     "Ranking"
        },
        text="yield"
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        plot_bgcolor="white",
        xaxis_title="Average Yield (MT/ha)",
        yaxis_title="Province",
        legend_title="Ranking",
        height=600
    )

    return fig

# ─────────────────────────────────────────────
# 7. 3D SURFACE PLOT — REGION × YEAR × YIELD
# ─────────────────────────────────────────────

def plot_3d_yield_surface(df):
    """
    3D Surface plot showing yield across regions and years.
    Requires Region level data to render properly.
    Shows informative message if Region data unavailable.
    """
    # Check if Region level data exists
    if "Region" not in df["level"].unique():
        fig = go.Figure()
        fig.update_layout(
            title="3D Yield Surface — Unavailable",
            annotations=[dict(
                text=(
                    "This chart requires Region level data. "
                    "Please include Region in your filters."
                ),
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Use Palay if available, otherwise use whatever is present
    if "Palay" in df["ecosystem"].unique():
        eco_filter = "Palay"
    else:
        eco_filter = df["ecosystem"].iloc[0]

    regional = df[
        (df["level"] == "Region") &
        (df["ecosystem"] == eco_filter)
    ].groupby(["location", "year"])["yield"].mean().reset_index()

    if regional.empty:
        fig = go.Figure()
        fig.update_layout(
            title="3D Yield Surface — Insufficient Data",
            annotations=[dict(
                text="No regional data available for current filters.",
                showarrow=False,
                font=dict(size=14),
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )]
        )
        return fig

    # Pivot to matrix format
    pivot = regional.pivot(
        index="location",
        columns="year",
        values="yield"
    ).fillna(0)

    years    = list(pivot.columns)
    regions  = list(pivot.index)
    z_values = pivot.values.tolist()

    fig = go.Figure(data=[go.Surface(
        z=z_values,
        x=years,
        y=regions,
        colorscale="YlGn",
        colorbar=dict(title="Yield (MT/ha)"),
        hovertemplate=(
            "Year: %{x}<br>"
            "Region: %{y}<br>"
            "Yield: %{z:.2f} MT/ha<extra></extra>"
        )
    )])

    fig.update_layout(
        title="3D Rice Yield Surface — Region × Year × Yield",
        scene=dict(
            xaxis=dict(title="Year"),
            yaxis=dict(title="Region"),
            zaxis=dict(title="Yield (MT/ha)"),
            camera=dict(
                eye=dict(x=1.8, y=-1.8, z=0.8)
            )
        ),
        height=650,
        margin=dict(l=0, r=0, t=50, b=0)
    )

    return fig