from world.intelligence.corporate_network_engine import CorporateNetworkEngine

class FakeCompany:
    def __init__(self, company_id):
        self.real_company_id = company_id
        self.active = True

class FakeUniverse:
    def get_company(self, company_id):
        return FakeCompany(company_id) if company_id in {"REAL-1", "REAL-2", "REAL-3"} else None

def test_network_add_dedupe_and_reload(tmp_path):
    path = tmp_path / "network.json"
    engine = CorporateNetworkEngine(state_file=path, universe=FakeUniverse())
    first = engine.add_relationship("REAL-1", "REAL-2", "SUPPLIES", confidence=0.95, evidence="documented")
    second = engine.add_relationship("REAL-1", "REAL-2", "SUPPLIES", confidence=0.98, evidence="updated")
    assert first.relationship_id == second.relationship_id
    assert engine.counts()["relationships"] == 1
    assert engine.get_neighbors("REAL-1") == ["REAL-2"]
    reloaded = CorporateNetworkEngine(state_file=path, universe=FakeUniverse())
    assert reloaded.get_relationships("REAL-2")[0].evidence == "updated"

def test_network_rejects_unknown_company(tmp_path):
    engine = CorporateNetworkEngine(state_file=tmp_path / "network.json", universe=FakeUniverse())
    try:
        engine.add_relationship("REAL-1", "REAL-X", "SUPPLIES")
        assert False
    except ValueError:
        assert True
