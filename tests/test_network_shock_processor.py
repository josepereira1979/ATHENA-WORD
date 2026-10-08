from world.intelligence.network_propagation_engine import NetworkPropagationEngine
from world.intelligence.network_shock_processor import NetworkShockProcessor


class FakeCompany:
    def __init__(self, company_id):
        self.real_company_id = company_id
        self.active = True


class FakeUniverse:
    def get_company(self, company_id):
        return FakeCompany(company_id) if company_id in {"A", "B"} else None


class FakeFamily:
    def __init__(self):
        self.family_id = "F-1"
        self.real_company_id = "B"
        self.alive = True


class FakeFamilyEngine:
    def __init__(self):
        self.families = {"F-1": FakeFamily()}


class FakeLearning:
    def __init__(self):
        self.rows = []

    def record_experience(self, **kwargs):
        self.rows.append(kwargs)

    def save(self):
        pass


def test_network_shock_reaches_family(tmp_path):
    network = __import__(
        "world.intelligence.corporate_network_engine",
        fromlist=["CorporateNetworkEngine"],
    ).CorporateNetworkEngine(
        state_file=tmp_path / "network.json",
        universe=FakeUniverse(),
    )
    network.add_relationship("A", "B", "SUPPLIES", confidence=0.95, evidence="documented")
    propagation = NetworkPropagationEngine(network, state_file=tmp_path / "propagation.json")
    learning = FakeLearning()
    processor = NetworkShockProcessor(propagation, FakeFamilyEngine(), learning)

    result = processor.process_shock("A", "RISK", world_date="2027-02-04")

    assert result["signals"] == 1
    assert result["family_signals"] == 1
    assert learning.rows[0]["knowledge_domain"] == "NETWORK_RISK"
