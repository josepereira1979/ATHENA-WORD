from world.intelligence.global_world_population import GlobalWorldPopulationEngine


def test_population_engine_ingests_and_reports(tmp_path):
    class Core:
        state = {"world_date": "2027-01-01", "tick": 0}

    from world.reality_bridge.real_company_universe import RealCompanyUniverse
    from world.families.family_engine import FamilyEngine
    from world.companies.company_engine import CompanyEngine

    class Bridge:
        pass

    class Runtime:
        world_core = Core()
        engines = {
            "REALITY_BRIDGE": Bridge(),
            "FAMILY": FamilyEngine(state_file=tmp_path / "f.json", auto_load=False),
            "COMPANY": CompanyEngine(state_file=tmp_path / "c.json", auto_load=False),
        }

    runtime = Runtime()
    runtime.engines["REALITY_BRIDGE"].universe = RealCompanyUniverse(tmp_path / "u.json", auto_load=False)
    engine = GlobalWorldPopulationEngine(runtime)
    result = engine.ingest_records([
        {"name": "World Tech", "ticker": "WTECH", "exchange": "NASDAQ", "country": "US", "sector": "TECHNOLOGY"},
        {"name": "World ETF", "ticker": "WETF", "exchange": "NASDAQ", "country": "US", "asset_type": "ETF"},
    ])
    assert result["ingestion"]["created_companies"] == 1
    assert result["validation"]["rejected"] == 1
    assert result["census"]["companies_with_primary_listing"] == 1
