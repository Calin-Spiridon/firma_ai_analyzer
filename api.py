from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from cachetools import TTLCache
from threading import Lock
import traceback
import os

app = Flask(__name__)
CORS(app)

_analysis_cache: TTLCache = TTLCache(maxsize=128, ttl=1800)
_cache_lock = Lock()


def _cached_build_analysis(cui: int, force: bool = False) -> dict:
    if not force:
        with _cache_lock:
            if cui in _analysis_cache:
                return _analysis_cache[cui]
    from app.analysis_service import build_company_analysis
    result = build_company_analysis(cui)
    with _cache_lock:
        _analysis_cache[cui] = result
    return result


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

def _fmt_abs(v):
    if v is None: return "-"
    try:
        return f"{int(round(v)):,}".replace(",", ".")
    except Exception:
        return "-"

def _get_year_dict(data, year):
    return data.get(str(year), data.get(year, {}))

def _calculate_yoy_change(current, previous):
    if current is None or previous in (None, 0): return None
    return (current - previous) / previous

def _parse_cui(cui_param):
    cui_clean = "".join(filter(str.isdigit, cui_param.strip()))
    if not cui_clean or len(cui_clean) < 2 or len(cui_clean) > 10:
        return None, jsonify({"error": "CUI invalid"}), 400
    if not _validate_cui(cui_clean):
        return None, jsonify({"error": "CUI invalid — cifra de control nu este corecta"}), 400
    return int(cui_clean), None, None


def _get_cagr_3y(result):
    from app.utils import calculate_cagr
    yrs = result["years_sorted"]
    nby = result["normalized_by_year"]
    if len(yrs) < 3:
        return None, None, None
    y3s, y3e = yrs[-3], yrs[-1]
    ca_s = _get_year_dict(nby, y3s).get("cifra_afaceri")
    ca_e = _get_year_dict(nby, y3e).get("cifra_afaceri")
    if ca_s not in (None, 0) and ca_e not in (None, 0) and y3e > y3s:
        return calculate_cagr(ca_s, ca_e, y3e - y3s), y3s, y3e
    return None, y3s, y3e


