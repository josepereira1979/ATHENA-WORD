from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


class GlobalFamilyMarketAllocator:
    """Distribui famílias por empresas cotadas reais, 1:1, agrupadas por mercado."""

    ENGINE_NAME = "ATHENA WORLD - GLOBAL FAMILY MARKET ALLOCATOR"
    ENGINE_VERSION = "V01"

    def __init__(self, runtime):
        self.runtime = runtime

    def _candidates(self):
        universe = self.runtime.engines["REALITY_BRIDGE"].universe
        company_engine = self.runtime.engines["COMPANY"]

        used = {
            c.real_company_id
            for c in company_engine.get_all_companies()
            if getattr(c, "real_company_id", None)
        }

        rows = []
        for company in universe.get_all_companies():
            if not company.active or company.real_company_id in used:
                continue
            listing = universe.get_primary_listing(company.real_company_id)
            if listing is None or not listing.active:
                continue
            rows.append((company, listing))

        return sorted(
            rows,
            key=lambda x: (
                x[1].country or "",
                x[1].exchange or "",
                x[1].ticker or "",
                x[0].real_company_id,
            ),
        )

    def preview(self, limit: int | None = None) -> Dict[str, Any]:
        families = [
            f for f in self.runtime.engines["FAMILY"].get_all_families()
            if f.alive and f.virtual_company_id is None
        ]
        candidates = self._candidates()
        if limit is not None:
            candidates = candidates[:max(0, int(limit))]

        universe = self.runtime.engines["REALITY_BRIDGE"].universe
        groups = defaultdict(int)
        rows = []

        for company, listing in candidates[:len(families)]:
            key = f"{listing.country or 'UNKNOWN'}/{listing.exchange or 'UNKNOWN'}"
            groups[key] += 1
            rows.append({
                "real_company_id": company.real_company_id,
                "legal_name": company.legal_name,
                "country": listing.country or company.country,
                "exchange": listing.exchange,
                "ticker": listing.ticker,
            })

        return {
            "families_available": len(families),
            "companies_available": len(candidates),
            "assignable": min(len(families), len(candidates)),
            "market_groups": dict(sorted(groups.items())),
            "preview": rows,
        }

    def allocate(self, limit: int | None = None) -> Dict[str, Any]:
        """Atribui na mesma ordem determinística usada no agrupamento mundial."""
        family_engine = self.runtime.engines["FAMILY"]
        company_engine = self.runtime.engines["COMPANY"]

        families = [
            f for f in family_engine.get_all_families()
            if f.alive and f.virtual_company_id is None
        ]
        candidates = self._candidates()
        if limit is not None:
            candidates = candidates[:max(0, int(limit))]

        created = []
        world_date = self.runtime.world_core.state["world_date"]

        for family, (real_company, listing) in zip(families, candidates):
            virtual = company_engine.create_company(
                world_date=world_date,
                company_name=f"{real_company.legal_name} [WORLD]",
                sector=real_company.sector or "GENERAL",
                country=real_company.country or listing.country or "WORLD",
            )
            created.append(
                self.runtime.assign_family_to_real_company(
                    family_id=family.family_id,
                    virtual_company_id=virtual.company_id,
                    real_company_id=real_company.real_company_id,
                    listing_id=listing.listing_id,
                    world_date=world_date,
                )
            )

        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "created_assignments": len(created),
            "assignments": created,
            "families_remaining": len([
                f for f in family_engine.get_all_families()
                if f.alive and f.virtual_company_id is None
            ]),
            "companies_available_after": len(self._candidates()),
            "market_report": self.report(),
        }

    def report(self) -> Dict[str, Any]:
        family_engine = self.runtime.engines["FAMILY"]
        universe = self.runtime.engines["REALITY_BRIDGE"].universe

        groups = defaultdict(lambda: {
            "families": 0,
            "companies": [],
        })

        for family in family_engine.get_all_families():
            if not family.alive or not family.real_company_id:
                continue
            company = universe.get_company(family.real_company_id)
            listing = universe.get_primary_listing(family.real_company_id)
            if company is None or listing is None:
                continue

            key = f"{listing.country or company.country or 'UNKNOWN'}/{listing.exchange}"
            groups[key]["families"] += 1
            groups[key]["companies"].append({
                "family_id": family.family_id,
                "family_name": family.family_name,
                "real_company_id": company.real_company_id,
                "company": company.legal_name,
                "ticker": listing.ticker,
            })

        return {
            "total_assigned_families": sum(x["families"] for x in groups.values()),
            "groups": dict(sorted(groups.items())),
        }
