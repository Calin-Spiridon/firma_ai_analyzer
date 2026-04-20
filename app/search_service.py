from app.termene_client import TermeneClient
from app.search_models import SearchCompanyRow


def search_companies_in_termene(
    county: str | None,
    min_turnover: float | None,
    min_employees: int | None,
) -> list[dict]:
    client = TermeneClient()

    # TODO:
    # aici trebuie conectat endpointul real de search/filter din Termene
    raw_results = client.search_companies(
        county=county,
        min_turnover=min_turnover,
        min_employees=min_employees,
    )

    companies = []

    for item in raw_results:
        company = SearchCompanyRow(
            position=0,
            company_name=item.get("company_name") or item.get("denumire") or "-",
            cui=str(item.get("cui") or ""),
            county=item.get("county") or item.get("judet"),
            locality=item.get("locality") or item.get("localitate"),
            caen_code=item.get("caen_code") or item.get("caen"),
            turnover=item.get("turnover") or item.get("cifra_afaceri"),
            employees=item.get("employees") or item.get("numar_angajati"),
        )
        companies.append(company.to_dict())

    companies.sort(key=lambda x: x.get("turnover") or 0, reverse=True)

    for idx, company in enumerate(companies, start=1):
        company["position"] = idx

    return companies