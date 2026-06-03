from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100 if -1 <= value <= 1 else value


def _trend_pp(current: float | None, base: float | None, threshold_pp: float = 1.0) -> str:
    current = _pct(current)
    base = _pct(base)
    if current is None or base is None:
        return "necunoscut"
    diff = current - base
    if diff > threshold_pp:
        return "crestere"
    if diff < -threshold_pp:
        return "scadere"
    return "stabil"


def _trend_ratio(current: float | None, base: float | None, threshold_ratio: float = 0.10) -> str:
    current = _safe_float(current)
    base = _safe_float(base)
    if current is None or base is None or base == 0:
        return "necunoscut"
    change = (current - base) / abs(base)
    if change > threshold_ratio:
        return "crestere"
    if change < -threshold_ratio:
        return "scadere"
    return "stabil"


def classify_growth(cagr_ca: float | None) -> dict:
    cagr = _pct(_safe_float(cagr_ca))
    if cagr is None:
        return {"score": "⚪", "label": "Necunoscut", "profile": "Date insuficiente", "message": "Nu există suficiente date pentru evaluarea creșterii."}
    if cagr > 12:
        return {"score": "🔵", "label": "Excepțional", "profile": "Creștere puternică", "message": "Compania crește într-un ritm foarte bun. Nivelul actual poate indica o capacitate ridicată de dezvoltare și câștig de teren în piață."}
    if cagr >= 7:
        return {"score": "🟢", "label": "Bun", "profile": "Creștere sănătoasă", "message": "Compania crește într-un ritm sănătos, care poate susține dezvoltarea fără semne evidente de stagnare."}
    if cagr >= 3:
        return {"score": "🟡", "label": "Acceptabil", "profile": "Creștere modestă", "message": "Compania crește, însă ritmul este modest. Pentru o firmă care urmărește dezvoltarea accelerată, acest nivel poate fi sub așteptări."}
    if cagr >= 0:
        return {"score": "🟠", "label": "Atenție", "profile": "Stagnare", "message": "Compania are o creștere foarte redusă. Datele indică mai degrabă menținerea poziției actuale decât dezvoltare reală."}
    return {"score": "🔴", "label": "Risc", "profile": "Contracție", "message": "Cifra de afaceri este în scădere. Situația poate indica pierdere de volum, presiune concurențială sau probleme ale modelului comercial."}


def classify_profitability(current_profit_margin: float | None, profit_margin_base: float | None = None, current_equity: float | None = None, base_equity: float | None = None) -> dict:
    margin = _pct(_safe_float(current_profit_margin))
    margin_trend = _trend_pp(current_profit_margin, profit_margin_base, threshold_pp=1.0)
    equity_trend = _trend_ratio(current_equity, base_equity, threshold_ratio=0.10)
    if margin is None:
        return {"score": "⚪", "label": "Necunoscut", "profile": "Date insuficiente", "margin_trend": margin_trend, "equity_trend": equity_trend, "message": "Nu există suficiente date pentru evaluarea profitabilității."}
    if margin > 12:
        score, label, profile, message = "🔵", "Excepțional", "Profitabilitate foarte ridicată", "Compania transformă o parte importantă din vânzări în profit. Acest nivel sugerează o poziționare favorabilă sau o eficiență operațională peste medie."
    elif margin >= 7:
        score, label, profile, message = "🟢", "Bun", "Profitabilitate sănătoasă", "Compania generează profit la un nivel sănătos și dispune de o marjă care poate absorbi fluctuații normale ale costurilor și ale pieței."
    elif margin >= 4:
        score, label, profile, message = "🟡", "Acceptabil", "Profitabilitate acceptabilă", "Business-ul generează profit și creează valoare, însă există încă spațiu semnificativ de îmbunătățire a profitabilității."
    elif margin > 0:
        score, label, profile, message = "🟠", "Atenție", "Profitabilitate redusă", "Compania operează cu o marjă redusă. Profitul există, însă capacitatea de a absorbi șocuri economice, comerciale sau operaționale este limitată."
    else:
        score, label, profile, message = "🔴", "Risc", "Pierdere sau profit nul", "Activitatea nu generează profit sau generează pierderi. Prioritatea principală devine restabilirea capacității companiei de a crea valoare."
    if margin_trend == "scadere":
        message += " Tendința descendentă a marjei trebuie analizată, deoarece poate indica erodarea capacității de a transforma vânzările în profit."
    elif margin_trend == "crestere":
        message += " Tendința pozitivă a marjei arată o îmbunătățire a capacității companiei de a transforma vânzările în profit."
    if equity_trend == "crestere":
        value_creation = "Capitalul propriu este în creștere, ceea ce indică faptul că o parte din valoarea creată rămâne în companie."
    elif equity_trend == "scadere":
        value_creation = "Capitalul propriu este în scădere, ceea ce ridică întrebări privind acumularea valorii în companie."
    elif equity_trend == "stabil":
        value_creation = "Capitalul propriu este relativ stabil, ceea ce indică o acumulare limitată de valoare în companie."
    else:
        value_creation = "Evoluția capitalului propriu nu poate fi evaluată pe baza datelor disponibile."
    return {"score": score, "label": label, "profile": profile, "margin_trend": margin_trend, "equity_trend": equity_trend, "message": message, "value_creation_message": value_creation}


