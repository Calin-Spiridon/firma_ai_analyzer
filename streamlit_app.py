import pandas as pd
import streamlit as st

from app.analysis_service import build_company_analysis
from app.cache_manager import load_from_cache, save_to_cache
from app.openai_client import generate_tpc_analysis_openai
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
    if result is None:
        return

    company_info = result["company_info"]
    years_sorted = result["years_sorted"]
    latest_year = result["latest_year"]
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

    refresh_ai_clicked = st.button("Regenerează interpretarea AI")
    need_generate = st.session_state.analysis_text is None or refresh_ai_clicked

    if need_generate:
        try:
            with st.spinner("Se generează analiza cu AI..."):
                st.session_state.analysis_text = generate_tpc_analysis_openai(
                    company_info=company_info,
                    years_sorted=years_sorted,
                    latest_year=latest_year,
                    indicators=indicators,
                    cagr_ca=cagr_ca,
                )
        except Exception as e:
            st.error(f"A apărut o eroare la generarea analizei: {str(e)}")

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
    if "local_results" not in st.session_state:
        st.session_state.local_results = []
    if "enriched_results" not in st.session_state:
        st.session_state.enriched_results = []

    # ════════════════════════════════════════════════════════════════════
    # PASUL 1 — Filtrare din baza de date locală
    # ════════════════════════════════════════════════════════════════════
    st.subheader("Pasul 1 — Filtrare companii din baza de date locală")

    col1, col2, col3 = st.columns(3)
    with col1:
        min_turnover = st.number_input(
            "CA minimă (RON)", min_value=0.0, value=0.0, step=1000000.0,
            key="p1_ca_min"
        )
    with col2:
        max_turnover = st.number_input(
            "CA maximă (RON)", min_value=0.0, value=0.0, step=1000000.0,
            key="p1_ca_max"
        )
    with col3:
        min_employees = st.number_input(
            "Nr. minim angajați", min_value=0, value=0, step=10,
            key="p1_emp"
        )

    col4, col5 = st.columns(2)
    with col4:
        county_filter = st.selectbox(
            "Județ",
            options=["Toate", "Municipiul Bucuresti", "Ilfov"],
            key="p1_judet"
        )
    with col5:
        max_results = st.number_input(
            "Număr maxim rezultate", min_value=10, max_value=500, value=100, step=10,
            key="p1_max"
        )

    search_clicked = st.button("Filtrează", key="btn_search_local")

    if search_clicked:
        try:
            from app.local_db_service import search_local_db
            results = search_local_db(
                min_turnover=float(min_turnover) if min_turnover > 0 else None,
                max_turnover=float(max_turnover) if max_turnover > 0 else None,
                min_employees=int(min_employees) if min_employees > 0 else None,
                county=None if county_filter == "Toate" else county_filter,
                max_results=int(max_results),
            )
            st.session_state.local_results = results
            st.session_state.enriched_results = []
            st.success(f"✅ {len(results)} companii găsite.")

            # Download CSV rezultate filtrate
            df_csv = pd.DataFrame(results)
            df_csv = df_csv.rename(columns={
                "cui": "CUI",
                "denumire": "Denumire",
                "judet": "Județ",
                "localitate": "Localitate",
                "caen": "CAEN",
                "cifra_afaceri": "Cifră de afaceri",
                "angajati": "Angajați",
                "profit_net": "Profit net",
            })
            csv_filtrat = df_csv.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇️ Descarcă CSV rezultate filtrate",
                data=csv_filtrat,
                file_name="rezultate_filtrate.csv",
                mime="text/csv",
                key="btn_dl_filtrat",
            )

        except Exception as e:
            st.error(f"Eroare: {str(e)}")
            

    # ── Tabel Pasul 1 cu selecție ───────────────────────────────────────
    local_results = st.session_state.local_results

    if local_results:
        st.markdown(f"**{len(local_results)} companii — selectează pentru enrichment Termene:**")

        selected_cuis = []
        for item in local_results:
            col_chk, col_info = st.columns([1, 10])
            with col_chk:
                checked = st.checkbox("", key=f"chk_{item['cui']}", value=False)
            with col_info:
                ca_fmt = f"{item['cifra_afaceri']:,.0f}" if item['cifra_afaceri'] else "-"
                st.write(
                    f"**{item['denumire']}** · CUI: {item['cui']} · "
                    f"CAEN: {item['caen']} · CA: {ca_fmt} RON · "
                    f"Angajați: {item['angajati']} · {item['judet']}"
                )
            if checked:
                selected_cuis.append(item["cui"])

        st.markdown(f"*{len(selected_cuis)} companii selectate*")

        # ════════════════════════════════════════════════════════════════
        # PASUL 2 — Enrichment Termene
        # ════════════════════════════════════════════════════════════════
        st.divider()
        st.subheader("Pasul 2 — Enrichment Termene pentru companiile selectate")
        st.caption(f"⚠️ Fiecare companie consumă 1 request din limita de 500.")

        enrich_clicked = st.button(
            f"Enrichment Termene ({len(selected_cuis)} selectate)",
            disabled=(len(selected_cuis) == 0),
            key="btn_enrich",
        )

        if enrich_clicked and selected_cuis:
            try:
                with st.spinner(f"Se procesează {len(selected_cuis)} companii..."):
                    enriched_rows = enrich_companies(selected_cuis)
                df = pd.DataFrame(enriched_rows)
                if "turnover" in df.columns:
                    df = df.sort_values(
                        by="turnover",
                        key=lambda x: pd.to_numeric(x, errors="coerce"),
                        ascending=False,
                    )
                st.session_state.enriched_results = df.to_dict("records")
                st.success(f"✅ {len(df)} companii procesate.")
            except Exception as e:
                st.error(f"Eroare enrichment: {str(e)}")

        # ════════════════════════════════════════════════════════════════
        # PASUL 3 — Tabel final cu buton Analizează
        # ════════════════════════════════════════════════════════════════
        enriched_results = st.session_state.enriched_results

        if enriched_results:
            st.divider()
            st.subheader("Pasul 3 — Rezultate finale")

            df_display = format_enrichment_dataframe(pd.DataFrame(enriched_results))
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            csv_data = df_display.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Descarcă CSV",
                data=csv_data,
                file_name="rezultate_enrichment.csv",
                mime="text/csv",
                key="btn_dl_enrichment",
            )

            st.markdown("**Analizează o companie:**")
            for row in enriched_results:
                cui = row.get("cui")
                nume = row.get("company_name") or str(cui)
                col_info, col_btn = st.columns([8, 2])
                with col_info:
                    st.write(f"**{nume}** · CUI: {cui}")
                with col_btn:
                    if st.button("Analizează", key=f"btn_analyze_{cui}"):
                        try:
                            with st.spinner(f"Se analizează {nume}..."):
                                result = build_company_analysis(int(cui))
                                save_to_cache(str(cui), result)
                            st.session_state.result = result
                            st.session_state.analysis_text = None
                            st.success("✅ Gata! Vezi tab-ul 'Analiză companie'.")
                        except Exception as e:
                            st.error(f"Eroare: {str(e)}")

  

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

    analyze_clicked = st.button("Analizează compania", key="btn_analyze_main")

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