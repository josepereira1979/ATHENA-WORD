from world.intelligence.corporate_network_engine import CorporateNetworkEngine
from world.intelligence.network_propagation_engine import NetworkPropagationEngine


class FakeCompany:
    def __init__(self, company_id):
        self.real_company_id = company_id
        self.active = True


class FakeUniverse:
    def get_company(self, company_id):
        return FakeCompany(company_id) if company_id in {"A", "B", "C", "D"} else None


def build_network(tmp_path):
    network = CorporateNetworkEngine(state_file=tmp_path / "network.json", universe=FakeUniverse())
    network.add_relationship("A", "B", "SUPPLIES", confidence=1.0, evidence="A supplies B")
    network.add_relationship("B", "C", "SUPPLIES", confidence=0.9, evidence="B supplies C")
    network.add_relationship("B", "D", "COMPETES_WITH", confidence=0.8, evidence="B competes with D")
    return network


def test_risk_propagates_and_attenuates(tmp_path):
    engine = NetworkPropagationEngine(build_network(tmp_path), state_file=tmp_path / "propagation.json")
    signals = engine.propagate("A", "RISK", initial_strength=1.0, max_depth=3, world_date="2027-02-03")

    by_company = {x.affected_company_id: x for x in signals}
    assert by_company["B"].direction == "RISK"
    assert by_company["C"].direction == "RISK"
    assert by_company["C"].depth == 2
    assert by_company["C"].strength < by_company["B"].strength
    assert by_company["D"].direction == "OPPORTUNITY"
    assert by_company["D"].depth == 2


def test_propagation_does_not_loop(tmp_path):
    network = build_network(tmp_path)
    network.add_relationship("C", "A", "PARTNER_OF", confidence=0.8, evidence="cycle")
    engine = NetworkPropagationEngine(network, state_file=tmp_path / "propagation.json")
    signals = engine.propagate("A", "RISK", max_depth=6)
    assert all(x.depth <= 6 for x in signals)
    assert len({x.affected_company_id for x in signals}) == len(signals)


def test_invalid_direction_rejected(tmp_path):
    engine = NetworkPropagationEngine(build_network(tmp_path), state_file=tmp_path / "propagation.json")
    try:
        engine.propagate("A", "NEUTRAL")
        assert False
    except ValueError:
        assert True
