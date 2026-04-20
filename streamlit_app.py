import pandas as pd
import streamlit as st

from app.analysis_service import build_company_analysis
from app.cache_manager import load_from_cache, save_to_cache
from app.claude_client import generate_tpc_analysis
from app.company_enrichment_service import enrich_companies
from app.excel_log import append_company_log
from app.pdf_exporter import generate_pdf_report
from app.termene_client import TermeneClient


# =========================
# FORMATTERS
# =========================
def format_number(value):
    if value is None:
        return "-"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_integer_number(value):
    if value is None:
        return "-"
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value, digits=1):
    if value is None:
        return "-"
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def format_enrichment_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df_display = df.copy()

    if "turnover" in df_display.columns:
        df_display["turnover"] = df_display["turnover"].apply(
            lambda x: format_integer_number(x) if pd.notnull(x) else "-"
        )

    if "profit_net" in df_display.columns:
        df_display["profit_net"] = df_display["profit_net"].apply(
            lambda x: format_integer_number(x) if pd.notnull(x) else "-"
        )

    if "employees" in df_display.columns:
        df_display["employees"] = df_display["employees"].apply(
            lambda x: format_integer_number(x) if pd.notnull(x) else "-"
        )

    if "profit_margin" in df_display.columns:
        df_display["profit_margin"] = df_display["profit_margin"].apply(
            lambda x: format_percent(x, digits=2) if pd.notnull(x) else "-"
        )

    if "cagr_ca" in df_display.columns:
        df_display["cagr_ca"] = df_display["cagr_ca"].apply(
            lambda x: format_percent(x, digits=2) if pd.notnull(x) else "-"
        )

    df_display = df_display.rename(
        columns={
            "cui": "CUI",
            "company_name": "Denumire",
            "caen_code": "CAEN",
            "caen_label": "Activitate",
            "latest_year": "An",
            "turnover": "Cifră de afaceri",
            "employees": "Angajați",
            "profit_net": "Profit net",
            "profit_margin": "% Profit",
            "cagr_ca": "% CAGR",
            "phone": "Telefon",
            "email": "Email",
            "shareholders": "Asociați",
            "status": "Status",
        }
    )

    return df_display


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
            format_percent(indicators.get("profit_margin"), digits=2),
            format_number(indicators.get("sales_on_assets")),
            format_number(indicators.get("equity_multiplier")),
            format_integer_number(indicators.get("zile_stoc")),
            format_integer_number(indicators.get("zile_creante")),
            format_integer_number(indicators.get("capital_blocat")),
            format_percent(indicators.get("capital_blocat_ratio"), digits=1),
            format_integer_number(indicators.get("salariu_mediu_lunar")),
            format_integer_number(indicators.get("salariu_anual")),
            format_integer_number(indicators.get("fond_salarial")),
            format_percent(indicators.get("pondere_fond_salarial"), digits=1),
            format_integer_number(indicators.get("productivitate")),
            format_number(indicators.get("randament")),
            format_percent(indicators.get("debt_ratio"), digits=1),
            format_number(indicators.get("debt_to_equity")),
            format_percent(indicators.get("datorii_ratio_ca"), digits=1),
            format_percent(indicators.get("roe_dupont"), digits=1),
            format_percent(cagr_ca, digits=1) if cagr_ca is not None else "N/A",
        ],
    }


# =========================
# ANALYSIS TAB HELPERS
# =========================
def run_company_analysis(cui: str, use_cache: bool):
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


def render_company_analysis_result():
    result = st.session_state.result
    if not result:
        return

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

    refresh_claude_clicked = st.button("Regenerează interpretarea Claude")
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
            file_name=f"TPC Analysis {company_info.get('company_name', company_info.get('cui', 'company'))}.pdf",
            mime="application/pdf",
        )

    with st.expander("Date brute pe ultimii ani disponibili"):
        st.json(result["normalized_by_year"])


