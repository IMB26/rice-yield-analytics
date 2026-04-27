import os
import json
import re
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from data_processor import REQUIRED_COLUMNS

load_dotenv(override=True)

# Streamlit Cloud stores secrets in st.secrets, not os.environ.
# Inject them into os.environ so os.getenv() works in both environments.
try:
    import streamlit as st
    for _key in ("GROQ_API_KEY", "TAVILY_API_KEY"):
        if not os.environ.get(_key) and _key in st.secrets:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

# -----------------------------
# API clients
# -----------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


# -----------------------------
# Static search seeds per chart
# -----------------------------
SEARCH_QUERIES = {
    "yield_trend": [
        "Philippine rice yield production trend PSA",
        "RCEF rice competitiveness enhancement fund Philippines",
        "PAGASA climate impacts rice Philippines",
    ],
    "ecosystem": [
        "irrigated vs rainfed rice yield Philippines",
        "NIA irrigation infrastructure Philippines rice",
        "IRRI rainfed rice vulnerability Philippines",
    ],
    "seasonal": [
        "wet dry season rice yield Philippines",
        "PAGASA El Nino La Nina Philippines agriculture",
        "PhilRice seasonal rice management",
    ],
    "regional": [
        "regional rice production Philippines PSA",
        "Central Luzon rice productivity factors",
        "BARMM rice production constraints",
    ],
    "area_vs_yield": [
        "farm size rice productivity Philippines",
        "CARP land reform farm fragmentation Philippines",
        "IRRI mechanization smallholder rice",
    ],
    "top_provinces": [
        "top rice producing provinces Philippines PSA",
        "Nueva Ecija irrigation rice yield",
        "low productivity rice provinces Philippines",
    ],
    "3d_surface": [
        "regional rice yield disparity Philippines",
        "Philippine rice productivity by region",
        "DA regional rice programs Philippines",
    ],
    "executive_summary": [
        "Philippine rice industry overview 2024",
        "rice self sufficiency Philippines DA",
        "Philippines rice climate resilience programs",
    ],
}

ALLOWED_DOMAINS = [
    "psa.gov.ph",
    "da.gov.ph",
    "irri.org",
    "philrice.gov.ph",
    "pagasa.dost.gov.ph",
    "nia.gov.ph",
    "fao.org",
    "reliefweb.int",
    "rappler.com",
    "inquirer.net",
    "businessmirror.com.ph",
]


# -----------------------------
# Utility helpers
# -----------------------------
def _extract_balanced_json_object(text: str):
    """
    Extract the first balanced JSON object from text.
    Handles braces inside quoted strings.
    """
    start = text.find("{")
    if start == -1:
        return None

    in_string = False
    escaped = False
    depth = 0

    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

    return None


def _safe_json_loads(raw: str, default):
    if not raw:
        return default
    raw = raw.strip()

    candidates = [raw]

    # Candidate: markdown fenced JSON
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidates.append(fence_match.group(1).strip())

    # Candidate: first balanced JSON object anywhere in text
    balanced = _extract_balanced_json_object(raw)
    if balanced:
        candidates.append(balanced.strip())

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            continue

    return default


def build_filter_context(stats, filters):
    return "\n".join([
        f"- Year range: {filters.get('year_range', stats.get('year_range', 'N/A'))}",
        f"- Ecosystem: {', '.join(filters.get('ecosystems', ['All ecosystems']))}",
        f"- Season: {', '.join(filters.get('semesters', ['All seasons']))}",
    ])


def _shorten_articles(articles):
    compact = []
    for a in articles:
        compact.append({
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "source": a.get("source", ""),
            "snippet": (a.get("snippet", "") or "")[:350],
        })
    return compact


# -----------------------------
# Dataset evidence builder
# -----------------------------
def build_dataset_evidence(chart_key: str, stats: dict) -> dict:
    evidence = {
        "chart_key": chart_key,
        "scope": {
            "year_range": stats.get("year_range"),
            "total_records": stats.get("total_records"),
            "provinces": stats.get("provinces"),
            "regions": stats.get("regions"),
        },
        "metrics": {},
        "claims_seed": [],
    }

    if chart_key == "yield_trend":
        evidence["metrics"] = {
            "national_avg_yield_mt_ha": stats.get("national_avg_yield"),
            "national_max_yield_mt_ha": stats.get("national_max_yield"),
            "national_min_yield_mt_ha": stats.get("national_min_yield"),
            "best_year": stats.get("best_year"),
            "worst_year": stats.get("worst_year"),
        }
        evidence["claims_seed"] = [
            "Describe national trajectory from worst to best year.",
            "Quantify spread between minimum and maximum yield.",
            "Mark causes as hypothesis unless externally supported.",
        ]

    elif chart_key == "ecosystem":
        evidence["metrics"] = {
            "irrigated_avg_yield_mt_ha": stats.get("irrigated_avg_yield"),
            "rainfed_avg_yield_mt_ha": stats.get("rainfed_avg_yield"),
        }
        evidence["claims_seed"] = [
            "Quantify irrigated vs rainfed gap directly from dataset.",
            "Do not assume reasons without evidence support.",
        ]

    elif chart_key == "seasonal":
        evidence["metrics"] = {
            "wet_season_avg_mt_ha": stats.get("wet_season_avg"),
            "dry_season_avg_mt_ha": stats.get("dry_season_avg"),
        }
        evidence["claims_seed"] = [
            "Compare wet and dry season averages using given values only.",
        ]

    elif chart_key in ["regional", "top_provinces", "3d_surface", "area_vs_yield", "executive_summary"]:
        evidence["metrics"] = {
            "top_5_provinces": stats.get("top_5_provinces"),
            "bottom_5_provinces": stats.get("bottom_5_provinces"),
            "national_avg_yield_mt_ha": stats.get("national_avg_yield"),
            "best_year": stats.get("best_year"),
            "worst_year": stats.get("worst_year"),
            "irrigated_avg_yield_mt_ha": stats.get("irrigated_avg_yield"),
            "rainfed_avg_yield_mt_ha": stats.get("rainfed_avg_yield"),
            "wet_season_avg_mt_ha": stats.get("wet_season_avg"),
            "dry_season_avg_mt_ha": stats.get("dry_season_avg"),
        }
        evidence["claims_seed"] = [
            "State ranking and disparity findings only when directly supported by metrics.",
            "Separate facts from hypotheses.",
        ]

    return evidence