def classify_cashflow(capital_blocat_ratio: float | None) -> dict:
    ratio = _pct(_safe_float(capital_blocat_ratio))
    if ratio is None:
        return {"score": "⚪", "label": "Necunoscut", "profile": "Date insuficiente", "message": "Nu există suficiente date pentru evaluarea cash-flow-ului operațional."}
    if ratio < 10:
        return {"score": "🔵", "label": "Excepțional", "profile": "Cash Generator", "message": "Modelul necesită foarte puțin capital pentru a funcționa și transformă rapid activitatea în numerar."}
    if ratio < 20:
        return {"score": "🟢", "label": "Bun", "profile": "Cash Discipline", "message": "Nivelul capitalului blocat este sănătos. Activitatea poate susține creșterea fără presiuni majore asupra lichidității."}
    if ratio < 30:
        return {"score": "🟡", "label": "Acceptabil", "profile": "Cash Expansion", "message": "Modelul începe să consume cantități semnificative de numerar pentru susținerea activității. Situația trebuie monitorizată."}
    if ratio < 40:
        return {"score": "🟠", "label": "Atenție", "profile": "Cash Pressure", "message": "O parte importantă din resursele companiei rămâne blocată în stocuri și creanțe. Creșterea poate necesita finanțare suplimentară."}
    return {"score": "🔴", "label": "Risc", "profile": "Cash Trap", "message": "Activitatea consumă volume mari de numerar și poate deveni dependentă de finanțare externă pentru susținerea operațiunilor curente."}


def classify_assets(sales_on_assets: float | None) -> dict:
    soa = _safe_float(sales_on_assets)
    if soa is None:
        return {"score": "⚪", "label": "Necunoscut", "profile": "Date insuficiente", "message": "Nu există suficiente date pentru evaluarea utilizării capitalului."}
    if soa > 3:
        return {"score": "🔵", "label": "Excepțional", "profile": "Randament excepțional al activelor", "message": "Modelul utilizează excepțional capitalul investit. Randamentul activelor permite companiei să accelereze creșterea fără investiții semnificative suplimentare."}
    if soa >= 2:
        return {"score": "🟢", "label": "Bun", "profile": "Randament bun al activelor", "message": "Activele sunt utilizate eficient și susțin bine dezvoltarea companiei. Randamentul activelor permite accelerarea creșterii fără presiuni majore asupra investițiilor."}
    if soa >= 1.2:
        return {"score": "🟡", "label": "Acceptabil", "profile": "Randament acceptabil al activelor", "message": "Compania utilizează capitalul într-un mod rezonabil, însă dacă își propune o creștere accelerată, ar trebui să ia în calcul și îmbunătățirea randamentului activelor."}
    if soa >= 0.8:
        return {"score": "🟠", "label": "Atenție", "profile": "Randament redus al activelor", "message": "Înainte de a accelera creșterea, compania ar trebui să își îmbunătățească randamentul activelor. În forma actuală, dezvoltarea poate necesita investiții semnificative."}
    return {"score": "🔴", "label": "Risc", "profile": "Model intensiv în capital", "message": "Randamentul activelor sugerează un model intensiv în capital. Înainte de a urmări creșterea, prioritatea ar trebui să fie optimizarea utilizării activelor existente."}


