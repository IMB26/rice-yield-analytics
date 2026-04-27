"""
word_generator.py
Builds a .docx file using only Python's standard library (zipfile + io).
A .docx is a ZIP archive of XML files — no lxml or python-docx required.
"""
import io
import os
import zipfile
import xml.sax.saxutils as saxutils
from datetime import datetime

from pdf_generator import fig_to_png, sanitize_text

# ─────────────────────────────────────────────
# BRAND COLORS  (Word XML uses hex without #)
# ─────────────────────────────────────────────
C_GREEN_DARK = "1A7A3E"
C_GREEN      = "27AE60"
C_TEXT       = "1C1C2E"
C_MUTED      = "6B7280"
C_LINK       = "0070C0"

# Image canvas: 6 in wide × 3 in tall, in EMUs (1 inch = 914400 EMU)
IMG_CX = 5486400
IMG_CY = 2743200


# ─────────────────────────────────────────────
# XML PRIMITIVE BUILDERS
# ─────────────────────────────────────────────
def _esc(text: str) -> str:
    return saxutils.escape(str(text))


def _run(text: str, bold=False, italic=False, size=21, color=None) -> str:
    """
    size is in half-points: 21 = 10.5 pt, 24 = 12 pt, 36 = 18 pt, 56 = 28 pt
    """
    props = [f'<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>']
    if bold:   props.append("<w:b/>")
    if italic: props.append("<w:i/>")
    if color:  props.append(f'<w:color w:val="{color}"/>')
    props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>"
    return f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'


def _para(runs_xml: str, align="left", space_before=0, space_after=120) -> str:
    jc      = f'<w:jc w:val="{align}"/>' if align != "left" else ""
    spacing = f'<w:spacing w:before="{space_before}" w:after="{space_after}"/>'
    return f"<w:p><w:pPr>{jc}{spacing}</w:pPr>{runs_xml}</w:p>"


def _empty_para() -> str:
    return "<w:p/>"


def _page_break() -> str:
    return "<w:p><w:r><w:br w:type='page'/></w:r></w:p>"


def _divider() -> str:
    return (
        "<w:p><w:pPr>"
        "<w:pBdr>"
        f'<w:bottom w:val="single" w:sz="6" w:space="1" w:color="{C_GREEN}"/>'
        "</w:pBdr>"
        '<w:spacing w:before="40" w:after="40"/>'
        "</w:pPr></w:p>"
    )


# ─────────────────────────────────────────────
# STYLED PARAGRAPH SHORTCUTS
# ─────────────────────────────────────────────
def _h1(text: str) -> str:
    r = _run(sanitize_text(text), bold=True, size=36, color=C_GREEN_DARK)
    return _para(r, space_before=160, space_after=60)


def _h2(text: str) -> str:
    r = _run(sanitize_text(text), bold=True, size=24, color=C_GREEN)
    return _para(r, space_before=120, space_after=40)


def _body(text: str) -> str:
    r = _run(sanitize_text(text), size=21, color=C_TEXT)
    return _para(r, space_after=100)


def _note(text: str) -> str:
    r = _run(sanitize_text(text), italic=True, size=18, color=C_MUTED)
    return _para(r, space_after=80)


def _center(text: str, size=24, color=C_MUTED, bold=False) -> str:
    r = _run(sanitize_text(text), bold=bold, size=size, color=color)
    return _para(r, align="center", space_after=80)


# ─────────────────────────────────────────────
# INLINE IMAGE
# ─────────────────────────────────────────────
def _image_para(r_id: str, img_id: int, cx=IMG_CX, cy=IMG_CY) -> str:
    return f"""<w:p>
<w:pPr><w:jc w:val="center"/><w:spacing w:after="120"/></w:pPr>
<w:r><w:drawing>
<wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  distT="0" distB="0" distL="0" distR="0">
  <wp:extent cx="{cx}" cy="{cy}"/>
  <wp:docPr id="{img_id}" name="Image{img_id}"/>
  <wp:cNvGraphicFramePr>
    <a:graphicFrameLocks
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      noChangeAspect="1"/>
  </wp:cNvGraphicFramePr>
  <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
      <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:nvPicPr>
          <pic:cNvPr id="0" name="Image{img_id}"/>
          <pic:cNvPicPr/>
        </pic:nvPicPr>
        <pic:blipFill>
          <a:blip r:embed="{r_id}"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
          <a:stretch><a:fillRect/></a:stretch>
        </pic:blipFill>
        <pic:spPr>
          <a:xfrm>
            <a:off x="0" y="0"/>
            <a:ext cx="{cx}" cy="{cy}"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </pic:spPr>
      </pic:pic>
    </a:graphicData>
  </a:graphic>
</wp:inline>
</w:drawing></w:r>
</w:p>"""



