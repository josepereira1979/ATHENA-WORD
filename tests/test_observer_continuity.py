from pathlib import Path

from world.observer.observer_engine import ObserverEngine


def test_latest_observation_survives_and_returns_latest(tmp_path: Path):
    engine = ObserverEngine(state_file=tmp_path / "observer.json")
    engine.observe("TEST", "COMPANY-1", "COMPANY", "REVENUE", 100, world_date="2027-01-01", tick=1)
    engine.observe("TEST", "COMPANY-1", "COMPANY", "REVENUE", 120, previous_value=100, world_date="2027-01-02", tick=2)
    latest = engine.get_latest_observation("COMPANY-1", "REVENUE")
    assert latest is not None
    assert latest.value == 120
