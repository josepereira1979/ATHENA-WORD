from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from world.intelligence.global_market_census import GlobalMarketCensus
from world.intelligence.global_family_market_allocator import GlobalFamilyMarketAllocator
from world.reality_bridge.global_listed_company_ingestion import GlobalListedCompanyIngestion
from world.reality_bridge.listed_company_sync import ListedCompanySync


class GlobalWorldPopulationEngine:
    """Orquestra ingestão, censo e povoamento 1:1 sem inventar identidades."""

    ENGINE_NAME = "ATHENA WORLD - GLOBAL WORLD POPULATION ENGINE"
    ENGINE_VERSION = "V01"

    def __init__(self, runtime):
        self.runtime = runtime
        universe = runtime.engines["REALITY_BRIDGE"].universe
        self.ingestion = GlobalListedCompanyIngestion(universe)
        self.sec_sync = ListedCompanySync()
        self.census = GlobalMarketCensus(runtime)
        self.allocator = GlobalFamilyMarketAllocator(runtime)

    def ingest_records(self, records: Iterable[Dict[str, Any]], allocate: bool = False) -> Dict[str, Any]:
        validation = self.ingestion.validate_records(records)
        valid_records = [item["record"] for item in validation["valid"]]
        ingested = self.ingestion.ingest(valid_records)
        allocation = None
        if allocate:
            allocation = self.allocator.allocate()
        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "validation": {
                "valid": validation["valid_count"],
                "rejected": validation["rejected_count"],
            },
            "ingestion": ingested,
            "allocation": allocation,
            "census": self.census.build(),
            "readiness": self.census.readiness(),
        }

    def ingest_sec(self, user_agent: str, max_new: Optional[int] = None, allocate: bool = False) -> Dict[str, Any]:
        records = self.sec_sync.fetch_sec(user_agent)
        rows = [
            {
                "real_company_id": f"REAL-SEC-{record.cik}",
                "source_cik": record.cik,
                "source_identity": f"SEC:{record.cik}",
                "legal_name": record.legal_name,
                "ticker": record.ticker,
                "exchange": record.exchange,
                "country": record.country,
            }
            for record in records
        ]
        if max_new is not None:
            rows = rows[:max(0, int(max_new))]
        return self.ingest_records(rows, allocate=allocate)

    def preview(self, limit: Optional[int] = None) -> Dict[str, Any]:
        census = self.census.build()
        allocation = self.allocator.preview(limit=limit)
        return {
            "census": census,
            "readiness": self.census.readiness(),
            "allocation_preview": allocation,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "census": self.census.build(),
            "readiness": self.census.readiness(),
        }
