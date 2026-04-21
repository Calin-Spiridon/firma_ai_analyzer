import requests
import pandas as pd
import unicodedata
from io import StringIO


ONRC_CSV_URL = (
    "https://data.gov.ro/dataset/f7374920-a656-4e34-85dd-a61c6e6e5603"
    "/resource/488a8d00-90df-4f37-b5f4-6c9111e6f1e7/download/od_firme.csv"
)


def _normalize(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s.upper())
    return "".join(c for c in s if not unicodedata.combining(c))


def search_companies_local_full(
    county: str = None,
    localitate: str = None,
    max_results: int = 500,
) -> list[dict]:

    try:
        response = requests.get(ONRC_CSV_URL, timeout=120)
        response.raise_for_status()

        response.encoding = "utf-8"
        text = response.text

        df = pd.read_csv(
            StringIO(text),
            sep="^",
            dtype=str,
            low_memory=False,
            encoding_errors="replace",
            on_bad_lines="skip",
            quoting=3,
        )
    except Exception as e:
        raise Exception(f"Nu am putut descărca lista de firme: {str(e)}")

    df.columns = [c.strip().upper().replace("﻿", "") for c in df.columns]

    if county:
        county_ascii = _normalize(county.strip())

        if "ADR_JUDET" in df.columns:
            df = df[df["ADR_JUDET"].apply(lambda x: county_ascii in _normalize(x))]

    df = df.head(max_results)

    results = []
    for _, row in df.iterrows():
        cui_raw = str(row.get("CUI", "") or "").strip()
        cui_digits = "".join(filter(str.isdigit, cui_raw))
        if not cui_digits or cui_digits == "0":
            continue
        results.append({
            "cui": int(cui_digits),
            "denumire": str(row.get("DENUMIRE", "") or "").strip(),
            "judet": str(row.get("ADR_JUDET", "") or "").strip(),
            "localitate": str(row.get("ADR_LOCALITATE", "") or "").strip(),
            "forma_juridica": str(row.get("FORMA_JURIDICA", "") or "").strip(),
        })

    return results