def classify_human_capital(productivity: float | None, employee_yield: float | None = None, payroll_ratio: float | None = None) -> dict:
    prod = _safe_float(productivity)
    randament = _safe_float(employee_yield)
    payroll = _pct(_safe_float(payroll_ratio))
    if prod is None:
        return {"score": "⚪", "label": "Necunoscut", "profile": "Date insuficiente", "message": "Nu există suficiente date pentru evaluarea productivității."}
    if prod > 2_000_000:
        score, label, profile, message = "🔵", "Excepțional", "Knowledge-intensive / High leverage", "Modelul generează un volum foarte mare de venituri raportat la numărul de angajați. Compania poate scala activitatea fără creșterea proporțională a echipei."
    elif prod >= 1_000_000:
        score, label, profile, message = "🔵", "Excepțional", "Productivitate foarte bună", "Compania generează un nivel ridicat de venituri raportat la numărul de angajați. Productivitatea oferă o bază foarte bună pentru creștere."
    elif prod >= 750_000:
        score, label, profile, message = "🟢", "Bun", "Productivitate bună", "Organizația utilizează eficient resursa umană și dispune de o bază sănătoasă pentru dezvoltare."
    elif prod >= 500_000:
        score, label, profile, message = "🟡", "Acceptabil", "Productivitate medie", "Compania se află într-o zonă medie de productivitate. Există oportunități de creștere prin optimizarea proceselor și utilizarea mai eficientă a resurselor existente."
    else:
        score, label, profile, message = "🟠", "Atenție", "Labor-intensive", "Compania este puternic dependentă de resursa umană. Fidelizarea angajaților și creșterea productivității trebuie să fie preocupări importante ale managementului."
    randament_message = None
    if randament is not None:
        if randament > 10:
            randament_message = "Randamentul ridicat al angajaților sugerează un raport foarte bun între valoarea creată și costurile salariale. Compania poate susține creșterea fără presiuni majore de salarizare."
        elif randament < 2:
            randament_message = "Productivitatea redusă și randamentul scăzut al angajaților indică o posibilă presiune a salariilor asupra costurilor. Cu alte cuvinte, compania poate ajunge să plătească prea mult în raport cu veniturile generate per angajat, ceea ce limitează profitabilitatea."
        elif randament < 3:
            randament_message = "Randamentul redus al angajaților sugerează că productivitatea devine un factor critic pentru profitabilitatea viitoare. Creșterea eficienței poate avea un impact mai mare decât extinderea echipei."
    return {"score": score, "label": label, "profile": profile, "message": message, "randament": randament, "randament_message": randament_message, "payroll_ratio": payroll}


def build_tpc_scoring_profile(indicators: dict, cagr_ca: float | None, profit_margin_base: float | None = None, equity_base: float | None = None) -> dict:
    growth = classify_growth(cagr_ca)
    profitability = classify_profitability(
        current_profit_margin=indicators.get("profit_margin"),
        profit_margin_base=profit_margin_base,
        current_equity=indicators.get("capital_propriu"),
        base_equity=equity_base,
    )
    cashflow = classify_cashflow(indicators.get("capital_blocat_ratio"))
    assets = classify_assets(indicators.get("sales_on_assets"))
    human_capital = classify_human_capital(
        productivity=indicators.get("productivitate"),
        employee_yield=indicators.get("randament"),
        payroll_ratio=indicators.get("pondere_fond_salarial"),
    )
    return {"growth": growth, "profitability": profitability, "cashflow": cashflow, "assets": assets, "human_capital": human_capital}
