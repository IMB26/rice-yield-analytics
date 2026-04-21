import streamlit as st
import pandas as pd
from data_processor import load_and_validate, clean_data, get_summary_stats
from visualizations import (
    plot_yield_trend,
    plot_ecosystem_comparison,
    plot_seasonal_analysis,
    plot_regional_heatmap,
    plot_area_vs_yield,
    plot_top_provinces,
    plot_3d_yield_surface
)
from insights import (
    map_columns,
    REQUIRED_COLUMNS,
    get_full_section
)
from pdf_generator import generate_report

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Rice Yield Analytics",
    page_icon="🌾",
    layout="wide"
)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.title("🌾 Philippine Rice Yield Analytics")
st.markdown("Upload a PSA rice production CSV to generate visualizations, AI insights, and a PDF report.")
st.divider()

# ─────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "Upload your PSA CSV file",
    type=["csv"],
    help="Expected columns: Ecosystem/Croptype, Geolocation, Year, Semester, Level, AreaHarvested, Production, Yield"
)

if uploaded_file is None:
    st.info("👆 Upload a CSV file to get started.")
    st.stop()

# ─────────────────────────────────────────────
# LOAD AND CLEAN DATA
# ─────────────────────────────────────────────

with st.spinner("Loading and validating data..."):
    peek = pd.read_csv(uploaded_file, nrows=0)
    uploaded_columns = list(peek.columns)

    exact_match = all(
        col in uploaded_columns for col in REQUIRED_COLUMNS
    )

    if exact_match:
        uploaded_file.seek(0)
        df, is_valid, message = load_and_validate(uploaded_file)
    else:
        st.info("⚙️ Detecting column structure using AI...")
        mapping = map_columns(uploaded_columns)

        if mapping is None:
            st.error(
                "❌ Could not automatically map columns. "
                "Please use the standard PSA CSV format."
            )
            st.stop()

        uploaded_file.seek(0)
        df, is_valid, message = load_and_validate(
            uploaded_file,
            column_mapping=mapping
        )
        st.success("✅ Columns mapped successfully using AI.")

if not is_valid:
    st.error(f"❌ {message}")
    st.stop()

with st.spinner("Cleaning data..."):
    df = clean_data(df)

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Official_Seal_of_the_Philippine_Statistics_Authority.png/200px-Official_Seal_of_the_Philippine_Statistics_Authority.png",
        width=80
    )
    st.title("⚙️ Filters")
    st.markdown("Customize your analysis below.")
    st.divider()

    min_year = int(df["year"].min())
    max_year = int(df["year"].max())

    year_range = st.slider(
        "📅 Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )

    st.divider()

    st.markdown("🌱 **Ecosystem Type**")
    ecosystems = df["ecosystem"].unique().tolist()
    selected_ecosystems = []
    for eco in ecosystems:
        if st.checkbox(eco, value=True, key=f"eco_{eco}"):
            selected_ecosystems.append(eco)

    st.divider()

    st.markdown("🌦️ **Season**")
    selected_semesters = []
    for sem in ["Wet Season", "Dry Season"]:
        if st.checkbox(sem, value=True, key=f"sem_{sem}"):
            selected_semesters.append(sem)

    st.divider()
    st.caption("Filters apply to all charts and insights.")

# ─────────────────────────────────────────────
# BUILD ACTIVE FILTERS DICT
# ─────────────────────────────────────────────

active_filters = {
    "year_range": f"{year_range[0]} - {year_range[1]}",
    "ecosystems": selected_ecosystems if selected_ecosystems else ["All"],
    "semesters":  selected_semesters if selected_semesters else ["All"],
}

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────

df_filtered = df[
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1]) &
    (df["ecosystem"].isin(
        selected_ecosystems if selected_ecosystems else ecosystems
    )) &
    (df["semester"].isin(
        selected_semesters if selected_semesters else ["Wet Season", "Dry Season"]
    ))
].copy()

if df_filtered.empty:
    st.warning("⚠️ No data matches your current filters. Please adjust the sidebar filters.")
    st.stop()

stats = get_summary_stats(df_filtered)

# ─────────────────────────────────────────────
# DATASET OVERVIEW
# ─────────────────────────────────────────────

st.subheader("📋 Dataset Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Year Range",        stats["year_range"])
col2.metric("Avg Yield (MT/ha)", stats["national_avg_yield"])
col3.metric("Best Year",         stats["best_year"])
col4.metric("Worst Year",        stats["worst_year"])

st.caption("ℹ️ Adjust filters in the sidebar then click Generate Report to update the analysis.")
st.divider()
# ─────────────────────────────────────────────
# GENERATE REPORT BUTTON
# ─────────────────────────────────────────────

st.subheader("📊 Visualizations & AI Insights")
st.markdown("Click the button below to generate all charts and AI-written analysis.")