# ─────────────────────────────────────────────
# PAGE BUILDERS
# ─────────────────────────────────────────────
def _cover_page_xml(stats: dict) -> str:
    parts = [_empty_para()] * 4

    for line in ("Philippine Rice Yield", "Analytics Report"):
        r = _run(line, bold=True, size=56, color=C_GREEN_DARK)
        parts.append(_para(r, align="center", space_after=40))

    parts.append(_divider())
    parts.append(_empty_para())

    parts.append(_center(f"Data Period: {stats['year_range']}"))
    parts.append(_center(f"Generated: {datetime.today().strftime('%B %d, %Y')}"))
    parts.append(_empty_para())

    rows = [
        ("Provinces Covered",      str(stats["provinces"])),
        ("Regions Covered",        str(stats["regions"])),
        ("Total Records",          f"{stats['total_records']:,}"),
        ("National Average Yield", f"{stats['national_avg_yield']} MT/ha"),
        ("Data Source",            "Philippine Statistics Authority (PSA)"),
    ]
    for label, value in rows:
        r = _run(f"{label}:  ", bold=True, size=21, color=C_GREEN_DARK)
        r += _run(value, size=21, color=C_TEXT)
        parts.append(_para(r, align="center", space_after=80))

    parts.append(_empty_para())
    parts.append(
        _center(
            "AI Insights: Groq LLaMA 3.3 70B  ·  Evidence: Tavily Search",
            size=17,
        )
    )
    parts.append(_page_break())
    return "".join(parts)


def _executive_summary_xml(section: dict) -> str:
    narrative = section["narrative"] if isinstance(section, dict) else section
    parts = [_h1("Executive Summary"), _divider(), _empty_para(), _body(narrative)]
    parts.append(_page_break())
    return "".join(parts)


def _chart_section_xml(
    title: str,
    r_id: str | None,
    img_id: int,
    section: dict,
) -> str:
    parts = [_h1(title), _divider(), _empty_para()]
    if r_id:
        parts.append(_image_para(r_id, img_id))
    parts += [_empty_para(), _h2("Analysis")]
    narrative = section["narrative"] if isinstance(section, dict) else section
    parts.append(_body(narrative))
    parts.append(_page_break())
    return "".join(parts)


def _text_section_xml(title: str, section: dict) -> str:
    parts = [
        _h1(title), _divider(), _empty_para(),
        _note("Note: This visualization is interactive and best viewed in the web application."),
        _empty_para(), _h2("Analysis"),
    ]
    narrative = section["narrative"] if isinstance(section, dict) else section
    parts.append(_body(narrative))
    parts.append(_page_break())
    return "".join(parts)


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


def _references_page_xml(insights: dict) -> str:
    parts = [_h1("References"), _divider(), _empty_para()]

    any_printed = False

    for key, label in _SECTION_LABELS:
        section  = insights.get(key, {})
        articles = section.get("articles", []) if isinstance(section, dict) else []
        if not articles:
            continue

        any_printed = True
        parts.append(_h2(label))

        for article in articles:
            title  = sanitize_text(article.get("title", "Untitled"))
            source = article.get("source", "")
            url    = article.get("url", "")

            label_text = f"{title} ({source})" if source else title
            title_run  = _run(label_text, bold=True, size=19, color=C_TEXT)
            url_run    = _run(f"  {url}", italic=True, size=17, color=C_LINK) if url else ""
            parts.append(_para(title_run + url_run, space_after=60))

        parts.append(_empty_para())

    if not any_printed:
        parts.append(
            _note("No external Tavily sources were retrieved for this report.")
        )

    return "".join(parts)


