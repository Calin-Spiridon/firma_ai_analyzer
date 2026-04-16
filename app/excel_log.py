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
        "profit_margin": indicators["profit_margin"],
        "sales_on_assets": indicators["sales_on_assets"],
        "equity_multiplier": indicators["equity_multiplier"],
        "zile_stoc": indicators["zile_stoc"],
        "zile_creante": indicators["zile_creante"],
        "capital_blocat": indicators["capital_blocat"],
        "capital_blocat_ratio": indicators["capital_blocat_ratio"],
        "pondere_fond_salarial": indicators["pondere_fond_salarial"],
        "productivitate": indicators["productivitate"],
        "randament": indicators["randament"],
        "debt_ratio": indicators["debt_ratio"],
        "debt_to_equity": indicators["debt_to_equity"],
        "datorii_vs_cash_block": indicators["datorii_vs_cash_block"],
        "datorii_ratio_ca": indicators["datorii_ratio_ca"],
        "roe_dupont": indicators["roe_dupont"],
        "cagr_ca": cagr_ca,
    }

    os.makedirs("data", exist_ok=True)

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_excel(EXCEL_PATH, index=False)