if st.button("🚀 Generate Report", type="primary", use_container_width=True):

    with st.spinner("Generating charts..."):
        st.session_state.figures = {
            "yield_trend":   plot_yield_trend(df_filtered),
            "ecosystem":     plot_ecosystem_comparison(df_filtered),
            "seasonal":      plot_seasonal_analysis(df_filtered),
            "regional":      plot_regional_heatmap(df_filtered),
            "area_vs_yield": plot_area_vs_yield(df_filtered),
            "top_provinces": plot_top_provinces(df_filtered),
            "3d_surface":    plot_3d_yield_surface(df_filtered),
        }

    with st.spinner("Generating AI insights — this takes about 30 seconds..."):
        st.session_state.insights = {
            "yield_trend":       get_full_section("yield_trend",       stats, active_filters, st.session_state.figures["yield_trend"]),
            "ecosystem":         get_full_section("ecosystem",         stats, active_filters, st.session_state.figures["ecosystem"]),
            "seasonal":          get_full_section("seasonal",          stats, active_filters, st.session_state.figures["seasonal"]),
            "regional":          get_full_section("regional",          stats, active_filters, st.session_state.figures["regional"]),
            "area_vs_yield":     get_full_section("area_vs_yield",     stats, active_filters, st.session_state.figures["area_vs_yield"]),
            "top_provinces":     get_full_section("top_provinces",     stats, active_filters, st.session_state.figures["top_provinces"]),
            "executive_summary": get_full_section("executive_summary", stats, active_filters),
            "3d_surface":        get_full_section("3d_surface",        stats, active_filters, st.session_state.figures["3d_surface"]),
        }

    with st.spinner("Building PDF report..."):
        st.session_state.pdf_bytes = generate_report(
            st.session_state.figures,
            st.session_state.insights,
            stats
        )

    st.session_state.report_ready = True
    st.success("✅ Report generated successfully!")

# ─────────────────────────────────────────────
# DISPLAY RESULTS — outside button block
# ─────────────────────────────────────────────

if st.session_state.get("report_ready"):

    st.download_button(
        label="📥 Download PDF Report",
        data=st.session_state.pdf_bytes,
        file_name="rice_yield_report.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.divider()

    # ── Chart 1 ──
    st.subheader("📈 National Yield Trend")
    st.plotly_chart(
        st.session_state.figures["yield_trend"],
        use_container_width=True
    )
    with st.expander("💡 AI Analysis", expanded=True):
        st.write(st.session_state.insights["yield_trend"]["narrative"])
        st.divider()
        st.markdown("**📚 Sources**")
        for source in st.session_state.insights["yield_trend"]["institutional"]:
            st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")

    st.divider()

    # ── Chart 2 ──
    st.subheader("🌱 Ecosystem Comparison: Irrigated vs Rainfed")
    st.plotly_chart(
        st.session_state.figures["ecosystem"],
        use_container_width=True
    )
    with st.expander("💡 AI Analysis", expanded=True):
        st.write(st.session_state.insights["ecosystem"]["narrative"])
        st.divider()
        st.markdown("**📚 Sources**")
        for source in st.session_state.insights["ecosystem"]["institutional"]:
            st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")

    st.divider()

    # ── Chart 3 ──
    st.subheader("🌦️ Wet Season vs Dry Season Analysis")
    st.plotly_chart(
        st.session_state.figures["seasonal"],
        use_container_width=True
    )
    with st.expander("💡 AI Analysis", expanded=True):
        st.write(st.session_state.insights["seasonal"]["narrative"])
        st.divider()
        st.markdown("**📚 Sources**")
        for source in st.session_state.insights["seasonal"]["institutional"]:
            st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")

    st.divider()

    # ── Chart 4 ──
    st.subheader("🗺️ Regional Yield Heatmap")
    st.plotly_chart(
        st.session_state.figures["regional"],
        use_container_width=True
    )
    with st.expander("💡 AI Analysis", expanded=True):
        st.write(st.session_state.insights["regional"]["narrative"])
        st.divider()
        st.markdown("**📚 Sources**")
        for source in st.session_state.insights["regional"]["institutional"]:
            st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")

    st.divider()

    # ── Chart 5 ──
    st.subheader("📐 Area Harvested vs Yield")
    st.plotly_chart(
        st.session_state.figures["area_vs_yield"],
        use_container_width=True
    )
    with st.expander("💡 AI Analysis", expanded=True):
        st.write(st.session_state.insights["area_vs_yield"]["narrative"])
        st.divider()
        st.markdown("**📚 Sources**")
        for source in st.session_state.insights["area_vs_yield"]["institutional"]:
            st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")

    st.divider()

    # ── Chart 6 ──
    st.subheader("🏆 Top & Bottom Provinces by Yield")
    st.plotly_chart(
        st.session_state.figures["top_provinces"],
        use_container_width=True
    )
    with st.expander("💡 AI Analysis", expanded=True):
        st.write(st.session_state.insights["top_provinces"]["narrative"])
        st.divider()
        st.markdown("**📚 Sources**")
        for source in st.session_state.insights["top_provinces"]["institutional"]:
            st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")

    st.divider()

    # ── Chart 7 ──
    st.subheader("🌐 3D Yield Surface: Region × Year × Yield")
    st.plotly_chart(
        st.session_state.figures["3d_surface"],
        use_container_width=True
    )
    with st.expander("💡 AI Analysis", expanded=True):
        st.write(st.session_state.insights["3d_surface"]["narrative"])
        st.divider()
        st.markdown("**📚 Sources**")
        for source in st.session_state.insights["3d_surface"]["institutional"]:
            st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")

    st.divider()

    # ── Executive Summary ──
    st.subheader("📝 Executive Summary")
    st.write(st.session_state.insights["executive_summary"]["narrative"])
    st.divider()
    st.markdown("**📚 Sources**")
    for source in st.session_state.insights["executive_summary"]["institutional"]:
        st.markdown(f"• [{source['title']} — {source['org']}]({source['url']})")