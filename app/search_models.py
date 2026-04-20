from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class CompanySearchFilters:
    county: Optional[str] = None
    min_turnover: Optional[float] = None
    min_employees: Optional[int] = None


@dataclass
class SearchCompanyRow:
    position: int
    company_name: str
    cui: str
    county: Optional[str] = None
    locality: Optional[str] = None
    caen_code: Optional[str] = None
    turnover: Optional[float] = None
    employees: Optional[int] = None

    is_enriched: bool = False
    enrichment_status: str = "pending"   # pending / success / error
    enriched_at: Optional[str] = None

    profit_margin: Optional[float] = None
    cagr_ca: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    shareholders: Optional[str] = None

    def to_dict(self):
        return asdict(self)