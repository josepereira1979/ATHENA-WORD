from __future__ import annotations

from typing import Any, Dict, List


class FamilyCompanyExpansion:
    """Garante a regra estrutural: uma família -> uma empresa real -> uma empresa virtual."""

    ENGINE_NAME = "ATHENA WORLD - FAMILY COMPANY EXPANSION"
    ENGINE_VERSION = "V01"

    def __init__(self, family_engine, company_engine, universe, runtime):
        self.family_engine = family_engine
        self.company_engine = company_engine
        self.universe = universe
        self.runtime = runtime

    def expand(self, world_date: str, limit: int | None = None) -> Dict[str, Any]:
        families = [
            x for x in self.family_engine.get_all_families()
            if x.alive and x.virtual_company_id is None
        ]
        real_companies = [
            x for x in self.universe.get_all_companies()
            if x.active and self.universe.get_primary_listing(x.real_company_id)
        ]
        existing_real = {
            x.real_company_id
            for x in self.company_engine.get_all_companies()
            if getattr(x, "real_company_id", None)
        }
        candidates = [x for x in real_companies if x.real_company_id not in existing_real]
        if limit is not None:
            candidates = candidates[:max(0, int(limit))]

        created: List[Dict[str, Any]] = []
        for family, real_company in zip(families, candidates):
            listing = self.universe.get_primary_listing(real_company.real_company_id)
            virtual = self.company_engine.create_company(
                world_date=world_date,
                company_name=f"{real_company.legal_name} [WORLD]",
                sector=real_company.sector or "GENERAL",
                country=real_company.country or "WORLD",
            )
            result = self.runtime.assign_family_to_real_company(
                family_id=family.family_id,
                virtual_company_id=virtual.company_id,
                real_company_id=real_company.real_company_id,
                listing_id=listing.listing_id,
                world_date=world_date,
            )
            created.append(result)

        return {
            "created_assignments": len(created),
            "families_remaining": len([
                x for x in self.family_engine.get_all_families()
                if x.alive and x.virtual_company_id is None
            ]),
            "real_companies_without_virtual": len([
                x for x in self.universe.get_all_companies()
                if x.active and self.universe.get_primary_listing(x.real_company_id)
                and x.real_company_id not in {
                    c.real_company_id for c in self.company_engine.get_all_companies()
                    if getattr(c, "real_company_id", None)
                }
            ]),
            "assignments": created,
        }
