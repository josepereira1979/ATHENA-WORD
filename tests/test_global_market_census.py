from world.intelligence.global_market_census import GlobalMarketCensus


def test_census_counts_capacity(tmp_path):
    from world.reality_bridge.real_company_universe import RealCompanyUniverse
    from world.families.family_engine import FamilyEngine
    from world.companies.company_engine import CompanyEngine

    class Core:
        state = {"world_date": "2027-01-01", "tick": 0}

    class Runtime:
        world_core = Core()
        engines = {
            "REALITY_BRIDGE": type("Bridge", (), {"universe": RealCompanyUniverse(tmp_path / "u.json", auto_load=False)})(),
            "FAMILY": FamilyEngine(state_file=tmp_path / "f.json", auto_load=False),
            "COMPANY": CompanyEngine(state_file=tmp_path / "c.json", auto_load=False),
        }

    runtime = Runtime()
    universe = runtime.engines["REALITY_BRIDGE"].universe
    company = universe.create_company("Census Corp", country="US", sector="TECH")
    universe.add_listing(company.real_company_id, "NASDAQ", "CNS", country="US", primary=True)

    runtime.engines["FAMILY"].create_family("Family A", "2027-01-01", ["A1", "A2"])
    runtime.engines["FAMILY"].create_family("Family B", "2027-01-01", ["B1", "B2"])

    census = GlobalMarketCensus(runtime)
    result = census.build()
    assert result["active_real_companies"] == 1
    assert result["companies_with_primary_listing"] == 1
    assert result["alive_families"] == 2
    assert result["unassigned_families"] == 2
    assert result["unassigned_company_capacity"] == 1
    assert census.readiness()["status"] == "PARTIAL_CAPACITY"
