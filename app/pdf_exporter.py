import os
from pathlib import Path

from jinja2 import Template

os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib:" + os.environ.get(
    "DYLD_FALLBACK_LIBRARY_PATH", ""
)

from weasyprint import HTML


def _table_to_lookup(table_data: dict) -> dict:
    indicators = table_data.get("Indicator", [])
    values = table_data.get("Valoare", [])
    return dict(zip(indicators, values))


def _find_value_by_prefix(
    lookup: dict,
    prefix: str,
    exclude_contains: list[str] | None = None,
) -> str:
    exclude_contains = exclude_contains or []

    for key, value in lookup.items():
        if key.startswith(prefix):
            if any(excl in key for excl in exclude_contains):
                continue
            return value
    return "N/A"


def _find_value_containing(
    lookup: dict,
    text: str,
    exclude_contains: list[str] | None = None,
) -> str:
    exclude_contains = exclude_contains or []

    for key, value in lookup.items():
        if text in key:
            if any(excl in key for excl in exclude_contains):
                continue
            return value
    return "N/A"


def _get_kpi_highlights(table_data: dict) -> dict:
    lookup = _table_to_lookup(table_data)

    kpi_cagr = _find_value_by_prefix(
        lookup,
        "%CAGR (",
    )

    kpi_profit = _find_value_by_prefix(
        lookup,
        "%Profit Net ",
    )

    kpi_roe = _find_value_containing(
        lookup,
        "ROE DuPont",
    )

    kpi_creante = _find_value_by_prefix(
        lookup,
        "Zile creanțe",
    )

    kpi_stoc = _find_value_by_prefix(
        lookup,
        "Zile stoc",
    )

    return {
        "kpi_cagr": kpi_cagr,
        "kpi_profit": kpi_profit,
        "kpi_roe": kpi_roe,
        "kpi_debt": kpi_creante,
        "kpi_stoc": kpi_stoc,
    }


def sanitize_pdf_text(text: str) -> str:
    if not text:
        return ""

    replacements = {
        "👉": "-",
        "🔷": "",
        "–": "-",
        "—": "-",
        "„": '"',
        "”": '"',
        "’": "'",
        "\u00a0": " ",   # non-breaking space
        "\u200b": "",    # zero-width space
    }

    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    return cleaned


def build_table_rows(table_data: dict) -> str:
    rows = ""

    indicators = table_data.get("Indicator", [])
    values = table_data.get("Valoare", [])

    for i in range(len(indicators)):
        indicator = indicators[i] if i < len(indicators) else "-"
        value = values[i] if i < len(values) else "-"

        rows += f"""
        <div class="row">
            <div class="indicator">{indicator}</div>
            <div class="value">{value}</div>
        </div>
        """

    return rows


def format_analysis_text(text: str) -> str:
    paragraphs = text.split("\n")
    formatted = ""

    for p in paragraphs:
        cleaned = p.strip()
        if not cleaned:
            continue

        if cleaned.startswith(("1.", "2.", "3.", "4.", "5.", "6.")):
            formatted += f"<h2>{cleaned}</h2>"
        elif cleaned.startswith("HOOK:"):
            formatted += f"<h2>{cleaned}</h2>"
        elif cleaned.startswith("INTERPRETARE:"):
            formatted += f"<h2>{cleaned}</h2>"
        elif cleaned.startswith("ÎNTREBĂRI:"):
            formatted += f"<h2>{cleaned}</h2>"
        elif cleaned.startswith("CUM POATE SPUNE AGENTUL:"):
            formatted += f"<h2>{cleaned}</h2>"
        elif cleaned.startswith("EVOLUȚIE:"):
            formatted += f"<h2>{cleaned}</h2>"
        elif cleaned.startswith("SEMNAL:"):
            formatted += f"<h2>{cleaned}</h2>"
        elif cleaned.startswith("- "):
            formatted += f"<p><strong>{cleaned}</strong></p>"
        else:
            formatted += f"<p>{cleaned}</p>"

    return formatted


def generate_pdf_report(
    company_info: dict,
    years_sorted: list,
    table_data: dict,
    analysis_text: str,
) -> bytes:
    template_path = Path(__file__).parent / "templates" / "report.html"
    logo_path = (Path(__file__).parent / "templates" / "tpc_logo.png").resolve().as_uri()

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    years_text = " · ".join(str(year) for year in years_sorted)
    table_rows = build_table_rows(table_data)

    clean_analysis_text = sanitize_pdf_text(analysis_text)
    formatted_analysis = format_analysis_text(clean_analysis_text)

    kpis = _get_kpi_highlights(table_data)

    html_content = template.render(
        logo_path=logo_path,
        company_name=company_info.get("company_name", "-"),
        cui=company_info.get("cui", "-"),
        caen=company_info.get("caen_code", "-"),
        caen_label=company_info.get("caen_label", "-"),
        years=years_text,
        table_rows=table_rows,
        interpretation=formatted_analysis,
        kpi_cagr=kpis["kpi_cagr"],
        kpi_profit=kpis["kpi_profit"],
        kpi_roe=kpis["kpi_roe"],
        kpi_debt=kpis["kpi_debt"],
        kpi_stoc=kpis["kpi_stoc"],
    )

    pdf_bytes = HTML(
        string=html_content,
        base_url=str((Path(__file__).parent / "templates").resolve()),
    ).write_pdf()

    return pdf_bytes