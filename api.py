from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import traceback
import os

app = Flask(__name__)
CORS(app)


def _validate_cui(cui_str: str) -> bool:
    digits = cui_str.lstrip("0") or "0"
    if len(digits) < 2 or len(digits) > 10:
        return False
    key = [7, 5, 3, 2, 1, 7, 5, 3, 2]
    padded = digits[:-1].zfill(9)
    total = sum(int(padded[i]) * key[i] for i in range(9))
    control = (total * 10) % 11
    if control == 10:
        control = 0
    return control == int(digits[-1])


def _fmt_pct(v, d=2):
    if v is None: return "N/A"
    return f"{v * 100:.{d}f}%".replace(".", ",")

def _fmt_num(v, d=2):
    if v is None: return "N/A"
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _fmt_int(v):
    if v is None: return "N/A"
    return f"{int(v):,}".replace(",", ".")


def _get_year_dict(data, year):
    if year in data: return data[year]
    if str(year) in data: return data[str(year)]
    return {}


def _calculate_yoy_change(current, previous):
    if current is None or previous in (None, 0): return None
    return (current - previous) / previous


def _build_table_data(result):
    from app.utils import calculate_cagr

    indicators_by_year = result["indicators_by_year"]
    normalized_by_year = result["normalized_by_year"]
    years_sorted       = result["years_sorted"]
    latest_year        = result["latest_year"]
    cagr_ca            = result["cagr_ca"]

    i_cur  = _get_year_dict(indicators_by_year, latest_year)
    prev1  = years_sorted[-2] if len(years_sorted) >= 2 else None
    prev2  = years_sorted[-3] if len(years_sorted) >= 3 else None
    i_p1   = _get_year_dict(indicators_by_year, prev1) if prev1 else {}
    i_p2   = _get_year_dict(indicators_by_year, prev2) if prev2 else {}

    start_year = years_sorted[0]
    end_year   = years_sorted[-1]

    # CAGR 3 ani
    cagr_3y = None
    cagr_3y_label = "%CAGR ultimii 3 ani - creștere medie anuală"
    if len(years_sorted) >= 3:
        y3s = years_sorted[-3]
        y3e = years_sorted[-1]
        cagr_3y_label = f"%CAGR ({y3s} - {y3e}) - creștere medie anuală"
        ca_s = _get_year_dict(normalized_by_year, y3s).get("cifra_afaceri")
        ca_e = _get_year_dict(normalized_by_year, y3e).get("cifra_afaceri")
        if ca_s not in (None, 0) and ca_e is not None and y3e > y3s:
            cagr_3y = calculate_cagr(ca_s, ca_e, y3e - y3s)

    # YoY CA
    yoy_ca = None
    yoy_ca_label = "%Dinamica CA vs anul anterior"
    if prev1:
        yoy_ca_label = f"%Dinamica CA {latest_year} vs {prev1}"
        cur_ca  = _get_year_dict(normalized_by_year, latest_year).get("cifra_afaceri")
        prev_ca = _get_year_dict(normalized_by_year, prev1).get("cifra_afaceri")
        yoy_ca  = _calculate_yoy_change(cur_ca, prev_ca)

    indicators = [
        {"name": f"%Profit Net {latest_year} (Profit Net/CA)",                          "value": _fmt_pct(i_cur.get("profit_margin"), 2)},
        {"name": f"%Profit Net {prev1} (Profit Net/CA)" if prev1 else "%Profit Net an anterior", "value": _fmt_pct(i_p1.get("profit_margin"), 2) if prev1 else "N/A"},
        {"name": f"%Profit Net {prev2} (Profit Net/CA)" if prev2 else "%Profit Net cu 2 ani în urmă", "value": _fmt_pct(i_p2.get("profit_margin"), 2) if prev2 else "N/A"},
        {"name": "Sales on asset (CA/Active totale)",                                    "value": _fmt_num(i_cur.get("sales_on_assets"))},
        {"name": "Equity multiplier (Active totale/Capital Propriu)",                    "value": _fmt_num(i_cur.get("equity_multiplier"))},
        {"name": "Zile stoc (Stoc/CA medie zilnică)",                                    "value": _fmt_int(i_cur.get("zile_stoc"))},
        {"name": "Zile creanțe (Creanțe/CA medie zilnică)",                              "value": _fmt_int(i_cur.get("zile_creante"))},
        {"name": "Capital Blocat (Creanțe + Stocuri)",                                   "value": _fmt_int(i_cur.get("capital_blocat"))},
        {"name": "%Capital Blocat (Capital Blocat / CA)",                                "value": _fmt_pct(i_cur.get("capital_blocat_ratio"), 1)},
        {"name": "Salariu brut mediu lunar (salariu brut mediu pe economie)",            "value": _fmt_int(i_cur.get("salariu_mediu_lunar")) + " lei"},
        {"name": "Salariu brut anual (Salariu mediu brut lunar*12)",                     "value": _fmt_int(i_cur.get("salariu_anual"))},
        {"name": "Fond salarial (Salariu brut anual*număr angajați)",                    "value": _fmt_int(i_cur.get("fond_salarial"))},
        {"name": "%Fond Salarial (Fond salarial/CA)",                                    "value": _fmt_pct(i_cur.get("pondere_fond_salarial"), 1)},
        {"name": "Productivitate (CA/Nr Angajați)",                                      "value": _fmt_int(i_cur.get("productivitate"))},
        {"name": "Randament angajat (Productivitate/Salariu brut anual per angajat)",    "value": _fmt_num(i_cur.get("randament"))},
        {"name": "Debt Ratio (Datorii totale/Active totale)",                            "value": _fmt_pct(i_cur.get("debt_ratio"), 1)},
        {"name": "Debt to equity (Datorii totale/Capital Propriu)",                      "value": _fmt_num(i_cur.get("debt_to_equity"))},
        {"name": "%Datorii (Datorii totale/CA)",                                         "value": _fmt_pct(i_cur.get("datorii_ratio_ca"), 1)},
        {"name": "ROE DuPont (%Profit Net*Sales on asset*equity multiplier)",            "value": _fmt_pct(i_cur.get("roe_dupont"), 1)},
        {"name": f"%CAGR ({start_year} - {end_year}) - creștere medie anuală",          "value": _fmt_pct(cagr_ca, 1) if cagr_ca else "N/A"},
        {"name": cagr_3y_label,                                                          "value": _fmt_pct(cagr_3y, 1) if cagr_3y else "N/A"},
        {"name": yoy_ca_label,                                                           "value": _fmt_pct(yoy_ca, 1) if yoy_ca else "N/A"},
    ]

    # Format dict pentru pdf_exporter
    table_data = {
        "Indicator": [r["name"] for r in indicators],
        "Valoare":   [r["value"] for r in indicators],
    }

    return indicators, table_data


