import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "export_targetare_ro.xlsx"

_df_cache = None


def _load_db() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        _df_cache = pd.read_excel(DB_PATH, dtype={
            "CUI": str,
            "Cod CAEN": str,
        })
    return _df_cache


def search_local_db(
    min_turnover: float = None,
    max_turnover: float = None,
    min_employees: int = None,
    county: str = None,
    max_results: int = 200,
) -> list[dict]:

    df = _load_db().copy()

    if county:
        county_norm = county.strip().upper()
        df = df[df["Judet"].str.upper().str.contains(county_norm, na=False)]

    if min_turnover and min_turnover > 0:
        df = df[pd.to_numeric(df["Cifra de Afaceri"], errors="coerce") >= min_turnover]

    if max_turnover and max_turnover > 0:
        df = df[pd.to_numeric(df["Cifra de Afaceri"], errors="coerce") <= max_turnover]

    if min_employees and min_employees > 0:
        df = df[pd.to_numeric(df["Angajati"], errors="coerce") >= min_employees]

    df = df.sort_values("Cifra de Afaceri", ascending=False)
    df = df.head(max_results)

    results = []
    for _, row in df.iterrows():
        cui_raw = str(row.get("CUI", "") or "").strip()
        cui_digits = "".join(filter(str.isdigit, cui_raw))
        if not cui_digits:
            continue
        results.append({
            "cui": int(cui_digits),
            "denumire": str(row.get("Numele Companiei", "") or "").strip(),
            "judet": str(row.get("Judet", "") or "").strip(),
            "localitate": str(row.get("Localitate", "") or "").strip(),
            "caen": str(row.get("Cod CAEN", "") or "").strip(),
            "cifra_afaceri": row.get("Cifra de Afaceri"),
            "angajati": row.get("Angajati"),
            "profit_net": row.get("Profit Net"),
        })

    return results
