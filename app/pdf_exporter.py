import os
from pathlib import Path
from jinja2 import Template

os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib:" + os.environ.get(
    "DYLD_FALLBACK_LIBRARY_PATH", ""
)

from weasyprint import HTML


def build_table_rows(table_data: dict) -> str:
    rows = ""

    for i in range(len(table_data["Indicator"])):
        rows += f"""
        <div class="row">
            <div class="indicator">{table_data["Indicator"][i]}</div>
            <div class="value">{table_data["Valoare"][i]}</div>
        </div>
        """

    return rows


def format_analysis_text(text: str) -> str:
    text = text.replace("Interpretare:", "<h2>1. Interpretare TPC</h2>")
    text = text.replace("Concluzie:", "<h2>2. Concluzie TPC</h2>")

    paragraphs = text.split("\n")
    formatted = ""

    for p in paragraphs:
        cleaned = p.strip()
        if not cleaned:
            continue

        if cleaned.startswith("<h2>"):
            formatted += cleaned
        else:
            formatted += f"<p>{cleaned}</p>"

    return formatted


def generate_pdf_report(
    company_info: dict,
    years_sorted: list,
    table_data: dict,
    analysis_text: str
) -> bytes:
    template_path = Path(__file__).parent / "templates" / "report.html"
    logo_path = (Path(__file__).parent / "templates" / "tpc_logo.png").resolve().as_uri()

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    years_text = " · ".join(str(year) for year in years_sorted)
    table_rows = build_table_rows(table_data)
    formatted_analysis = format_analysis_text(analysis_text)

    html_content = template.render(
        logo_path=logo_path,
        company_name=company_info.get("company_name", "-"),
        cui=company_info.get("cui", "-"),
        caen=company_info.get("caen_code", "-"),
        caen_label=company_info.get("caen_label", "-"),
        years=years_text,
        table_rows=table_rows,
        interpretation=formatted_analysis,
        kpi_cagr=table_data["Valoare"][-1],
        kpi_profit=table_data["Valoare"][0],
        kpi_roe=table_data["Valoare"][17],
        kpi_debt=table_data["Valoare"][13],
        kpi_stoc=table_data["Valoare"][3],
    )

    pdf_bytes = HTML(string=html_content, base_url=str((Path(__file__).parent / "templates").resolve())).write_pdf()

    return pdf_bytes