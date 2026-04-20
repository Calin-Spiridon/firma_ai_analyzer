import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_tpc_analysis(
    company_info: dict,
    years_sorted: list,
    latest_year: int,
    indicators: dict,
    cagr_ca: float
) -> str:
    prompt = f"""
Ești consultant senior TPC, specializat în diagnostic de business, structură financiară și eficiență operațională.

Analizează compania de mai jos și scrie în limba română un text clar, convingător și business-oriented.

Structura este OBLIGATORIE și trebuie să conțină EXACT aceste 6 secțiuni, în această ordine:

1. Creștere. Modelul are tracțiune?
2. Profitabilitate. Ce înseamnă pentru companie?
3. Cash Flow. Cum se manifestă în practică?
4. Eficiența activelor. Ce implică pentru eficiență?
5. Capital uman. Care este impactul asupra performanței?
6. Concluzie strategică

Pentru fiecare secțiune:
- scrie titlul exact, pe un rând separat
- apoi 1 sau 2 paragrafe scurte
- fără bullet points
- fără markdown (#, ##, **)
- fără titlu principal înainte de secțiunea 1

Reguli:
- maximum 650 de cuvinte în total
- ton profesionist, clar, business-oriented
- fără jargon inutil
- nu repeta toate cifrele; folosește doar cifrele care susțin insight-ul
- începe analiza cu ce funcționează bine în model
- apoi evidențiază dezechilibrele și tensiunile
- accent puternic pe relația dintre creștere, profit și cash
- identifică mecanismul din spate al modelului economic
- NU oferi soluții
- NU oferi recomandări
- NU spune „ar trebui”
- exprimă implicații, nu acțiuni
- evidențiază unde modelul este stabil și unde devine vulnerabil
- concluzia trebuie să fie clară, memorabilă și bine închisă
- răspunsul este invalid dacă lipsește oricare dintre cele 6 secțiuni

Companie:
- Denumire: {company_info.get('company_name')}
- CUI: {company_info.get('cui')}
- CAEN: {company_info.get('caen_code')} - {company_info.get('caen_label')}

Ani analizați: {years_sorted}
Ultimul an analizat: {latest_year}
CAGR CA: {f"{cagr_ca:.4f}" if cagr_ca is not None else "N/A"}

Indicatori ultim an:
- profit_margin: {indicators['profit_margin']}
- sales_on_assets: {indicators['sales_on_assets']}
- equity_multiplier: {indicators['equity_multiplier']}
- zile_stoc: {indicators['zile_stoc']}
- zile_creante: {indicators['zile_creante']}
- capital_blocat: {indicators['capital_blocat']}
- capital_blocat_ratio: {indicators['capital_blocat_ratio']}
- pondere_fond_salarial: {indicators['pondere_fond_salarial']}
- productivitate: {indicators['productivitate']}
- randament: {indicators['randament']}
- debt_ratio: {indicators['debt_ratio']}
- debt_to_equity: {indicators['debt_to_equity']}
- datorii_ratio_ca: {indicators['datorii_ratio_ca']}
- roe_dupont: {indicators['roe_dupont']}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        temperature=0.2,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.content[0].text