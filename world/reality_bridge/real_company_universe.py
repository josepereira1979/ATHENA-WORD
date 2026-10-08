from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "real_company_universe_state.json"


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


@dataclass
class Listing:
    listing_id: str
    real_company_id: str
    exchange: str
    ticker: str
    country: Optional[str] = None
    share_class: Optional[str] = None
    currency: Optional[str] = None
    primary: bool = False
    active: bool = True


@dataclass
class RealCompany:
    real_company_id: str
    legal_name: str
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    active: bool = True
    listing_ids: List[str] = field(default_factory=list)
    source_cik: Optional[str] = None


class RealCompanyUniverse:
    """Identidade canónica das empresas reais.

    O ID da empresa é estável e independente de ticker, bolsa ou classe.
    Tickers/listagens podem mudar sem quebrar as ligações da ATHENA WORLD.
    """

    ENGINE_NAME = "ATHENA WORLD - REAL COMPANY UNIVERSE"
    ENGINE_VERSION = "V01"

    def __init__(self, state_file: Path = STATE_FILE, auto_load: bool = True):
        self.state_file = Path(state_file)
        self.companies: Dict[str, RealCompany] = {}
        self.listings: Dict[str, Listing] = {}
        if auto_load:
            self.load()

    @staticmethod
    def _new_id() -> str:
        return new_id("REAL")

    def create_company(
        self,
        legal_name: str,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        real_company_id: Optional[str] = None,
        source_cik: Optional[str] = None,
    ) -> RealCompany:
        if not legal_name:
            raise ValueError("legal_name não pode estar vazio.")

        if real_company_id and real_company_id in self.companies:
            raise ValueError("real_company_id já existe.")

        company = RealCompany(
            real_company_id=real_company_id or self._new_id(),
            legal_name=legal_name,
            country=country,
            sector=sector,
            industry=industry,
        )
        self.companies[company.real_company_id] = company
        self.save()
        return company

    def add_listing(
        self,
        real_company_id: str,
        exchange: str,
        ticker: str,
        country: Optional[str] = None,
        share_class: Optional[str] = None,
        currency: Optional[str] = None,
        primary: bool = False,
    ) -> Listing:
        company = self.get_company(real_company_id)
        if company is None:
            raise ValueError("Empresa real inexistente.")
        if not exchange or not ticker:
            raise ValueError("exchange e ticker são obrigatórios.")

        ticker_norm = ticker.upper().strip()
        exchange_norm = exchange.upper().strip()

        for listing in self.listings.values():
            if (
                listing.active
                and listing.exchange.upper() == exchange_norm
                and listing.ticker.upper() == ticker_norm
            ):
                raise ValueError("Ticker/listagem activa já existe.")

        if primary:
            for listing_id in company.listing_ids:
                old = self.listings.get(listing_id)
                if old is not None:
                    old.primary = False

        listing = Listing(
            listing_id=new_id("LIST"),
            real_company_id=real_company_id,
            exchange=exchange_norm,
            ticker=ticker_norm,
            country=country,
            share_class=share_class,
            currency=currency,
            primary=primary,
        )
        self.listings[listing.listing_id] = listing
        company.listing_ids.append(listing.listing_id)
        self.save()
        return listing

    def get_company(self, real_company_id: str) -> Optional[RealCompany]:
        return self.companies.get(real_company_id)

    def get_listing(self, listing_id: str) -> Optional[Listing]:
        return self.listings.get(listing_id)

    def get_company_by_ticker(
        self,
        ticker: str,
        exchange: Optional[str] = None,
    ) -> Optional[RealCompany]:
        ticker_norm = ticker.upper().strip()
        exchange_norm = exchange.upper().strip() if exchange else None
        for listing in self.listings.values():
            if not listing.active or listing.ticker.upper() != ticker_norm:
                continue
            if exchange_norm and listing.exchange.upper() != exchange_norm:
                continue
            return self.get_company(listing.real_company_id)
        return None

    def get_primary_listing(self, real_company_id: str) -> Optional[Listing]:
        company = self.get_company(real_company_id)
        if company is None:
            return None
        for listing_id in company.listing_ids:
            listing = self.listings.get(listing_id)
            if listing and listing.active and listing.primary:
                return listing
        for listing_id in company.listing_ids:
            listing = self.listings.get(listing_id)
            if listing and listing.active:
                return listing
        return None

    def get_all_companies(self) -> List[RealCompany]:
        return list(self.companies.values())

    def get_all_listings(self) -> List[Listing]:
        return list(self.listings.values())

    def count(self) -> int:
        return len(self.companies)

    def active_count(self) -> int:
        return sum(1 for company in self.companies.values() if company.active)

    def save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "engine_name": self.ENGINE_NAME,
            "engine_version": self.ENGINE_VERSION,
            "companies": [asdict(x) for x in self.companies.values()],
            "listings": [asdict(x) for x in self.listings.values()],
        }
        with self.state_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=4)

    def load(self) -> None:
        if not self.state_file.exists():
            return
        with self.state_file.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        self.companies = {
            item["real_company_id"]: RealCompany(**item)
            for item in payload.get("companies", [])
        }
        self.listings = {
            item["listing_id"]: Listing(**item)
            for item in payload.get("listings", [])
        }

    def reset(self) -> None:
        self.companies = {}
        self.listings = {}
        if self.state_file.exists():
            self.state_file.unlink()
