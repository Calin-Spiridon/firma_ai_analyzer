# firma_ai_analyzer

A Python tool for analyzing company financial data and assessing risk levels.

## Overview

Analyzes key financial ratios (receivables, inventory, profit margin) to produce a risk score and flag potential issues for each company.

## Project Structure

- `main.py` — core analysis logic and sample data
- `requirements.txt` — Python dependencies
- `.venv/` — virtual environment (not committed)

## Key Logic

- `analyze_company(company_data)` — computes ratios and returns a risk assessment dict
- `print_company_analysis(result)` — formats and prints the result to stdout
- Risk levels: **Scazut** (low), **Mediu** (medium), **Ridicat** (high)

## Risk Scoring

| Metric | Threshold | Points |
|---|---|---|
| Receivables / Turnover | > 25% | +30 |
| Receivables / Turnover | > 15% | +15 |
| Inventory / Turnover | > 20% | +30 |
| Inventory / Turnover | > 12% | +15 |
| Profit Margin | < 3% | +40 |
| Profit Margin | < 6% | +20 |

Score >= 70 → Ridicat, >= 35 → Mediu, < 35 → Scazut

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Notes

- Output is in Romanian
- No external API calls currently; `requests` and `python-dotenv` are available for future integrations