# -----------------------------
# Tavily search
# -----------------------------
def build_dynamic_queries(chart_key: str, pass1: dict) -> list:
    queries = list(SEARCH_QUERIES.get(chart_key, []))
    findings = pass1.get("dataset_findings", [])

    for f in findings:
        claim = (f.get("claim") or "").strip()
        if claim:
            queries.append(f"Philippines rice: {claim}")

    seen = set()
    deduped = []
    for q in queries:
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)

    return deduped[:8]


def search_real_articles(chart_key: str, override_queries=None) -> list:
    if tavily is None:
        return []

    queries = override_queries or SEARCH_QUERIES.get(chart_key, [])
    articles = []

    for query in queries:
        try:
            results = tavily.search(
                query=query,
                search_depth="basic",
                max_results=2,
                include_domains=ALLOWED_DOMAINS
            )
            for r in results.get("results", []):
                url = r.get("url", "") or ""
                source = ""
                try:
                    source = url.split("/")[2]
                except Exception:
                    source = ""
                articles.append({
                    "title": r.get("title", ""),
                    "url": url,
                    "snippet": (r.get("content", "") or "")[:400],
                    "source": source,
                })
        except Exception:
            continue

    # Deduplicate by URL
    seen = set()
    unique = []
    for a in articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)

    # Show two more sources than before (8 -> 10)
    return unique[:10]


# -----------------------------
# Two-pass generation
# -----------------------------
CHART_GUIDANCE = {
    "yield_trend": "Focus on long-run trend, best/worst year contrast, and plausible drivers as hypotheses.",
    "ecosystem": "Focus on irrigated vs rainfed yield difference and implications for resilience.",
    "seasonal": "Focus on wet vs dry comparison and seasonal risk framing.",
    "regional": "Focus on regional disparity and potential structural explanations.",
    "area_vs_yield": "Focus on farm area versus productivity relationship and caveats.",
    "top_provinces": "Focus on top/bottom ranking and practical implications.",
    "3d_surface": "Focus on landscape interpretation and inequality over time.",
    "executive_summary": "Integrate top findings into concise policy-oriented summary.",
}


def generate_dataset_first_analysis(chart_key: str, evidence: dict, filter_context: str) -> dict:
    if client is None:
        return {
            "dataset_findings": [],
            "draft_narrative": "Insight unavailable: GROQ_API_KEY is not configured.",
        }

    system_msg = (
        "You are a senior agricultural data analyst.\n"
        "Rules:\n"
        "1) Use ONLY the provided dataset evidence.\n"
        "2) Do NOT use external facts in this step.\n"
        "3) If a cause is uncertain, label it as hypothesis.\n"
        "4) Return valid JSON only."
    )

    user_msg = f"""
Chart key: {chart_key}
Chart guidance: {CHART_GUIDANCE.get(chart_key, "General agricultural analysis.")}

Active filters:
{filter_context}

Dataset evidence JSON:
{json.dumps(evidence, ensure_ascii=True)}

Return exactly this JSON schema:
{{
  "dataset_findings": [
    {{
      "id": "F1",
      "claim": "text",
      "evidence": "explicit metric/value from dataset evidence",
      "type": "fact|hypothesis",
      "confidence": 0.0
    }}
  ],
  "draft_narrative": "6-8 sentences, paragraph only, no bullets, MT/ha units where relevant"
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
        parsed = _safe_json_loads(raw, default=None)
        if parsed and isinstance(parsed, dict):
            # Normalize required keys to avoid downstream key errors
            parsed.setdefault("dataset_findings", [])
            parsed.setdefault("draft_narrative", "")
            if not isinstance(parsed["dataset_findings"], list):
                parsed["dataset_findings"] = []
            if not isinstance(parsed["draft_narrative"], str):
                parsed["draft_narrative"] = str(parsed["draft_narrative"])
            return parsed
        return {
            "dataset_findings": [],
            "draft_narrative": (
                "Insight unavailable: dataset-first JSON parse failed. "
                f"Raw preview: {(raw or '')[:300]}"
            ),
        }
    except Exception as e:
        return {
            "dataset_findings": [],
            "draft_narrative": f"Insight unavailable: dataset-first request failed ({e}).",
        }


def ground_with_tavily_sources(chart_key: str, pass1: dict, articles: list) -> dict:
    if client is None:
        return {
            "supported_findings": [],
            "unsupported_findings": [f.get("id", "") for f in pass1.get("dataset_findings", []) if f.get("id")],
            "final_narrative": pass1.get("draft_narrative", "Insight unavailable."),
        }

    system_msg = (
        "You are an evidence-grounding assistant.\n"
        "Rules:\n"
        "1) Do NOT change dataset findings.\n"
        "2) Only attach sources that clearly support a finding.\n"
        "3) If unsupported, keep finding as dataset-only.\n"
        "4) Return valid JSON only."
    )

    user_msg = f"""