# =========================
# SEARCH TAB HELPERS
# =========================
def render_search_tab():
    st.subheader("Căutare companii")
    st.write(
        "Aici pregătim modulul de screening companii după criterii. "
        "Momentan poți testa enrichment-ul manual pe listă de CUI-uri. "
        "Search-ul real din Termene îl legăm când avem payload-ul de filtrare."
    )

    county = st.text_input("Județ", value="")
    min_turnover = st.number_input(
        "Cifra de afaceri minimă (RON)",
        min_value=0.0,
        value=0.0,
        step=100000.0,
    )
    min_employees = st.number_input(
        "Număr minim angajați",
        min_value=0,
        value=0,
        step=1,
    )

    batch_size = st.number_input(
        "Batch viitor pentru enrichment",
        min_value=1,
        max_value=100,
        value=20,
        step=1,
    )

    col1, col2 = st.columns(2)
    with col1:
        search_clicked = st.button("Caută companii")
    with col2:
        st.button("Procesează următoarele N", disabled=True)

    if search_clicked:
        filters = {
            "county": county.strip() or None,
            "min_turnover": float(min_turnover) if min_turnover > 0 else None,
            "min_employees": int(min_employees) if min_employees > 0 else None,
            "batch_size": int(batch_size),
        }

        try:
            client = TermeneClient()
            _ = client.search_companies(filters)
            st.success("Search-ul este conectat.")
        except NotImplementedError as e:
            st.warning(str(e))
            st.info(
                "Momentan endpointul real de search nu este încă legat. "
                "Până atunci poți folosi enrichment-ul manual de mai jos."
            )
        except Exception as e:
            st.error(f"A apărut o eroare la search: {str(e)}")

    st.divider()
    st.markdown("### Structura pregătită pentru etapa următoare")

    preview_df = pd.DataFrame(
        [
            {
                "Poziție": 1,
                "Denumire": "Exemplu SRL",
                "CUI": "12345678",
                "Județ": county or "București",
                "Cifra Afaceri": "15.000.000",
                "Nr. Angajați": "45",
                "Profit %": "-",
                "CAGR %": "-",
                "Telefon": "-",
                "Email": "-",
                "Acționari": "-",
                "Status": "pending",
            }
        ]
    )

    st.dataframe(preview_df, use_container_width=True, hide_index=True)

    csv_data = preview_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descarcă CSV exemplu",
        data=csv_data,
        file_name="search_results_preview.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown("### Test enrichment manual după CUI-uri")

    manual_cui_input = st.text_area(
        "Introdu CUI-uri separate prin virgulă",
        value="27758121",
        height=120,
    )

    run_manual_enrichment = st.button("Rulează enrichment manual")

    if run_manual_enrichment:
        try:
            cui_list = [
                int(x.strip())
                for x in manual_cui_input.split(",")
                if x.strip()
            ]

            with st.spinner("Se rulează enrichment-ul..."):
                enriched_rows = enrich_companies(cui_list)

            df_enriched = pd.DataFrame(enriched_rows)
            df_enriched_display = format_enrichment_dataframe(df_enriched)

            if "Cifră de afaceri" in df_enriched_display.columns:
                df_enriched_display = df_enriched_display.sort_values(
                    by="Cifră de afaceri",
                    ascending=False,
                )

            st.dataframe(df_enriched_display, use_container_width=True, hide_index=True)

            csv_enriched = df_enriched_display.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Descarcă CSV enrichment manual",
                data=csv_enriched,
                file_name="manual_enrichment_results.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"Eroare la enrichment manual: {str(e)}")


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Company Analyser by TPC", layout="wide")

if "result" not in st.session_state:
    st.session_state.result = None

if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = None


# =========================
# UI
# =========================
st.title("Company Analyser by TPC")
tab_analysis, tab_search = st.tabs([
    "Analiză companie",
    "Căutare companii",
])

with tab_analysis:
    st.write("Introdu CUI-ul unei companii și generează analiza financiară.")

    cui_input = st.text_input("CUI companie", value="")
    use_cache = st.checkbox("Folosește cache dacă există", value=False)

    analyze_clicked = st.button("Analizează compania")

    if analyze_clicked:
        if not cui_input.strip().isdigit():
            st.error("Te rog introdu un CUI valid, format doar din cifre.")
        else:
            try:
                run_company_analysis(cui_input.strip(), use_cache)
            except Exception as e:
                st.error(f"A apărut o eroare: {str(e)}")

    render_company_analysis_result()

with tab_search:
    render_search_tab()