def _build_table_data(result):
    iby  = result["indicators_by_year"]
    nby  = result["normalized_by_year"]
    yrs  = result["years_sorted"]
    last = result["latest_year"]
    cagr = result["cagr_ca"]

    i_cur = _get_year_dict(iby, last)
    prev1 = yrs[-2] if len(yrs) >= 2 else None
    prev2 = yrs[-3] if len(yrs) >= 3 else None
    i_p1  = _get_year_dict(iby, prev1) if prev1 else {}
    i_p2  = _get_year_dict(iby, prev2) if prev2 else {}

    sy = yrs[0]; ey = yrs[-1]

    years_last_3_desc = list(reversed(yrs[-3:] if len(yrs) >= 3 else yrs))

    cagr_3y, c3s, c3e = _get_cagr_3y(result)
    cagr_3y_label = (
        f"%CAGR ({c3s} - {c3e}) - crestere medie anuala"
        if c3s else "%CAGR ultimii 3 ani"
    )

    yoy = None
    yoy_label = "%Dinamica CA vs anul anterior"
    if prev1:
        yoy_label = f"%Dinamica CA {last} vs {prev1}"
        yoy = _calculate_yoy_change(
            _get_year_dict(nby, last).get("cifra_afaceri"),
            _get_year_dict(nby, prev1).get("cifra_afaceri"),
        )

    abs_rows = []
    for year in years_last_3_desc:
        yd = _get_year_dict(nby, year)
        abs_rows.append({"name": f"Cifra Afaceri - {year}", "value": _fmt_abs(yd.get("cifra_afaceri"))})
    for year in years_last_3_desc:
        yd = _get_year_dict(nby, year)
        abs_rows.append({"name": f"Profit Net - {year}", "value": _fmt_abs(yd.get("profit_net"))})
    for year in years_last_3_desc:
        yd = _get_year_dict(nby, year)
        emp = yd.get("numar_angajati") if yd.get("numar_angajati") is not None else yd.get("numar_mediu_angajati")
        abs_rows.append({"name": f"Numar Salariati - {year}", "value": _fmt_abs(emp)})

    calc_rows = [
        {"name": f"%Profit Net {last} (Profit Net/CA)",                              "value": _fmt_pct(i_cur.get("profit_margin"), 2)},
        {"name": f"%Profit Net {prev1} (Profit Net/CA)" if prev1 else "%Profit Net an anterior", "value": _fmt_pct(i_p1.get("profit_margin"), 2) if prev1 else "N/A"},
        {"name": f"%Profit Net {prev2} (Profit Net/CA)" if prev2 else "%Profit Net cu 2 ani in urma", "value": _fmt_pct(i_p2.get("profit_margin"), 2) if prev2 else "N/A"},
        {"name": "Sales on asset (CA/Active totale)",                                "value": _fmt_num(i_cur.get("sales_on_assets"))},
        {"name": "Equity multiplier (Active totale/Capital Propriu)",                "value": _fmt_num(i_cur.get("equity_multiplier"))},
        {"name": "Zile stoc (Stoc/CA medie zilnica)",                                "value": _fmt_int(i_cur.get("zile_stoc"))},
        {"name": "Zile creante (Creante/CA medie zilnica)",                          "value": _fmt_int(i_cur.get("zile_creante"))},
        {"name": "Capital Blocat (Creante + Stocuri)",                               "value": _fmt_int(i_cur.get("capital_blocat"))},
        {"name": "%Capital Blocat (Capital Blocat / CA)",                            "value": _fmt_pct(i_cur.get("capital_blocat_ratio"), 1)},
        {"name": "Salariu brut mediu lunar (salariu brut mediu pe economie)",        "value": _fmt_int(i_cur.get("salariu_mediu_lunar")) + " lei"},
        {"name": "Salariu brut anual (Salariu mediu brut lunar*12)",                 "value": _fmt_int(i_cur.get("salariu_anual"))},
        {"name": "Fond salarial (Salariu brut anual*numar angajati)",                "value": _fmt_int(i_cur.get("fond_salarial"))},
        {"name": "%Fond Salarial (Fond salarial/CA)",                                "value": _fmt_pct(i_cur.get("pondere_fond_salarial"), 1)},
        {"name": "Productivitate (CA/Nr Angajati)",                                  "value": _fmt_int(i_cur.get("productivitate"))},
        {"name": "Randament angajat (Productivitate/Salariu brut anual per angajat)","value": _fmt_num(i_cur.get("randament"))},
        {"name": "Debt Ratio (Datorii totale/Active totale)",                        "value": _fmt_pct(i_cur.get("debt_ratio"), 1)},
        {"name": "Debt to equity (Datorii totale/Capital Propriu)",                  "value": _fmt_num(i_cur.get("debt_to_equity"))},
        {"name": "%Datorii (Datorii totale/CA)",                                     "value": _fmt_pct(i_cur.get("datorii_ratio_ca"), 1)},
        {"name": "ROE DuPont (%Profit Net*Sales on asset*equity multiplier)",        "value": _fmt_pct(i_cur.get("roe_dupont"), 1)},
        {"name": f"%CAGR ({sy} - {ey}) - crestere medie anuala",                    "value": _fmt_pct(cagr, 1) if cagr else "N/A"},
        {"name": cagr_3y_label,                                                      "value": _fmt_pct(cagr_3y, 1) if cagr_3y is not None else "N/A"},
        {"name": yoy_label,                                                          "value": _fmt_pct(yoy, 1) if yoy is not None else "N/A"},
    ]

    all_rows = abs_rows + calc_rows
    table_data = {
        "Indicator": [r["name"] for r in all_rows],
        "Valoare":   [r["value"] for r in all_rows],
    }
    return all_rows, table_data


def _get_dynamic_inputs(result):
    yrs  = result["years_sorted"]
    last = result["latest_year"]
    iby  = result["indicators_by_year"]
    nby  = result["normalized_by_year"]

    years_last_3 = yrs[-3:] if len(yrs) >= 3 else yrs
    profit_margin_last_3y = [
        _get_year_dict(iby, y).get("profit_margin") for y in years_last_3
    ]
    cagr_3y, _, _ = _get_cagr_3y(result)
    revenue_growth = None
    if len(yrs) >= 2:
        revenue_growth = _calculate_yoy_change(
            _get_year_dict(nby, last).get("cifra_afaceri"),
            _get_year_dict(nby, yrs[-2]).get("cifra_afaceri"),
        )
    return {
        "profit_margin_last_3y":    profit_margin_last_3y,
        "cagr_3y":                  cagr_3y,
        "revenue_growth_last_year": revenue_growth,
        "years_last_3":             years_last_3,
    }