Chart key: {chart_key}

Dataset findings JSON:
{json.dumps(pass1, ensure_ascii=True)}

Candidate articles JSON:
{json.dumps(_shorten_articles(articles), ensure_ascii=True)}

Return exactly this JSON schema:
{{
  "supported_findings": [
    {{
      "finding_id": "F1",
      "support_summary": "how source supports claim",
      "source_title": "title",
      "source_url": "url"
    }}
  ],
  "unsupported_findings": ["F2", "F3"],
  "final_narrative": "single paragraph of 6-8 sentences, data-first; inline citations [1], [2] only where matched"
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
        parsed = _safe_json_loads(raw, default=None)
        if parsed and isinstance(parsed, dict):
            parsed.setdefault("supported_findings", [])
            parsed.setdefault("unsupported_findings", [])
            parsed.setdefault("final_narrative", pass1.get("draft_narrative", "Insight unavailable."))
            if not isinstance(parsed["supported_findings"], list):
                parsed["supported_findings"] = []
            if not isinstance(parsed["unsupported_findings"], list):
                parsed["unsupported_findings"] = []
            if not isinstance(parsed["final_narrative"], str):
                parsed["final_narrative"] = str(parsed["final_narrative"])
            return parsed

        return {
            "supported_findings": [],
            "unsupported_findings": [f.get("id", "") for f in pass1.get("dataset_findings", []) if f.get("id")],
            "final_narrative": (
                pass1.get("draft_narrative", "Insight unavailable.")
                + " (Grounding JSON parse failed.)"
            ),
        }
    except Exception as e:
        return {
            "supported_findings": [],
            "unsupported_findings": [f.get("id", "") for f in pass1.get("dataset_findings", []) if f.get("id")],
            "final_narrative": (
                pass1.get("draft_narrative", "Insight unavailable.")
                + f" (Grounding request failed: {e})"
            ),
        }


# -----------------------------
# Column mapping helper
# -----------------------------
def map_columns(uploaded_columns: list) -> dict:
    if client is None:
        return None

    prompt = f"""
I have a CSV file with these columns:
{uploaded_columns}

Map them to required columns:
{REQUIRED_COLUMNS}

Rules:
- Match by meaning
- Each required column should be matched once if possible
- Use null if no good match
- Return only valid JSON object
- No markdown, no explanation
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a data engineering assistant. "
                        "Return only valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        parsed = _safe_json_loads(raw, default=None)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


# -----------------------------
# Master section builder
# -----------------------------
def get_full_section(chart_key, stats, filters=None, fig=None):
    from sources import SOURCES
    from visualizations import is_chart_empty

    if filters is None:
        filters = {}

    if fig is not None and is_chart_empty(fig):
        return {
            "narrative": (
                "This analysis is not available for the current filters. "
                "The chart could not be generated due to insufficient data."
            ),
            "institutional": [],
            "articles": [],
            "supported_findings": [],
            "unsupported_findings": [],
        }

    # 1) Build strict dataset evidence
    filter_context = build_filter_context(stats, filters)
    evidence = build_dataset_evidence(chart_key, stats)

    # 2) Pass 1 (dataset-only)
    pass1 = generate_dataset_first_analysis(chart_key, evidence, filter_context)

    # 3) Search with dynamic + base queries
    dyn_queries = build_dynamic_queries(chart_key, pass1)
    articles = search_real_articles(chart_key, override_queries=dyn_queries)

    # 4) Pass 2 (source grounding)
    grounded = ground_with_tavily_sources(chart_key, pass1, articles)

    # 5) Institutional references (static trusted orgs)
    institutional = SOURCES.get(chart_key, [])

    return {
        "narrative": grounded.get("final_narrative", pass1.get("draft_narrative", "")),
        "institutional": institutional,
        "articles": articles,
        "supported_findings": grounded.get("supported_findings", []),
        "unsupported_findings": grounded.get("unsupported_findings", []),
    }