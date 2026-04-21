import os
import pandas as pd
from datetime import datetime

EXCEL_PATH = "data/companies_log.xlsx"

def append_company_log(company_info: dict, latest_year: int, indicators: dict, cagr_ca: float):
    row = {
        "timestamp": datetime.now().isoformat(),
        "company_name": company_info.get("company_name"),
        "cui": company_info.get("cui"),
        "caen_code": company_info.get("caen_code"),
        "caen_label": company_info.get("caen_label"),
        "latest_year": latest_year,
        "profit_margin": indicators.get("profit_margin"),
        "sales_on_assets": indicators.get("sales_on_assets"),
        "equity_multiplier": indicators.get("equity_multiplier"),
        "zile_stoc": indicators.get("zile_stoc"),
        "zile_creante": indicators.get("zile_creante"),
        "capital_blocat": indicators.get("capital_blocat"),
        "capital_blocat_ratio": indicators.get("capital_blocat_ratio"),
        "pondere_fond_salarial": indicators.get("pondere_fond_salarial"),
        "productivitate": indicators.get("productivitate"),
        "randament": indicators.get("randament"),
        "debt_ratio": indicators.get("debt_ratio"),
        "debt_to_equity": indicators.get("debt_to_equity"),
        "datorii_vs_cash_block": indicators.get("datorii_vs_cash_block"),
        "datorii_ratio_ca": indicators.get("datorii_ratio_ca"),
        "roe_dupont": indicators.get("roe_dupont"),
        "cagr_ca": cagr_ca,
    }

    os.makedirs("data", exist_ok=True)

    try:
        if os.path.exists(EXCEL_PATH):
            df = pd.read_excel(EXCEL_PATH)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_excel(EXCEL_PATH, index=False)
    except Exception as e:
        print(f"[excel_log] Eroare la scrierea log-ului: {e}")
