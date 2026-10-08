from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict

from world.reality_bridge.exchange_registry import classify_exchange


class GlobalMarketCensus:
    """Censo estrutural do universo empresarial da ATHENA WORLD."""

    ENGINE_NAME = "ATHENA WORLD - GLOBAL MARKET CENSUS"
    ENGINE_VERSION = "V01"

    def __init__(self, runtime):
        self.runtime = runtime

    def build(self) -> Dict[str, Any]:
        universe = self.runtime.engines["REALITY_BRIDGE"].universe
        family_engine = self.runtime.engines["FAMILY"]
        company_engine = self.runtime.engines["COMPANY"]

        regions = defaultdict(int)
        countries = defaultdict(int)
        exchanges = defaultdict(int)
        sectors = defaultdict(int)
        assigned_by_region = defaultdict(int)
        assigned_by_country = defaultdict(int)

        represented = {
            c.real_company_id
            for c in company_engine.get_all_companies()
            if getattr(c, "real_company_id", None)
        }

        active_companies = 0
        companies_with_primary_listing = 0

        for company in universe.get_all_companies():
            if not company.active:
                continue
            active_companies += 1
            listing = universe.get_primary_listing(company.real_company_id)
            if listing is None or not listing.active:
                continue

            companies_with_primary_listing += 1
            profile = classify_exchange(listing.exchange)
            region = company.region or profile.region
            country = listing.country or company.country or profile.country
            exchange = profile.code
            sector = company.sector or "UNKNOWN"

            regions[region] += 1
            countries[country] += 1
            exchanges[exchange] += 1
            sectors[sector] += 1

            if company.real_company_id in represented:
                assigned_by_region[region] += 1
                assigned_by_country[country] += 1

        alive_families = [
            f for f in family_engine.get_all_families()
            if f.alive
        ]
        assigned_families = [
            f for f in alive_families
            if f.real_company_id and f.virtual_company_id
        ]

        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "active_real_companies": active_companies,
            "companies_with_primary_listing": companies_with_primary_listing,
            "alive_families": len(alive_families),
            "assigned_families": len(assigned_families),
            "unassigned_families": len(alive_families) - len(assigned_families),
            "unassigned_company_capacity": max(
                0,
                companies_with_primary_listing - len(represented),
            ),
            "regions": dict(sorted(regions.items())),
            "countries": dict(sorted(countries.items())),
            "exchanges": dict(sorted(exchanges.items())),
            "sectors": dict(sorted(sectors.items())),
            "assigned_by_region": dict(sorted(assigned_by_region.items())),
            "assigned_by_country": dict(sorted(assigned_by_country.items())),
        }

    def readiness(self) -> Dict[str, Any]:
        census = self.build()
        families = census["unassigned_families"]
        capacity = census["unassigned_company_capacity"]
        if families == 0:
            status = "COMPLETE"
        elif capacity >= families:
            status = "READY_FOR_FULL_ASSIGNMENT"
        elif capacity > 0:
            status = "PARTIAL_CAPACITY"
        else:
            status = "WAITING_FOR_COMPANIES"

        return {
            "status": status,
            "families_to_assign": families,
            "company_capacity": capacity,
            "coverage_ratio": (
                round(capacity / families, 6) if families else 1.0
            ),
        }
