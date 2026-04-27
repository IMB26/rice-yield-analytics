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
from word_generator import generate_word_report

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Rice Yield Analytics",
    page_icon="🌾",
    layout="wide"
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #161b27;
    border: 1px solid #2a3347;
    border-top: 3px solid #27ae60;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.35);
}
[data-testid="stMetricLabel"] > div {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #8892a4 !important;
}
[data-testid="stMetricValue"] > div {
    color: #2ecc71 !important;
    font-weight: 800 !important;
}

/* ── Primary (Generate) button ── */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #1e8449, #27ae60) !important;
    border: none !important;
    height: 3.2rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.4px !important;
    color: #ffffff !important;
    box-shadow: 0 4px 16px rgba(39,174,96,0.40) !important;
    transition: box-shadow 0.2s ease, transform 0.15s ease !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 6px 24px rgba(39,174,96,0.55) !important;
    transform: translateY(-1px) !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: #161b27 !important;
    border: 2px solid #27ae60 !important;
    color: #2ecc71 !important;
    font-weight: 700 !important;
    height: 3.2rem !important;
    font-size: 1rem !important;
    transition: background 0.15s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #1c2535 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] details {
    border: 1px solid #2a3347 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    background: #161b27 !important;
}
[data-testid="stExpander"] details summary {
    background: #1c2535 !important;
    padding: 0.75rem 1.1rem !important;
    font-weight: 600 !important;
    color: #2ecc71 !important;
    font-size: 0.95rem !important;
}
[data-testid="stExpander"] details summary:hover {
    background: #212d40 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #111827 !important;
    border-right: 1px solid #1f2d3d !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #2a7a4e !important;
    border-radius: 12px !important;
    background: #161b27 !important;
    padding: 0.5rem 1rem !important;
}

/* ── Plotly chart card ── */
[data-testid="stPlotlyChart"] > div {
    border-radius: 10px !important;
    border: 1px solid #2a3347 !important;
    box-shadow: 0 2px 14px rgba(0,0,0,0.40) !important;
    overflow: hidden;
}

/* ── Divider ── */
hr {
    border-color: #2a3347 !important;
    margin: 1.25rem 0 !important;
}

