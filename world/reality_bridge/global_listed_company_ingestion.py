from __future__ import annotations

from typing import Any, Dict, Iterable

from world.reality_bridge.exchange_registry import classify_exchange, market_source, normalize_exchange


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

    @staticmethod
    def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
        exchange = normalize_exchange(str(record.get("exchange", "")))
        profile = classify_exchange(exchange)
        source = market_source(exchange)
        row = dict(record)
        row["exchange"] = exchange
        row["country"] = row.get("country") or profile.country
        row["region"] = row.get("region") or source["region"]
        row["exchange_group"] = row.get("exchange_group") or profile.group
        return row

    def validate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        row = self.normalize_record(record)
        errors = []
        if not row.get("name") and not row.get("legal_name"):
            errors.append("MISSING_LEGAL_NAME")
        if not row.get("ticker"):
            errors.append("MISSING_TICKER")
        if not row.get("exchange"):
            errors.append("MISSING_EXCHANGE")
        if not self._is_operating_company(row):
            errors.append("NON_OPERATING_INSTRUMENT")
        profile = classify_exchange(row["exchange"])
        if profile.region == "OTHER":
            errors.append("UNKNOWN_EXCHANGE")
        return {"valid": not errors, "errors": errors, "record": row}

    def validate_records(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        valid = []
        rejected = []
        for record in records:
            result = self.validate_record(record)
            (valid if result["valid"] else rejected).append(result)
        return {
            "valid_count": len(valid),
            "rejected_count": len(rejected),
            "valid": valid,
            "rejected": rejected,
        }

    def ingest(self, records: Iterable[Dict[str, Any]]) -> Dict[str, int]:
        created_companies = 0
        created_listings = 0
        skipped = 0

        for raw_record in records:
            record = self.normalize_record(raw_record)
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
            source_identity = (
                record.get("source_identity")
                or record.get("issuer_id")
                or record.get("lei")
            )
            company = (
                self.universe.get_company_by_source_identity(str(source_identity))
                if source_identity
                else None
            )
            if company is None:
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
                    source_identity=str(source_identity) if source_identity else None,
                )
                created_companies += 1

            self.universe.add_listing(
                real_company_id=company.real_company_id,
                exchange=exchange,
                ticker=ticker,
                country=country or profile.country,
                share_class=record.get("share_class"),
                currency=record.get("currency"),
                primary=True,
            )
            created_listings += 1


