# api.py — Flask API pentru TPC Analyzer
# Pune acest fișier în ROOT-ul proiectului tău (lângă folderul app/)
# Rulează cu: python api.py (local) sau Railway îl detectează automat

from flask import Flask, jsonify, request
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)  # permite cereri din PHP


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de verificare — Railway îl folosește pentru health checks"""
    return jsonify({"status": "ok", "service": "TPC Analyzer API"})


@app.route("/analyze", methods=["GET"])
def analyze():
    """
    Endpoint principal.
    GET /analyze?cui=27758121
    Returnează JSON cu toate datele companiei + indicatori + interpretare AI
    """
    cui_param = request.args.get("cui", "").strip()

    # --- Validare CUI ---
    if not cui_param:
        return jsonify({"error": "Lipsește parametrul CUI"}), 400

    cui_clean = "".join(filter(str.isdigit, cui_param))
    if not cui_clean or len(cui_clean) < 2 or len(cui_clean) > 10:
        return jsonify({"error": "CUI invalid — introduceți doar cifre (2-10 caractere)"}), 400

    cui = int(cui_clean)

    try:
        # --- Importuri din proiectul tău existent ---
        from app.analysis_service import build_company_analysis
        from app.openai_client import generate_tpc_analysis_openai

        # --- Construiește analiza ---
        result = build_company_analysis(cui)

        company_info    = result["company_info"]
        years_sorted    = result["years_sorted"]
        latest_year     = result["latest_year"]
        indicators_by_year = result["indicators_by_year"]
        cagr_ca         = result["cagr_ca"]

        # Indicatorii pentru ultimul an
        latest_indicators = indicators_by_year.get(str(latest_year), {})

        # --- Generează interpretarea AI ---
        ai_text = generate_tpc_analysis_openai(
            company_info=company_info,
            years_sorted=years_sorted,
            latest_year=latest_year,
            indicators=latest_indicators,
            cagr_ca=cagr_ca,
        )

        # --- Construiește tabelul de indicatori pentru PHP ---
        def fmt_pct(v, d=2):
            if v is None: return "N/A"
            return f"{v * 100:.{d}f}%".replace(".", ",")

        def fmt_num(v, d=2):
            if v is None: return "N/A"
            return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def fmt_int(v):
            if v is None: return "N/A"
            return f"{int(v):,}".replace(",", ".")

        i = latest_indicators
        indicators_table = [
            {"name": "%Profit Net (Profit Net/CA)",                       "value": fmt_pct(i.get("profit_margin"), 2)},
            {"name": "Sales on asset (CA/Active totale)",                  "value": fmt_num(i.get("sales_on_assets"))},
            {"name": "Equity multiplier (Active totale/Capital Propriu)",  "value": fmt_num(i.get("equity_multiplier"))},
            {"name": "Zile stoc (Stoc/CA medie zilnică)",                  "value": fmt_int(i.get("zile_stoc"))},
            {"name": "Zile creanțe (Creanțe/CA medie zilnică)",            "value": fmt_int(i.get("zile_creante"))},
            {"name": "Capital Blocat (Creanțe + Stocuri)",                 "value": fmt_int(i.get("capital_blocat"))},
            {"name": "%Capital Blocat (Capital Blocat / CA)",              "value": fmt_pct(i.get("capital_blocat_ratio"), 1)},
            {"name": "Salariu brut mediu lunar",                           "value": fmt_int(i.get("salariu_mediu_lunar")) + " lei"},
            {"name": "Salariu brut anual estimat",                         "value": fmt_int(i.get("salariu_anual"))},
            {"name": "Fond salarial (Salariu brut anual × Nr. angajați)",  "value": fmt_int(i.get("fond_salarial"))},
            {"name": "%Fond Salarial (Fond salarial/CA)",                  "value": fmt_pct(i.get("pondere_fond_salarial"), 1)},
            {"name": "Productivitate (CA/Nr Angajați)",                    "value": fmt_int(i.get("productivitate"))},
            {"name": "Randament angajat",                                  "value": fmt_num(i.get("randament"))},
            {"name": "Debt ratio",                                         "value": fmt_pct(i.get("debt_ratio"), 1)},
            {"name": "Debt to equity",                                     "value": fmt_num(i.get("debt_to_equity"))},
            {"name": "%Datorii din CA",                                    "value": fmt_pct(i.get("datorii_ratio_ca"), 1)},
            {"name": "ROE DuPont",                                         "value": fmt_pct(i.get("roe_dupont"), 1)},
            {"name": f"CAGR Cifră Afaceri ({years_sorted[0]}-{years_sorted[-1]})",
                                                                           "value": fmt_pct(cagr_ca, 1) if cagr_ca else "N/A"},
        ]

        return jsonify({
            "success": True,
            "company": {
                "name":       company_info.get("company_name"),
                "cui":        str(cui),
                "caen":       company_info.get("caen_code"),
                "caen_desc":  company_info.get("caen_label"),
            },
            "years":              years_sorted,
            "latest_year":        latest_year,
            "indicators_table":   indicators_table,
            "ai_interpretation":  ai_text,
            "cagr_ca":            fmt_pct(cagr_ca, 1) if cagr_ca else "N/A",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Eroare internă: {str(e)}"}), 500


@app.route("/pdf", methods=["GET"])
def generate_pdf():
    """
    GET /pdf?cui=27758121
    Returnează PDF-ul ca fișier descărcabil
    """
    cui_param = request.args.get("cui", "").strip()
    cui_clean = "".join(filter(str.isdigit, cui_param))

    if not cui_clean:
        return jsonify({"error": "Lipsește CUI"}), 400

    try:
        from app.analysis_service import build_company_analysis
        from app.openai_client import generate_tpc_analysis_openai
        from app.pdf_exporter import generate_pdf_report

        result = build_company_analysis(int(cui_clean))

        company_info    = result["company_info"]
        years_sorted    = result["years_sorted"]
        latest_year     = result["latest_year"]
        indicators_by_year = result["indicators_by_year"]
        cagr_ca         = result["cagr_ca"]
        latest_indicators = indicators_by_year.get(str(latest_year), {})

        ai_text = generate_tpc_analysis_openai(
            company_info=company_info,
            years_sorted=years_sorted,
            latest_year=latest_year,
            indicators=latest_indicators,
            cagr_ca=cagr_ca,
        )

        # Construiește table_data în formatul așteptat de pdf_exporter
        def fmt_pct(v, d=2):
            if v is None: return "N/A"
            return f"{v * 100:.{d}f}%".replace(".", ",")
        def fmt_int(v):
            if v is None: return "N/A"
            return f"{int(v):,}".replace(",", ".")
        def fmt_num(v, d=2):
            if v is None: return "N/A"
            return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

        i = latest_indicators
        table_data = {
            "Indicator": [
                "%Profit Net", "Sales on assets", "Equity multiplier",
                "Zile stoc", "Zile creanțe", "Capital Blocat", "%Capital Blocat",
                "Salariu mediu lunar", "Salariu anual", "Fond salarial",
                "%Fond salarial", "Productivitate", "Randament",
                "Debt ratio", "Debt to equity", "%Datorii CA", "ROE DuPont",
                "CAGR CA"
            ],
            "Valoare": [
                fmt_pct(i.get("profit_margin"), 2),
                fmt_num(i.get("sales_on_assets")),
                fmt_num(i.get("equity_multiplier")),
                fmt_int(i.get("zile_stoc")),
                fmt_int(i.get("zile_creante")),
                fmt_int(i.get("capital_blocat")),
                fmt_pct(i.get("capital_blocat_ratio"), 1),
                fmt_int(i.get("salariu_mediu_lunar")),
                fmt_int(i.get("salariu_anual")),
                fmt_int(i.get("fond_salarial")),
                fmt_pct(i.get("pondere_fond_salarial"), 1),
                fmt_int(i.get("productivitate")),
                fmt_num(i.get("randament")),
                fmt_pct(i.get("debt_ratio"), 1),
                fmt_num(i.get("debt_to_equity")),
                fmt_pct(i.get("datorii_ratio_ca"), 1),
                fmt_pct(i.get("roe_dupont"), 1),
                fmt_pct(cagr_ca, 1) if cagr_ca else "N/A",
            ]
        }

        pdf_bytes = generate_pdf_report(
            company_info=company_info,
            years_sorted=years_sorted,
            table_data=table_data,
            analysis_text=ai_text,
        )

        from flask import Response
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=TPC_Analiza_{cui_clean}.pdf"
            }
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
