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

Analizează compania de mai jos folosind o logică pe 5 dimensiuni fundamentale:
1. Creștere (cifra de afaceri & CAGR)
2. Profitabilitate (% profit net)
3. Cash Flow (capital blocat, ciclul de numerar, datorii)
4. Eficiența activelor (sales on assets)
5. Capital uman (productivitate, fond salarial, randament)

Scrie în limba română un text, clar și convingător, format din 6 secțiuni:

1. Creștere. modelul are tracțiune?
(text)

2. Profitabilitate. Ce înseamnă pentru companie?
(text)

3. Cash Flow. Cum se manifestă în practică?
(text)

4. Eficiența activelor. Ce implică pentru eficiență?
(text)

5. Capital uman. Care este impactul asupra performanței?
(text)

6. Concluzie strategica:
(text)

Reguli:
- maximum 700 de cuvinte în total
- ton profesionist, clar, business-oriented
- fără bullet points
- fără jargon inutil
- nu enumera explicit cele 5 axe (integrează-le natural în text)
- nu repeta toate cifrele; folosește doar ce susține insight-ul
- începe cu 2 idei despre ce funcționează bine (creștere, eficiență, productivitate etc.)
- apoi evidențiază dezechilibrele și tensiunile din model
- accent puternic pe relația: creștere, profit si cash
- identifică mecanismul din spate (de ex: creștere finanțată prin capital blocat sau datorii)
- NU oferi soluții sau recomandări
- NU spune „ar trebui”
- exprimă implicații, nu acțiuni
- evidențiază unde modelul este stabil și unde devine vulnerabil
- concluzia trebuie să fie structurata, clară și memorabilă
- evită formulări generale sau banale
- scrie ca un consultant care înțelege modelul economic, nu doar cifrele
- nu scrie titlu principal
- nu folosi markdown (#, ##)
- folosește exact aceste etichete:

Interpretare:
Concluzie:

Companie:
- Denumire: {company_info.get('company_name')}
- CUI: {company_info.get('cui')}
- CAEN: {company_info.get('caen_code')} - {company_info.get('caen_label')}

Ani analizați: {years_sorted}
Ultimul an: {latest_year}
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
- datorii_vs_cash_block: {indicators['datorii_vs_cash_block']}
- datorii_ratio_ca: {indicators['datorii_ratio_ca']}
- roe_dupont: {indicators['roe_dupont']}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.content[0].text