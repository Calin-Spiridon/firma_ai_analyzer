import streamlit as st
import pandas as pd

from app.analysis_service import build_company_analysis
from app.cache_manager import load_from_cache, save_to_cache
from app.claude_client import generate_tpc_analysis
from app.excel_log import append_company_log
from app.pdf_exporter import generate_pdf_report


def format_number(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_integer_number(value):
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value):
    return f"{value * 100:.1f}%".replace(".", ",")


def sanitize_filename(text: str) -> str:
    allowed = []
    for char in text:
        if char.isalnum() or char in [" ", "_", "-"]:
            allowed.append(char)
    cleaned = "".join(allowed).strip().replace(" ", "_")
    return cleaned or "Company"


def get_year_dict(data: dict, year: int):
    if year in data:
        return data[year]
    if str(year) in data:
        return data[str(year)]
    return {}


st.set_page_config(page_title="Company Analyser by TPC", layout="wide")

if "result" not in st.session_state:
    st.session_state.result = None

if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = None

st.title("Company Analyzer by TPC")
st.write("Introdu CUI-ul unei companii și generează analiza financiară.")

cui_input = st.text_input("CUI companie", value="")
use_cache = st.checkbox("Folosește cache dacă există", value=False)

col_action_1, col_action_2 = st.columns([1, 1])

with col_action_1:
    analyze_clicked = st.button("Analizează compania")

with col_action_2:
    refresh_claude_clicked = st.button("Regenerează interpretarea Claude")

if analyze_clicked:
    if not cui_input.strip().isdigit():
        st.error("Te rog introdu un CUI valid, format doar din cifre.")
    else:
        cui = cui_input.strip()

        try:
            with st.spinner("Se procesează compania..."):
                cached = load_from_cache(cui) if use_cache else None

                if cached:
                    result = cached["data"]
                    st.info(f"Date încărcate din cache. Salvat la: {cached['cached_at']}")
                else:
                    result = build_company_analysis(int(cui))
                    save_to_cache(cui, result)
                    st.success("Date extrase din API și salvate în cache.")

            st.session_state.result = result
            st.session_state.analysis_text = None

            _company_info = result["company_info"]
            _latest_year = result["latest_year"]
            _indicators = get_year_dict(result["indicators_by_year"], _latest_year)
            _cagr_ca = result["cagr_ca"]
            append_company_log(_company_info, _latest_year, _indicators, _cagr_ca)

        except Exception as e:
            st.error(f"A apărut o eroare: {str(e)}")

if st.session_state.result:
    result = st.session_state.result

    company_info = result["company_info"]
    latest_year = result["latest_year"]
    years_sorted = result["years_sorted"]
    indicators = get_year_dict(result["indicators_by_year"], latest_year)
    cagr_ca = result["cagr_ca"]

    st.subheader("Companie")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Denumire:** {company_info.get('company_name') or '-'}")
        st.write(f"**CUI:** {company_info.get('cui') or '-'}")

    with col2:
        st.write(f"**CAEN:** {company_info.get('caen_code') or '-'}")
        st.write(f"**Denumire CAEN:** {company_info.get('caen_label') or '-'}")

    st.subheader("Ani analizati")
    years_text = " · ".join(str(year) for year in years_sorted)
    st.write(years_text)

    st.subheader(f"Indicatori {latest_year}")

    table_data = {
        "Indicator": [
            "Marja profit",
            "Sales on assets",
            "Equity multiplier",
            "Zile stoc",
            "Zile creanțe",
            "Capital blocat",
            "Capital blocat / CA",
            "Salariu mediu lunar",
            "Salariu anual",
            "Fond salarial",
            "Pondere fond salarial",
            "Productivitate",
            "Randament",
            "Debt ratio",
            "Debt to equity",
            "Datorii vs cash block",
            "Datorii / CA",
            "ROE DuPont",
            f"CAGR CA ({years_sorted[0]}-{years_sorted[-1]})",
        ],
        "Valoare": [
            format_percent(indicators["profit_margin"]),
            format_number(indicators["sales_on_assets"]),
            format_number(indicators["equity_multiplier"]),
            format_number(indicators["zile_stoc"]),
            format_number(indicators["zile_creante"]),
            format_integer_number(indicators["capital_blocat"]),
            format_percent(indicators["capital_blocat_ratio"]),
            format_number(indicators["salariu_mediu_lunar"]),
            format_integer_number(indicators["salariu_anual"]),
            format_integer_number(indicators["fond_salarial"]),
            format_percent(indicators["pondere_fond_salarial"]),
            format_integer_number(indicators["productivitate"]),
            format_number(indicators["randament"]),
            format_percent(indicators["debt_ratio"]),
            format_number(indicators["debt_to_equity"]),
            format_number(indicators["datorii_vs_cash_block"]),
            format_percent(indicators["datorii_ratio_ca"]),
            format_percent(indicators["roe_dupont"]),
            format_percent(cagr_ca) if cagr_ca is not None else "N/A",
        ]
    }

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(
        "* Fondul salarial a fost calculat estimativ, folosind salariul mediu brut din România corespunzător anului analizat (2024 sau 2025, după caz)."
    )

    need_generate = st.session_state.analysis_text is None or refresh_claude_clicked

    if need_generate:
        try:
            with st.spinner("Se generează analiza cu Claude..."):
                st.session_state.analysis_text = generate_tpc_analysis(
                    company_info=company_info,
                    years_sorted=years_sorted,
                    latest_year=latest_year,
                    indicators=indicators,
                    cagr_ca=cagr_ca,
                )
        except Exception as e:
            st.error(f"A apărut o eroare la Claude: {str(e)}")

    st.subheader("Interpretare TPC")
    if st.session_state.analysis_text:
        st.write(st.session_state.analysis_text)

        pdf_bytes = generate_pdf_report(
            company_info=company_info,
            years_sorted=years_sorted,
            table_data=table_data,
            analysis_text=st.session_state.analysis_text,
        )

        company_name_for_file = sanitize_filename(company_info.get("company_name", "Company"))

        st.download_button(
            label="Descarcă PDF",
            data=pdf_bytes,
            file_name=f"TPC_Analysis_{company_name_for_file}.pdf",
            mime="application/pdf",
        )

    with st.expander("Date brute pe ultimii 5 ani"):
        st.json(result["normalized_by_year"])
