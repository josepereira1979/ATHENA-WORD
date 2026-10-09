from types import SimpleNamespace

from world.intelligence.global_world_finalizer import GlobalWorldFinalizer


class FakeUniverse:
    def __init__(self, count):
        self.companies = [
            SimpleNamespace(
                real_company_id=f"REAL-{i:04d}",
                legal_name=f"Issuer {i:04d}",
                country="TEST",
                sector="TECH",
                active=True,
            )
            for i in range(count)
        ]
        self.listings = {
            c.real_company_id: SimpleNamespace(
                listing_id=f"LIST-{i:04d}",
                real_company_id=c.real_company_id,
                active=True,
            )
            for i, c in enumerate(self.companies, 1)
        }

    def get_all_companies(self):
        return self.companies

    def get_primary_listing(self, real_company_id):
        return self.listings.get(real_company_id)

    def get_company(self, real_company_id):
        return next((c for c in self.companies if c.real_company_id == real_company_id), None)


class FakeFamilyEngine:
    def __init__(self, count, agent_ids):
        self.families = {
            f"FAMILY-{i:04d}": SimpleNamespace(
                family_id=f"FAMILY-{i:04d}",
                family_name=f"Family {i:04d}",
                generation=1,
                alive=True,
                member_ids=agent_ids[(i - 1) * 2:i * 2],
                virtual_company_id=None,
                real_company_id=None,
                market_exchange=None,
                market_listing_id=None,
            )
            for i in range(1, count + 1)
        }

    def get_all_families(self):
        return list(self.families.values())

    def save(self):
        pass


class FakeAgentEngine:
    def __init__(self, agent_ids):
        self.agents = {
            agent_id: SimpleNamespace(agent_id=agent_id, primary_company_id=None)
            for agent_id in agent_ids
        }

    def create_agent(self, world_date, profession, family_id, generation):
        agent_id = f"AGENT-NEW-{len(self.agents) + 1}"
        self.agents[agent_id] = SimpleNamespace(agent_id=agent_id, primary_company_id=None)
        return self.agents[agent_id]

    def save(self):
        pass


class FakeCompanyEngine:
    def __init__(self):
        self.companies = {}

    def create_company(self, world_date, company_name, sector, country):
        company_id = f"VIRTUAL-{len(self.companies) + 1:04d}"
        company = SimpleNamespace(
            company_id=company_id,
            company_name=company_name,
            sector=sector,
            country=country,
            status="ACTIVE",
            real_company_id=None,
        )
        self.companies[company_id] = company
        return company

    def get_all_companies(self):
        return list(self.companies.values())

    def save(self):
        pass


class FakeRuntime:
    def __init__(self, count):
        agent_ids = [f"AGENT-{i:04d}" for i in range(1, count * 2 + 1)]
        self.engines = {
            "REALITY_BRIDGE": SimpleNamespace(universe=FakeUniverse(count)),
            "FAMILY": FakeFamilyEngine(count, agent_ids),
            "AGENT": FakeAgentEngine(agent_ids),
            "COMPANY": FakeCompanyEngine(),
        }

    def assign_family_to_real_company(
        self, family_id, virtual_company_id, real_company_id, listing_id, world_date
    ):
        family = self.engines["FAMILY"].families[family_id]
        company = self.engines["COMPANY"].companies[virtual_company_id]
        family.virtual_company_id = virtual_company_id
        family.real_company_id = real_company_id
        family.market_listing_id = listing_id
        company.real_company_id = real_company_id
        return {
            "family_id": family_id,
            "virtual_company_id": virtual_company_id,
            "real_company_id": real_company_id,
            "listing_id": listing_id,
        }


def test_finalizer_populates_1001_companies_families_virtual_companies_and_agents():
    runtime = FakeRuntime(1001)
    result = GlobalWorldFinalizer(runtime).finalize("2026-10-01")

    assert result["eligible_real_companies"] == 1001
    assert result["assigned_real_companies"] == 1001
    assert result["families_total"] == 1001
    assert result["virtual_companies_total"] == 1001
    assert result["agents_total"] == 2002
    assert result["new_assignments"] == 1001
    assert result["unassigned_real_companies"] == []
    assert result["duplicate_real_company_assignments"] == 0
    assert result["closed"] is True

    families = runtime.engines["FAMILY"].get_all_families()
    assert all(len(f.member_ids) >= 2 for f in families)
    assert all(
        member_id in runtime.engines["AGENT"].agents
        for family in families for member_id in family.member_ids
    )
    assert len({family.real_company_id for family in families}) == 1001
    assert len({family.virtual_company_id for family in families}) == 1001


def test_finalizer_is_idempotent_for_already_assigned_companies():
    runtime = FakeRuntime(3)
    finalizer = GlobalWorldFinalizer(runtime)
    first = finalizer.finalize("2026-10-01")
    second = finalizer.finalize("2026-10-02")

    assert first["new_assignments"] == 3
    assert second["new_assignments"] == 0
    assert second["assigned_real_companies"] == 3
    assert second["closed"] is True