def _get_dynamic_inputs(result):
    """Extrage datele necesare pentru generate_tpc_dynamic_insight_openai"""
    from app.utils import calculate_cagr

    years_sorted       = result["years_sorted"]
    latest_year        = result["latest_year"]
    indicators_by_year = result["indicators_by_year"]
    normalized_by_year = result["normalized_by_year"]

    years_last_3 = years_sorted[-3:] if len(years_sorted) >= 3 else years_sorted

    profit_margin_last_3y = []
    for y in years_last_3:
        ind = _get_year_dict(indicators_by_year, y)
        profit_margin_last_3y.append(ind.get("profit_margin"))

    cagr_3y = None
    if len(years_last_3) >= 3:
        y3s = years_last_3[0]
        y3e = years_last_3[-1]
        ca_s = _get_year_dict(normalized_by_year, y3s).get("cifra_afaceri")
        ca_e = _get_year_dict(normalized_by_year, y3e).get("cifra_afaceri")
        if ca_s not in (None, 0) and ca_e is not None and y3e > y3s:
            cagr_3y = calculate_cagr(ca_s, ca_e, y3e - y3s)

    revenue_growth_last_year = None
    if len(years_sorted) >= 2:
        prev_y  = years_sorted[-2]
        cur_ca  = _get_year_dict(normalized_by_year, latest_year).get("cifra_afaceri")
        prev_ca = _get_year_dict(normalized_by_year, prev_y).get("cifra_afaceri")
        revenue_growth_last_year = _calculate_yoy_change(cur_ca, prev_ca)

    return {
        "profit_margin_last_3y":   profit_margin_last_3y,
        "cagr_3y":                 cagr_3y,
        "revenue_growth_last_year": revenue_growth_last_year,
        "years_last_3":            years_last_3,
    }


def _parse_cui(cui_param):
    cui_clean = "".join(filter(str.isdigit, cui_param.strip()))
    if not cui_clean or len(cui_clean) < 2 or len(cui_clean) > 10:
        return None, jsonify({"error": "CUI invalid"}), 400
    if not _validate_cui(cui_clean):
        return None, jsonify({"error": "CUI invalid — cifra de control nu este corectă"}), 400
    return int(cui_clean), None, None


# ─────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "TPC Analyzer API v2"})


