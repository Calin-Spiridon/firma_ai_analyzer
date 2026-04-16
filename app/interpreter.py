def interpret_tpc(indicators: dict, cagr_ca: float):
    """
    Generează interpretare în stil TPC pe baza indicatorilor.
    """

    zile_creante = indicators["zile_creante"]
    capital_blocat_ratio = indicators["capital_blocat_ratio"]
    debt_ratio = indicators["debt_ratio"]
    debt_to_equity = indicators["debt_to_equity"]
    datorii_ratio_ca = indicators["datorii_ratio_ca"]
    profit_margin = indicators["profit_margin"]

    # --- INTERPRETARE ---
    interpretare = []

    interpretare.append("Compania nu are o problemă punctuală, ci una sistemică.")
    interpretare.append("Presiunea nu vine dintr-un singur indicator, ci din modul în care aceștia se leagă între ei.\n")

    # cash flow
    if zile_creante > 180:
        interpretare.append(
            "Observăm o presiune ridicată pe cash flow, determinată în principal de nivelul foarte mare al creanțelor. "
            f"Cu peste {int(zile_creante)} zile de încasare, compania funcționează practic ca un finanțator pentru clienții săi.\n"
        )

    # capital blocat
    if capital_blocat_ratio > 0.8:
        interpretare.append(
            "În paralel, capitalul blocat în stocuri și creanțe ajunge la un nivel echivalent cu întreaga cifră de afaceri anuală. "
            "Asta înseamnă că business-ul generează volum, dar nu reușește să transforme suficient de repede acest volum în lichiditate.\n"
        )

    # datorii
    if debt_ratio > 0.7:
        interpretare.append(
            "Structura de finanțare amplifică această presiune. Gradul ridicat de îndatorare, atât raportat la active, cât și la capitalurile proprii, "
            "indică un model dependent de finanțare externă, vulnerabil în context de blocaj operațional.\n"
        )

    # creștere
    if cagr_ca is not None:
        if cagr_ca < 0.02:
            interpretare.append(
                f"În același timp, creșterea este practic inexistentă. Un CAGR de {round(cagr_ca*100,1)}% în ultimii ani arată că business-ul se află într-o stare de stagnare operațională.\n"
            )
        elif cagr_ca < 0.05:
            interpretare.append(
                f"Creșterea este modestă (CAGR {round(cagr_ca*100,1)}%), insuficientă pentru a susține presiunea operațională.\n"
            )

    # --- CONCLUZIE ---
    concluzie = []
    concluzie.append("Nu discutăm doar despre profitabilitate.\n")
    concluzie.append("Discutăm despre un model de business în care:\n")

    if zile_creante > 180 or capital_blocat_ratio > 0.8:
        concluzie.append("- cash-ul este blocat în operațional")

    if debt_ratio > 0.7:
        concluzie.append("- structura financiară este tensionată")

    if profit_margin < 0.05:
        concluzie.append("- eficiența comercială este scăzută")

    concluzie.append("\nÎn această formă, compania nu are o problemă de rezultat, ci o problemă de mecanică internă a business-ului.")

    return "\n".join(interpretare), "\n".join(concluzie)