/* ── Alerts / info boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ── Checkbox label ── */
[data-testid="stCheckbox"] label {
    font-size: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SECTION HEADER HELPER
# ─────────────────────────────────────────────
def section_header(icon: str, title: str):
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin:1.25rem 0 0.4rem;">
        <div style="
            width:4px; height:28px;
            background:linear-gradient(180deg,#2ecc71,#1a7a45);
            border-radius:2px; flex-shrink:0;
        "></div>
        <span style="
            font-size:1.2rem; font-weight:700;
            color:#2ecc71; letter-spacing:-0.2px;
        ">{icon}&nbsp;{title}</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HEADER BANNER
# ─────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, #1a5c32 0%, #27ae60 100%);
    padding: 2rem 2.5rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(39,174,96,0.22);
">
    <div style="display:flex; align-items:center; gap:18px;">
        <span style="font-size:3rem; line-height:1;">🌾</span>
        <div>
            <h1 style="
                color:#ffffff; font-size:2rem; font-weight:800;
                margin:0; line-height:1.2; letter-spacing:-0.5px;
            ">Philippine Rice Yield Analytics</h1>
            <p style="
                color:rgba(255,255,255,0.85); margin:6px 0 0;
                font-size:0.97rem; font-weight:400;
            ">
                Upload a PSA rice production CSV to generate visualizations,
                AI&nbsp;insights, and a PDF report.
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

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

    exact_match = all(col in uploaded_columns for col in REQUIRED_COLUMNS)

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
    st.markdown("""
    <div style="text-align:center; padding:0.5rem 0 1rem;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Official_Seal_of_the_Philippine_Statistics_Authority.png/200px-Official_Seal_of_the_Philippine_Statistics_Authority.png"
             width="72" style="border-radius:50%; border:2px solid #2a3347;">
        <div style="font-size:1rem; font-weight:700; color:#2ecc71; margin-top:8px;">
            Filter Controls
        </div>
        <div style="font-size:0.78rem; color:#8892a4; margin-top:2px;">
            Applies to all charts and insights
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    st.markdown(
        "<p style='font-size:0.85rem; font-weight:700; color:#8892a4;"
        " text-transform:uppercase; letter-spacing:0.6px;'>🌱 Ecosystem</p>",
        unsafe_allow_html=True
    )
    ecosystems = df["ecosystem"].unique().tolist()
    selected_ecosystems = []
    for eco in ecosystems:
        if st.checkbox(eco, value=True, key=f"eco_{eco}"):
            selected_ecosystems.append(eco)

    st.divider()

    st.markdown(
        "<p style='font-size:0.85rem; font-weight:700; color:#8892a4;"
        " text-transform:uppercase; letter-spacing:0.6px;'>🌦️ Season</p>",
        unsafe_allow_html=True
    )
    selected_semesters = []
    for sem in ["Wet Season", "Dry Season"]:
        if st.checkbox(sem, value=True, key=f"sem_{sem}"):
            selected_semesters.append(sem)

# ─────────────────────────────────────────────
# BUILD ACTIVE FILTERS DICT
# ─────────────────────────────────────────────
active_filters = {
    "year_range": f"{year_range[0]} - {year_range[1]}",
    "ecosystems": selected_ecosystems if selected_ecosystems else ["All"],
    "semesters":  selected_semesters  if selected_semesters  else ["All"],
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
section_header("📋", "Dataset Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Year Range",        stats["year_range"])
col2.metric("Avg Yield (MT/ha)", stats["national_avg_yield"])
col3.metric("Best Year",         stats["best_year"])
col4.metric("Worst Year",        stats["worst_year"])

st.caption("ℹ️ Adjust filters in the sidebar, then click Generate Report to refresh the analysis.")
st.divider()

# ─────────────────────────────────────────────
# GENERATE REPORT BUTTON
# ─────────────────────────────────────────────
section_header("📊", "Visualizations & AI Insights")
st.markdown(
    "<p style='color:#8892a4; font-size:0.93rem; margin-bottom:0.75rem;'>"
    "Click below to generate all charts and AI-written analysis.</p>",
    unsafe_allow_html=True
)

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

    with st.spinner("Building PDF & Word reports..."):
        st.session_state.pdf_bytes  = generate_report(
            st.session_state.figures,
            st.session_state.insights,
            stats
        )
        st.session_state.docx_bytes = generate_word_report(
            st.session_state.figures,
            st.session_state.insights,
            stats
        )

    st.session_state.report_ready = True
    st.success("✅ Report generated successfully!")


# ─────────────────────────────────────────────
# EVIDENCE BLOCK HELPER
# ─────────────────────────────────────────────
def render_evidence_block(section: dict):
    if section.get("supported_findings"):
        st.markdown("**🔎 Tavily-backed evidence**")
        for i, item in enumerate(section["supported_findings"], start=1):
            support_summary = item.get("support_summary", "Source support available.")
            source_title    = item.get("source_title", "Source")
            source_url      = item.get("source_url", "#")
            st.markdown(f"{i}. {support_summary}  \n[{source_title}]({source_url})")

    if section.get("unsupported_findings"):
        st.caption(
            "Dataset findings without strong external match: "
            + ", ".join(section["unsupported_findings"])
        )

    if section.get("articles"):
        st.markdown("**📰 Related Tavily sources**")
        for article in section["articles"][:5]:
            title  = article.get("title", "Source")
            url    = article.get("url", "#")
            source = article.get("source", "")
            label  = f"{title} ({source})" if source else title
            st.markdown(f"- [{label}]({url})")


# ─────────────────────────────────────────────
# CHART + INSIGHT BLOCK HELPER
# ─────────────────────────────────────────────
def render_chart_section(icon: str, title: str, fig_key: str, insight_key: str):
    section_header(icon, title)
    st.plotly_chart(st.session_state.figures[fig_key], use_container_width=True)
    with st.expander("💡 AI Analysis", expanded=True):
        section = st.session_state.insights[insight_key]
        st.write(section["narrative"])
        render_evidence_block(section)
    st.divider()


# ─────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────
if st.session_state.get("report_ready"):

    col_pdf, col_word = st.columns(2)
    with col_pdf:
        st.download_button(
            label="📄 Download PDF Report",
            data=st.session_state.pdf_bytes,
            file_name="rice_yield_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col_word:
        st.download_button(
            label="📝 Download Word Report",
            data=st.session_state.docx_bytes,
            file_name="rice_yield_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    st.divider()

    render_chart_section("📈", "National Yield Trend",             "yield_trend",   "yield_trend")
    render_chart_section("🌱", "Ecosystem Comparison: Irrigated vs Rainfed", "ecosystem", "ecosystem")
    render_chart_section("🌦️", "Wet Season vs Dry Season Analysis","seasonal",      "seasonal")
    render_chart_section("🗺️", "Regional Yield Heatmap",           "regional",      "regional")
    render_chart_section("📐", "Area Harvested vs Yield",          "area_vs_yield", "area_vs_yield")
    render_chart_section("🏆", "Top & Bottom Provinces by Yield",  "top_provinces", "top_provinces")
    render_chart_section("🌐", "3D Yield Surface: Region × Year × Yield", "3d_surface", "3d_surface")

    # ── Executive Summary ──
    section_header("📝", "Executive Summary")
    st.markdown("""
    <div style="
        background:#161b27; border:1px solid #2a3347;
        border-left:4px solid #27ae60;
        border-radius:10px; padding:1.25rem 1.5rem;
        margin-bottom:1rem;
    ">
    """, unsafe_allow_html=True)
    section = st.session_state.insights["executive_summary"]
    st.write(section["narrative"])
    render_evidence_block(section)
    st.markdown("</div>", unsafe_allow_html=True)
