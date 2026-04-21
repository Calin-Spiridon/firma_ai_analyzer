from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import traceback
import os

app = Flask(__name__)
CORS(app, origins=["https://analiza.tpcconcept.ro", "http://localhost"])


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
    if v is None:
        return "N/A"
    return f"{v * 100:.{d}f}%".replace(".", ",")


def _fmt_num(v, d=2):
    if v is None:
        return "N/A"
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_int(v):
    if v is None:
        return "N/A"
    return f"{int(v):,}".replace(",", ".")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "TPC Analyzer API"})


@app.route("/analyze", methods=["GET"])
def analyze():
    """GET /analyze?cui=27758121"""
    cui_param = request.args.get("cui", "").strip()

    if not cui_param:
        return jsonify({"error": "Lipsește parametrul CUI"}), 400

    cui_clean = "".join(filter(str.isdigit, cui_param))
    if not cui_clean or len(cui_clean) < 2 or len(cui_clean) > 10:
        return jsonify({"error": "CUI invalid — introduceți doar cifre (2-10 caractere)"}), 400

    if not _validate_cui(cui_clean):
        return jsonify({"error": "CUI invalid — cifra de control nu este corectă"}), 400

    cui = int(cui_clean)

    try:
        from app.analysis_service import build_company_analysis
        from app.openai_client import generate_tpc_analysis_openai

        result = build_company_analysis(cui)

        company_info       = result["company_info"]
        years_sorted       = result["years_sorted"]
        latest_year        = result["latest_year"]
        indicators_by_year = result["indicators_by_year"]
        cagr_ca            = result["cagr_ca"]

        i = indicators_by_year.get(str(latest_year), {})

        ai_text = generate_tpc_analysis_openai(
            company_info=company_info,
            years_sorted=years_sorted,
            latest_year=latest_year,
            indicators=i,
            cagr_ca=cagr_ca,
        )

        indicators_table = [
            {"name": "%Profit Net (Profit Net/CA)",                       "value": _fmt_pct(i.get("profit_margin"), 2)},
            {"name": "Sales on asset (CA/Active totale)",                  "value": _fmt_num(i.get("sales_on_assets"))},
            {"name": "Equity multiplier (Active totale/Capital Propriu)",  "value": _fmt_num(i.get("equity_multiplier"))},
            {"name": "Zile stoc (Stoc/CA medie zilnică)",                  "value": _fmt_int(i.get("zile_stoc"))},
            {"name": "Zile creanțe (Creanțe/CA medie zilnică)",            "value": _fmt_int(i.get("zile_creante"))},
            {"name": "Capital Blocat (Creanțe + Stocuri)",                 "value": _fmt_int(i.get("capital_blocat"))},
            {"name": "%Capital Blocat (Capital Blocat / CA)",              "value": _fmt_pct(i.get("capital_blocat_ratio"), 1)},
            {"name": "Salariu brut mediu lunar",                           "value": _fmt_int(i.get("salariu_mediu_lunar")) + " lei"},
            {"name": "Salariu brut anual estimat",                         "value": _fmt_int(i.get("salariu_anual"))},
            {"name": "Fond salarial (Salariu brut anual × Nr. angajați)",  "value": _fmt_int(i.get("fond_salarial"))},
            {"name": "%Fond Salarial (Fond salarial/CA)",                  "value": _fmt_pct(i.get("pondere_fond_salarial"), 1)},
            {"name": "Productivitate (CA/Nr Angajați)",                    "value": _fmt_int(i.get("productivitate"))},
            {"name": "Randament angajat",                                  "value": _fmt_num(i.get("randament"))},
            {"name": "Debt ratio",                                         "value": _fmt_pct(i.get("debt_ratio"), 1)},
            {"name": "Debt to equity",                                     "value": _fmt_num(i.get("debt_to_equity"))},
            {"name": "%Datorii din CA",                                    "value": _fmt_pct(i.get("datorii_ratio_ca"), 1)},
            {"name": "ROE DuPont",                                         "value": _fmt_pct(i.get("roe_dupont"), 1)},
            {"name": f"CAGR Cifră Afaceri ({years_sorted[0]}-{years_sorted[-1]})",
                                                                           "value": _fmt_pct(cagr_ca, 1) if cagr_ca else "N/A"},
        ]

        return jsonify({
            "success":          True,
            "company": {
                "name":      company_info.get("company_name"),
                "cui":       str(cui),
                "caen":      company_info.get("caen_code"),
                "caen_desc": company_info.get("caen_label"),
            },
            "years":              years_sorted,
            "latest_year":        latest_year,
            "indicators_table":   indicators_table,
            "ai_interpretation":  ai_text,
            "cagr_ca":            _fmt_pct(cagr_ca, 1) if cagr_ca else "N/A",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Eroare internă: {str(e)}"}), 500


@app.route("/pdf", methods=["GET"])
def generate_pdf():
    """GET /pdf?cui=27758121"""
    cui_param = request.args.get("cui", "").strip()
    cui_clean = "".join(filter(str.isdigit, cui_param))

    if not cui_clean or len(cui_clean) < 2 or len(cui_clean) > 10:
        return jsonify({"error": "Lipsește sau CUI invalid"}), 400

    if not _validate_cui(cui_clean):
        return jsonify({"error": "CUI invalid — cifra de control nu este corectă"}), 400

    try:
        from app.analysis_service import build_company_analysis
        from app.openai_client import generate_tpc_analysis_openai
        from app.pdf_exporter import generate_pdf_report

        result = build_company_analysis(int(cui_clean))

        company_info       = result["company_info"]
        years_sorted       = result["years_sorted"]
        latest_year        = result["latest_year"]
        indicators_by_year = result["indicators_by_year"]
        cagr_ca            = result["cagr_ca"]

        i = indicators_by_year.get(str(latest_year), {})

        ai_text = generate_tpc_analysis_openai(
            company_info=company_info,
            years_sorted=years_sorted,
            latest_year=latest_year,
            indicators=i,
            cagr_ca=cagr_ca,
        )

        table_data = {
            "Indicator": [
                "%Profit Net", "Sales on assets", "Equity multiplier",
                "Zile stoc", "Zile creanțe", "Capital Blocat", "%Capital Blocat",
                "Salariu mediu lunar", "Salariu anual", "Fond salarial",
                "%Fond salarial", "Productivitate", "Randament",
                "Debt ratio", "Debt to equity", "%Datorii CA", "ROE DuPont",
                "CAGR CA",
            ],
            "Valoare": [
                _fmt_pct(i.get("profit_margin"), 2),
                _fmt_num(i.get("sales_on_assets")),
                _fmt_num(i.get("equity_multiplier")),
                _fmt_int(i.get("zile_stoc")),
                _fmt_int(i.get("zile_creante")),
                _fmt_int(i.get("capital_blocat")),
                _fmt_pct(i.get("capital_blocat_ratio"), 1),
                _fmt_int(i.get("salariu_mediu_lunar")),
                _fmt_int(i.get("salariu_anual")),
                _fmt_int(i.get("fond_salarial")),
                _fmt_pct(i.get("pondere_fond_salarial"), 1),
                _fmt_int(i.get("productivitate")),
                _fmt_num(i.get("randament")),
                _fmt_pct(i.get("debt_ratio"), 1),
                _fmt_num(i.get("debt_to_equity")),
                _fmt_pct(i.get("datorii_ratio_ca"), 1),
                _fmt_pct(i.get("roe_dupont"), 1),
                _fmt_pct(cagr_ca, 1) if cagr_ca else "N/A",
            ],
        }

        pdf_bytes = generate_pdf_report(
            company_info=company_info,
            years_sorted=years_sorted,
            table_data=table_data,
            analysis_text=ai_text,
        )

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=TPC_Analiza_{cui_clean}.pdf"
            },
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