# ─────────────────────────────────────────────
# STATIC ZIP MEMBERS
# ─────────────────────────────────────────────
_CONTENT_TYPES = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Default Extension="png"  ContentType="image/png"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
</Types>"""

_PACKAGE_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>"""

_STYLES = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
        <w:sz w:val="21"/><w:szCs w:val="21"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr><w:spacing w:after="120"/></w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>"""

_SETTINGS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:defaultTabStop w:val="720"/>
</w:settings>"""


def _doc_rels(image_rels: list[str]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        '  <Relationship Id="rId1" Target="styles.xml"',
        '    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"/>',
        '  <Relationship Id="rId2" Target="settings.xml"',
        '    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"/>',
    ]
    lines.extend(image_rels)
    lines.append("</Relationships>")
    return "\n".join(lines)


def _document_xml(body: str) -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
  <w:body>
{body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1134" w:right="1417" w:bottom="1134" w:left="1417"
               w:header="709" w:footer="709" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""


# ─────────────────────────────────────────────
# MASTER FUNCTION
# ─────────────────────────────────────────────
def generate_word_report(figures: dict, insights: dict, stats: dict) -> bytes:
    """
    Assembles a complete Word (.docx) report using only Python's standard library.

    Args:
        figures  - dict of chart name to Plotly figure
        insights - dict of chart name to section dict from get_full_section
        stats    - summary stats dict from data_processor

    Returns:
        bytes of the complete .docx file
    """
    chart_sections = [
        (f"National Yield Trend ({stats['year_range']})", "yield_trend"),
        ("Ecosystem Comparison: Irrigated vs Rainfed",    "ecosystem"),
        ("Wet Season vs Dry Season Analysis",             "seasonal"),
        ("Area Harvested vs Yield",                       "area_vs_yield"),
        ("Top & Bottom Provinces by Yield",               "top_provinces"),
    ]
    text_only_sections = [
        ("Regional Yield Analysis",              "regional"),
        ("3D Yield Surface — Regional Overview", "3d_surface"),
    ]

    # rId1 = styles, rId2 = settings; images start at rId3
    image_meta  = {}  # key -> (png_path, r_id, img_id)
    image_rels  = []

    for i, (_, key) in enumerate(chart_sections):
        r_id   = f"rId{3 + i}"
        img_id = i + 1
        try:
            png_path = fig_to_png(figures[key], f"{key}.png")
        except Exception:
            png_path = None
        image_meta[key] = (png_path, r_id, img_id)
        if png_path:
            image_rels.append(
                f'  <Relationship Id="{r_id}"\n'
                f'    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"\n'
                f'    Target="media/{key}.png"/>'
            )

    # Build document body
    body_parts = [_cover_page_xml(stats), _executive_summary_xml(insights["executive_summary"])]

    for title, key in chart_sections:
        png_path, r_id, img_id = image_meta[key]
        body_parts.append(
            _chart_section_xml(title, r_id if png_path else None, img_id, insights[key])
        )

    for title, key in text_only_sections:
        body_parts.append(_text_section_xml(title, insights[key]))

    # Consolidated references page
    body_parts.append(_references_page_xml(insights))

    doc_xml = _document_xml("\n".join(body_parts))

    # Assemble .docx ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",          _CONTENT_TYPES)
        zf.writestr("_rels/.rels",                  _PACKAGE_RELS)
        zf.writestr("word/document.xml",            doc_xml)
        zf.writestr("word/styles.xml",              _STYLES)
        zf.writestr("word/settings.xml",            _SETTINGS)
        zf.writestr("word/_rels/document.xml.rels", _doc_rels(image_rels))

        for _, key in chart_sections:
            png_path, _, _ = image_meta[key]
            if png_path and os.path.exists(png_path):
                with open(png_path, "rb") as f:
                    zf.writestr(f"word/media/{key}.png", f.read())

    return buf.getvalue()
