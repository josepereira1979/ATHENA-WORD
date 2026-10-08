from __future__ import annotations

from typing import Any, Dict, List


class GlobalWorldFinalizer:
    """Fecha o povoamento estrutural: uma família por empresa operacional cotada.

    A quantidade de famílias deixa de ser fixa. O universo real determina
    quantas famílias existem. Para cada empresa activa com uma listing activa,
    garante-se exactamente uma família, uma empresa virtual e, para famílias
    novas, dois agentes iniciais.
    """

    ENGINE_NAME = "ATHENA WORLD - GLOBAL WORLD FINALIZER"
    ENGINE_VERSION = "V01"

    def __init__(self, runtime):
        self.runtime = runtime

    def _eligible_companies(self):
        universe = self.runtime.engines["REALITY_BRIDGE"].universe
        return sorted(
            [
                company
                for company in universe.get_all_companies()
                if company.active
                and universe.get_primary_listing(company.real_company_id) is not None
            ],
            key=lambda x: (x.country or "", x.legal_name.upper(), x.real_company_id),
        )

    def _assigned_real_ids(self) -> set[str]:
        family_engine = self.runtime.engines["FAMILY"]
        return {
            family.real_company_id
            for family in family_engine.get_all_families()
            if family.alive and family.real_company_id
        }

    def finalize(self, world_date: str) -> Dict[str, Any]:
        family_engine = self.runtime.engines["FAMILY"]
        agent_engine = self.runtime.engines["AGENT"]
        company_engine = self.runtime.engines["COMPANY"]

        companies = self._eligible_companies()
        assigned = self._assigned_real_ids()

        unassigned_families = [
            family
            for family in family_engine.get_all_families()
            if family.alive and family.virtual_company_id is None
        ]

        created_families: List[str] = []
        created_agents: List[str] = []
        assignments: List[Dict[str, Any]] = []

        for company in companies:
            if company.real_company_id in assigned:
                continue

            if unassigned_families:
                family = unassigned_families.pop(0)
            else:
                family = family_engine.create_family(
                    world_date=world_date,
                    family_name=f"House {company.legal_name}",
                    generation=1,
                )
                created_families.append(family.family_id)

                for _ in range(2):
                    agent = agent_engine.create_agent(
                        world_date=world_date,
                        profession=f"Investigador de {company.sector or 'mercado'}",
                        family_id=family.family_id,
                        generation=1,
                    )
                    family_engine.add_member(
                        family.family_id,
                        agent.agent_id,
                        world_date,
                    )
                    created_agents.append(agent.agent_id)

            listing = self.runtime.engines["REALITY_BRIDGE"].universe.get_primary_listing(
                company.real_company_id
            )
            virtual = company_engine.create_company(
                world_date=world_date,
                company_name=f"{company.legal_name} [WORLD]",
                sector=company.sector or "GENERAL",
                country=company.country or "WORLD",
            )

            result = self.runtime.assign_family_to_real_company(
                family_id=family.family_id,
                virtual_company_id=virtual.company_id,
                real_company_id=company.real_company_id,
                listing_id=listing.listing_id,
                world_date=world_date,
            )

            if not family.member_ids:
                for _ in range(2):
                    agent = agent_engine.create_agent(
                        world_date=world_date,
                        profession=f"Investigador de {company.sector or 'mercado'}",
                        family_id=family.family_id,
                        generation=family.generation,
                    )
                    family_engine.add_member(family.family_id, agent.agent_id, world_date)
                    created_agents.append(agent.agent_id)

            for agent_id in family.member_ids:
                agent = agent_engine.agents.get(agent_id)
                if agent is not None and agent.primary_company_id is None:
                    agent.primary_company_id = virtual.company_id
                    agent.last_update_world_date = world_date
            agent_engine.save()

            assigned.add(company.real_company_id)
            assignments.append(result)

        family_engine.save()
        company_engine.save()

        eligible_ids = {company.real_company_id for company in companies}
        assigned_ids = [
            family.real_company_id
            for family in family_engine.get_all_families()
            if family.alive and family.real_company_id
        ]
        final_assigned = set(assigned_ids)
        orphaned = sorted(eligible_ids - final_assigned)
        duplicate_count = len(assigned_ids) - len(final_assigned)

        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "eligible_real_companies": len(companies),
            "families_total": len(family_engine.get_all_families()),
            "agents_total": len(agent_engine.agents),
            "virtual_companies_total": len(company_engine.get_all_companies()),
            "new_families": len(created_families),
            "new_agents": len(created_agents),
            "new_assignments": len(assignments),
            "assigned_real_companies": len(final_assigned & eligible_ids),
            "unassigned_real_companies": orphaned,
            "duplicate_real_company_assignments": duplicate_count,
            "closed": not orphaned and duplicate_count == 0 and len(final_assigned & eligible_ids) == len(eligible_ids),
        }