def _generate_ai_text(result, mode):
    i = _get_year_dict(result["indicators_by_year"], result["latest_year"])
    if mode == "dinamica":
        from app.openai_dynamic_client import generate_tpc_dynamic_insight_openai
        dynamic = _get_dynamic_inputs(result)
        return generate_tpc_dynamic_insight_openai(
            company_info=result["company_info"],
            profit_margin_last_3y=dynamic["profit_margin_last_3y"],
            cagr_3y=dynamic["cagr_3y"],
            revenue_growth_last_year=dynamic["revenue_growth_last_year"],
            years_last_3=dynamic["years_last_3"],
        )
    elif mode == "speech":
        from app.openai_speech_client import generate_tpc_agent_speech_openai
        return generate_tpc_agent_speech_openai(
            company_info=result["company_info"],
            years_sorted=result["years_sorted"],
            latest_year=result["latest_year"],
            indicators=i,
            cagr_ca=result["cagr_ca"],
        )
    else:
        from app.openai_client import generate_tpc_analysis_openai
        return generate_tpc_analysis_openai(
            company_info=result["company_info"],
            years_sorted=result["years_sorted"],
            latest_year=result["latest_year"],
            indicators=i,
            cagr_ca=result["cagr_ca"],
        )


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    with _cache_lock:
        sz = len(_analysis_cache)
    return jsonify({"status": "ok", "service": "TPC Analyzer API", "cache_size": sz})


@app.route("/analyze")
def analyze():
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code
    force = request.args.get("refresh", "0") == "1"
    try:
        result = _cached_build_analysis(cui, force=force)
        rows, _ = _build_table_data(result)
        return jsonify({
            "success":          True,
            "company": {
                "name":      result["company_info"].get("company_name"),
                "cui":       str(cui),
                "caen":      result["company_info"].get("caen_code"),
                "caen_desc": result["company_info"].get("caen_label"),
            },
            "years":            result["years_sorted"],
            "latest_year":      result["latest_year"],
            "indicators_table": rows,
            "cagr_ca":          _fmt_pct(result["cagr_ca"], 1) if result["cagr_ca"] is not None else "N/A",
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/ai/concluzie")
def ai_concluzie():
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code
    try:
        result = _cached_build_analysis(cui)
        text   = _generate_ai_text(result, "concluzie")
        return jsonify({"success": True, "mode": "concluzie", "text": text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/ai/dinamica")
def ai_dinamica():
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code
    try:
        result = _cached_build_analysis(cui)
        text   = _generate_ai_text(result, "dinamica")
        return jsonify({"success": True, "mode": "dinamica", "text": text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/ai/speech")
def ai_speech():
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code
    try:
        result = _cached_build_analysis(cui)
        text   = _generate_ai_text(result, "speech")
        return jsonify({"success": True, "mode": "speech", "text": text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── NOU: Limita de Credit Comercial ─────────────────────────
@app.route("/credit")
def credit_limit():
    """GET /credit?cui=... — Calculeaza limita de credit comercial TPC"""
    cui_param = request.args.get("cui", "")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code
    try:
        from app.credit_limit import calculate_credit_limit

        result      = _cached_build_analysis(cui)
        latest_year = result["latest_year"]
        indicators  = _get_year_dict(result["indicators_by_year"], latest_year)
        normalized  = _get_year_dict(result["normalized_by_year"], latest_year)

        # Adaugam cagr_ca in indicators
        indicators_with_cagr = dict(indicators)
        indicators_with_cagr["cagr_ca"] = result.get("cagr_ca")

        credit = calculate_credit_limit(indicators_with_cagr, normalized)

        if "error" in credit:
            return jsonify({"error": credit["error"]}), 422

        return jsonify({
            "success":     True,
            "company": {
                "name": result["company_info"].get("company_name"),
                "cui":  str(cui),
            },
            "latest_year": latest_year,
            "credit":      credit,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/pdf")
def pdf_data():
    """Returneaza JSON pentru pdf.php — fara WeasyPrint."""
    cui_param = request.args.get("cui", "")
    mode      = request.args.get("mode", "concluzie")
    cui, err, code = _parse_cui(cui_param)
    if err: return err, code
    try:
        result = _cached_build_analysis(cui)
        _, td  = _build_table_data(result)
        text   = _generate_ai_text(result, mode)
        return jsonify({
            "success":     True,
            "mode":        mode,
            "company":     result["company_info"],
            "years":       result["years_sorted"],
            "latest_year": result["latest_year"],
            "table_data":  td,
            "ai_text":     text,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)