# ─────────────────────────────────────────────
@app.route("/analyze")
def analyze():
    """
    GET /analyze?cui=...
    Returnează datele companiei + tabel indicatori FĂRĂ interpretare AI.
    Interpretarea se cere separat cu /ai/concluzie, /ai/dinamica, /ai/speech
    """
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code

    try:
        from app.analysis_service import build_company_analysis

        result = build_company_analysis(cui)
        indicators_table, _ = _build_table_data(result)

        return jsonify({
            "success":        True,
            "company": {
                "name":      result["company_info"].get("company_name"),
                "cui":       str(cui),
                "caen":      result["company_info"].get("caen_code"),
                "caen_desc": result["company_info"].get("caen_label"),
            },
            "years":          result["years_sorted"],
            "latest_year":    result["latest_year"],
            "indicators_table": indicators_table,
            "cagr_ca":        _fmt_pct(result["cagr_ca"], 1) if result["cagr_ca"] else "N/A",
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
@app.route("/ai/concluzie")
def ai_concluzie():
    """GET /ai/concluzie?cui=... → Interpretare TPC completă"""
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code

    try:
        from app.analysis_service import build_company_analysis
        from app.openai_client import generate_tpc_analysis_openai

        result   = build_company_analysis(cui)
        i        = _get_year_dict(result["indicators_by_year"], result["latest_year"])

        text = generate_tpc_analysis_openai(
            company_info=result["company_info"],
            years_sorted=result["years_sorted"],
            latest_year=result["latest_year"],
            indicators=i,
            cagr_ca=result["cagr_ca"],
        )
        return jsonify({"success": True, "mode": "concluzie", "text": text})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
@app.route("/ai/dinamica")
def ai_dinamica():
    """GET /ai/dinamica?cui=... → Dinamica Companie"""
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code

    try:
        from app.analysis_service import build_company_analysis
        from app.openai_dynamic_client import generate_tpc_dynamic_insight_openai

        result  = build_company_analysis(cui)
        dynamic = _get_dynamic_inputs(result)

        text = generate_tpc_dynamic_insight_openai(
            company_info=result["company_info"],
            profit_margin_last_3y=dynamic["profit_margin_last_3y"],
            cagr_3y=dynamic["cagr_3y"],
            revenue_growth_last_year=dynamic["revenue_growth_last_year"],
            years_last_3=dynamic["years_last_3"],
        )
        return jsonify({"success": True, "mode": "dinamica", "text": text})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
@app.route("/ai/speech")
def ai_speech():
    """GET /ai/speech?cui=... → Speech Agent"""
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code

    try:
        from app.analysis_service import build_company_analysis
        from app.openai_speech_client import generate_tpc_agent_speech_openai

        result = build_company_analysis(cui)
        i      = _get_year_dict(result["indicators_by_year"], result["latest_year"])

        text = generate_tpc_agent_speech_openai(
            company_info=result["company_info"],
            years_sorted=result["years_sorted"],
            latest_year=result["latest_year"],
            indicators=i,
            cagr_ca=result["cagr_ca"],
        )
        return jsonify({"success": True, "mode": "speech", "text": text})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
@app.route("/pdf")
def generate_pdf():
    """GET /pdf?cui=...&mode=concluzie|dinamica|speech"""
    cui_param = request.args.get("cui", "")
    mode      = request.args.get("mode", "concluzie")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code

    try:
        from app.analysis_service import build_company_analysis
        from app.pdf_exporter import generate_pdf_report

        result = build_company_analysis(cui)
        _, table_data = _build_table_data(result)
        i = _get_year_dict(result["indicators_by_year"], result["latest_year"])

        if mode == "dinamica":
            from app.openai_dynamic_client import generate_tpc_dynamic_insight_openai
            dynamic = _get_dynamic_inputs(result)
            text = generate_tpc_dynamic_insight_openai(
                company_info=result["company_info"],
                profit_margin_last_3y=dynamic["profit_margin_last_3y"],
                cagr_3y=dynamic["cagr_3y"],
                revenue_growth_last_year=dynamic["revenue_growth_last_year"],
                years_last_3=dynamic["years_last_3"],
            )
        elif mode == "speech":
            from app.openai_speech_client import generate_tpc_agent_speech_openai
            text = generate_tpc_agent_speech_openai(
                company_info=result["company_info"],
                years_sorted=result["years_sorted"],
                latest_year=result["latest_year"],
                indicators=i,
                cagr_ca=result["cagr_ca"],
            )
        else:
            from app.openai_client import generate_tpc_analysis_openai
            text = generate_tpc_analysis_openai(
                company_info=result["company_info"],
                years_sorted=result["years_sorted"],
                latest_year=result["latest_year"],
                indicators=i,
                cagr_ca=result["cagr_ca"],
            )

        pdf_bytes = generate_pdf_report(
            company_info=result["company_info"],
            years_sorted=result["years_sorted"],
            table_data=table_data,
            analysis_text=text,
        )

        safe_name = result["company_info"].get("company_name", str(cui)).replace(" ", "_")
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=TPC_{safe_name}_{mode}.pdf"},
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)