import os
import tempfile
from fpdf import FPDF
from datetime import datetime

# ─────────────────────────────────────────────
# CUSTOM PDF CLASS
# ─────────────────────────────────────────────

class RiceReport(FPDF):
    def header(self):
        """Runs automatically at the top of every page."""
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "Philippine Rice Yield Analytics Report", align="R")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        """Runs automatically at the bottom of every page."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# ─────────────────────────────────────────────
# HELPER — SAVE FIGURE AS PNG
# ─────────────────────────────────────────────

def fig_to_png(fig, filename):
    """
    Converts a Plotly figure to a PNG file.
    Saves to a temp folder and returns the file path.
    """
    temp_dir = tempfile.gettempdir()
    path = os.path.join(temp_dir, filename)
    fig.write_image(path, width=800, height=400, scale=2)
    return path

def sanitize_text(text):
    """
    Removes or replaces characters not supported
    by FPDF's built-in Helvetica font.
    Prevents FPDFUnicodeEncodingException errors.
    """
    replacements = {
        "\u2014": "-",   # em dash —
        "\u2013": "-",   # en dash –
        "\u2018": "'",   # left single quote '
        "\u2019": "'",   # right single quote '
        "\u201c": '"',   # left double quote "
        "\u201d": '"',   # right double quote "
        "\u2026": "...", # ellipsis …
        "\u00e9": "e",   # é
        "\u00f1": "n",   # ñ
        "\u00e0": "a",   # à
        "\u00e8": "e",   # è
        "\u00f3": "o",   # ó
        "\u00fa": "u",   # ú
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

# ─────────────────────────────────────────────
# COVER PAGE
# ─────────────────────────────────────────────

def add_cover_page(pdf, stats):
    """Adds a professional cover page to the report."""
    pdf.add_page()

    # Top spacing
    pdf.ln(20)

    # Main title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 12, "Philippine Rice Yield", align="C")
    pdf.ln(12)
    pdf.cell(0, 12, "Analytics Report", align="C")
    pdf.ln(10)

    # Divider
    pdf.set_draw_color(30, 100, 50)
    pdf.set_line_width(1)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(10)

    # Subtitle
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Data Period: {stats['year_range']}", align="C")
    pdf.ln(8)
    pdf.cell(0, 8, f"Generated: {datetime.today().strftime('%B %d, %Y')}", align="C")
    pdf.ln(20)

    # Dataset summary box
    pdf.set_fill_color(240, 248, 240)
    pdf.set_draw_color(180, 220, 180)
    pdf.set_line_width(0.3)
    pdf.rect(30, pdf.get_y(), 150, 60, style="FD")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 8, "Dataset Summary", align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    summary_items = [
        f"Provinces Covered: {stats['provinces']}",
        f"Regions Covered: {stats['regions']}",
        f"Total Records: {stats['total_records']:,}",
        f"National Average Yield: {stats['national_avg_yield']} MT/ha",
    ]

    for item in summary_items:
        pdf.cell(0, 7, item, align="C")
        pdf.ln(7)

    pdf.ln(20)

    # Source note
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, "Data Source: Philippine Statistics Authority (PSA)", align="C")
    pdf.ln(6)
    pdf.cell(0, 6, "AI Insights powered by Groq (LLaMA 3.3 70B)", align="C")


# ─────────────────────────────────────────────
# EXECUTIVE SUMMARY PAGE
# ─────────────────────────────────────────────

def add_executive_summary(pdf, section):
    """Adds the AI generated executive summary page."""
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 10, "Executive Summary", align="L")
    pdf.ln(8)

    pdf.set_draw_color(30, 100, 50)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Narrative
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)

    narrative = sanitize_text(
        section["narrative"] if isinstance(section, dict) else section
    )
    pdf.multi_cell(0, 7, narrative)

# ─────────────────────────────────────────────
# CHART SECTION
# ─────────────────────────────────────────────

def add_chart_section(pdf, title, png_path, section):
    """
    Adds one full section to the PDF:
    - Section title
    - Chart image
    - AI generated insight paragraph
    - Institutional sources
    """
    pdf.add_page()

    # Section title
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 10, title, align="L")
    pdf.ln(8)

    # Divider
    pdf.set_draw_color(30, 100, 50)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Chart image
    pdf.image(png_path, x=10, w=190)
    pdf.ln(6)

    # AI insight
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 6, "Analysis", align="L")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    narrative = sanitize_text(
        section["narrative"] if isinstance(section, dict) else section
    )
    pdf.multi_cell(0, 6, narrative)


# ─────────────────────────────────────────────
# MASTER FUNCTION — GENERATE FULL REPORT
# ─────────────────────────────────────────────

def add_text_section(pdf, title, section):
    """
    Adds a text-only section for charts that don't
    render well as static images (heatmap, 3D surface).
    Shows title, AI analysis, and sources only.
    """
    pdf.add_page()

    # Section title
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 10, title, align="L")
    pdf.ln(8)

    # Divider
    pdf.set_draw_color(30, 100, 50)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Note explaining why no chart
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(
        0, 6,
        "Note: This visualization is interactive and best viewed in the web application.",
        align="L"
    )
    pdf.ln(8)

    # AI Analysis
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 6, "Analysis", align="L")
    pdf.ln(5)


    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    narrative = sanitize_text(
        section["narrative"] if isinstance(section, dict) else section
    )
    pdf.multi_cell(0, 6, narrative)


# ─────────────────────────────────────────────
# CONSOLIDATED REFERENCES PAGE
# ─────────────────────────────────────────────

_SECTION_LABELS = [
    ("executive_summary", "Executive Summary"),
    ("yield_trend",       "National Yield Trend"),
    ("ecosystem",         "Ecosystem Comparison"),
    ("seasonal",          "Seasonal Analysis"),
    ("area_vs_yield",     "Area Harvested vs Yield"),
    ("top_provinces",     "Top & Bottom Provinces"),
    ("regional",          "Regional Yield Analysis"),
    ("3d_surface",        "3D Yield Surface"),
]


def add_references_page(pdf, insights):
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 100, 50)
    pdf.cell(0, 10, "References", align="L")
    pdf.ln(8)

    pdf.set_draw_color(30, 100, 50)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    any_printed = False

    for key, label in _SECTION_LABELS:
        section  = insights.get(key, {})
        articles = section.get("articles", []) if isinstance(section, dict) else []
        if not articles:
            continue

        any_printed = True

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 100, 50)
        pdf.cell(0, 7, label, align="L")
        pdf.ln(7)

        pdf.set_left_margin(10)
        pdf.set_right_margin(10)

        for article in articles:
            title  = sanitize_text(article.get("title", "Untitled"))
            source = article.get("source", "")
            url    = article.get("url", "")

            label_text = f"{title} ({source})" if source else title
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, sanitize_text(label_text))

            if url:
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(0, 0, 180)
                if len(url) > 90:
                    url = url[:87] + "..."
                pdf.cell(0, 5, url, align="L")
                pdf.ln(5)

        pdf.set_text_color(60, 60, 60)
        pdf.ln(4)

    if not any_printed:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 7, "No external Tavily sources were retrieved for this report.", align="L")


def generate_report(figures, insights, stats):
    """
    Assembles the complete PDF report.

    Args:
        figures  - dict of chart name to Plotly figure
        insights - dict of chart name to AI insight string
        stats    - summary stats dict from data_processor

    Returns:
        bytes - the complete PDF as a bytes object
    """
    pdf = RiceReport()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. Cover page
    add_cover_page(pdf, stats)

    # 2. Executive summary
    add_executive_summary(pdf, insights["executive_summary"])
    

    # 3. Chart sections
    chart_sections = [
        (f"National Yield Trend ({stats['year_range']})", "yield_trend"),
        ("Ecosystem Comparison: Irrigated vs Rainfed",    "ecosystem"),
        ("Wet Season vs Dry Season Analysis",             "seasonal"),
        ("Area Harvested vs Yield",                       "area_vs_yield"),
        ("Top & Bottom Provinces by Yield",               "top_provinces"),
    ]

    for title, key in chart_sections:
        png_path = fig_to_png(figures[key], f"{key}.png")
        add_chart_section(pdf, title, png_path, insights[key])

    # Text-only sections for interactive charts
    text_only_sections = [
        ("Regional Yield Analysis",              "regional"),
        ("3D Yield Surface - Regional Overview", "3d_surface"),
    ]

    for title, key in text_only_sections:
        add_text_section(pdf, title, insights[key])

    # 5. Consolidated references page
    add_references_page(pdf, insights)

    return bytes(pdf.output())