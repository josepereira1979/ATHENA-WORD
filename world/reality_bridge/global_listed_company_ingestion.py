from __future__ import annotations

from typing import Any, Dict, Iterable

from world.reality_bridge.exchange_registry import classify_exchange


class GlobalListedCompanyIngestion:
    """Camada de ingestão preparada para fontes oficiais por mercado.

    A ingestão separa identidade da empresa da sua listagem.
    Nunca transforma um ticker numa nova empresa quando já existe uma
    identidade canónica.
    """

    ENGINE_NAME = "ATHENA WORLD - GLOBAL LISTED COMPANY INGESTION"
    ENGINE_VERSION = "V01"

    def __init__(self, universe):
        self.universe = universe

    @staticmethod
    def _is_operating_company(record: Dict[str, Any]) -> bool:
        text = " ".join(
            str(record.get(k, "")).upper()
            for k in ("name", "legal_name", "security_type", "asset_type", "industry")
        )
        blocked = ("ETF", "ETN", "FUND", "TRUST", "MUTUAL", "INDEX FUND", "SPAC")
        return not any(token in text for token in blocked)

    def ingest(self, records: Iterable[Dict[str, Any]]) -> Dict[str, int]:
        created_companies = 0
        created_listings = 0
        skipped = 0

        for record in records:
            if not self._is_operating_company(record):
                skipped += 1
                continue

            name = (record.get("legal_name") or record.get("name") or "").strip()
            ticker = (record.get("ticker") or "").strip()
            exchange = (record.get("exchange") or "").strip()
            country = record.get("country")
            if not name or not ticker or not exchange:
                skipped += 1
                continue

            existing = self.universe.get_company_by_ticker(ticker, exchange)
            if existing is not None:
                skipped += 1
                continue

            profile = classify_exchange(exchange)
            company_id = record.get("real_company_id")
            company = self.universe.create_company(
                legal_name=name,
                country=country or profile.country,
                sector=record.get("sector"),
                industry=record.get("industry"),
                real_company_id=company_id,
                source_cik=record.get("source_cik"),
                region=profile.region,
                exchange_group=profile.group,
            )
            self.universe.add_listing(
                real_company_id=company.real_company_id,
                exchange=exchange,
                ticker=ticker,
                country=country or profile.country,
                share_class=record.get("share_class"),
                currency=record.get("currency"),
                primary=True,
            )
            created_companies += 1
            created_listings += 1

        return {
            "created_companies": created_companies,
            "created_listings": created_listings,
            "skipped": skipped,
        }
