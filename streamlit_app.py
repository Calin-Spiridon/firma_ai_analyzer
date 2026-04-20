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


def format_percent(value, digits=1):
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def get_year_dict(data: dict, year: int):
    if year in data:
        return data[year]
    if str(year) in data:
        return data[str(year)]
    return {}


def build_table_data(indicators: dict, cagr_ca: float, years_sorted: list[int]) -> dict:
    start_year = years_sorted[0]
    end_year = years_sorted[-1]

    return {
        "Indicator": [
            "%Profit Net (Profit Net/CA)",
            "Sales on asset (CA/Active totale)",
            "Equity multiplier (Active totale/Capital Propiu)",
            "Zile stoc (Stoc/CA medie zilnică)",
            "Zile creanțe (Creanțe/CA medie zilnică)",
            "Capital Blocat (Creanțe + Stocuri)",
            "%Capital Blocat (Capital Blocat / CA)",
            "Salariu brut mediu lunar (salariu brut mediu pe economie)",
            "Salariu brut anual (Salariu mediu brut lunar*12)",
            "Fond salarial (Salariu brut anual*număr angajați)",
            "%Fond Salarial (Fond salarial/CA)",
            "Productivitate (CA/Nr Angajați)",
            "Randament angajat (Productivitate/Salariu brut anual per angajat)",
            "Debt Ratio (Datorii totale/Active totale)",
            "Debt to equity (Datorii totale/Capital Propiu)",
            "%Datorii (Datorii totale/CA)",
            "ROE DuPont (%Profit Net*Sales on asset*equity multiplier)",
            f"%CAGR ({start_year} - {end_year}) - creștere medie anuală",
        ],
        "Valoare": [
            format_percent(indicators["profit_margin"], digits=2),
            format_number(indicators["sales_on_assets"]),
            format_number(indicators["equity_multiplier"]),
            format_integer_number(indicators["zile_stoc"]),
            format_integer_number(indicators["zile_creante"]),
            format_integer_number(indicators["capital_blocat"]),
            format_percent(indicators["capital_blocat_ratio"], digits=1),
            format_integer_number(indicators["salariu_mediu_lunar"]),
            format_integer_number(indicators["salariu_anual"]),
            format_integer_number(indicators["fond_salarial"]),
            format_percent(indicators["pondere_fond_salarial"], digits=1),
            format_integer_number(indicators["productivitate"]),
            format_number(indicators["randament"]),
            format_percent(indicators["debt_ratio"], digits=1),
            format_number(indicators["debt_to_equity"]),
            format_percent(indicators["datorii_ratio_ca"], digits=1),
            format_percent(indicators["roe_dupont"], digits=1),
            format_percent(cagr_ca, digits=1) if cagr_ca is not None else "N/A",
        ],
    }


st.set_page_config(page_title="Company Analyser by TPC", layout="wide")

if "result" not in st.session_state:
    st.session_state.result = None

if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = None

st.title("Company Analyser by TPC")
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

            company_info_for_log = result["company_info"]
            latest_year_for_log = result["latest_year"]
            indicators_for_log = get_year_dict(result["indicators_by_year"], latest_year_for_log)
            cagr_for_log = result["cagr_ca"]

            append_company_log(
                company_info_for_log,
                latest_year_for_log,
                indicators_for_log,
                cagr_for_log,
            )

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

    st.subheader("Ani analizați")
    years_text = " · ".join(str(year) for year in years_sorted)
    st.write(years_text)

    st.subheader(f"Indicatori {latest_year}")

    table_data = build_table_data(
        indicators=indicators,
        cagr_ca=cagr_ca,
        years_sorted=years_sorted,
    )

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(
    "* Fondul salarial a fost calculat estimativ, folosind salariul mediu brut din România corespunzător anului analizat (2024 sau 2025, după caz).\n"
    "* Analiza se bazează pe date publice disponibile și nu implică validarea directă cu compania."
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

        st.download_button(
            label="Descarcă PDF",
            data=pdf_bytes,
            file_name=f"tpc_analysis_{company_info.get('cui', 'company')}.pdf",
            mime="application/pdf",
        )

    with st.expander("Date brute pe ultimii 5 ani"):
        st.json(result["normalized_by_year"])