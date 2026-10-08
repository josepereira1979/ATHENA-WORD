from world.intelligence.network_shock_queue import NetworkShockQueue


def test_queue_lifecycle(tmp_path):
    queue = NetworkShockQueue(tmp_path / "queue.json")
    row = queue.enqueue("REAL-1", "RISK", strength=0.8, world_date="2027-02-05")
    assert row.status == "PENDING"
    assert len(queue.get_pending()) == 1
    queue.mark_processed(row.shock_id)
    assert queue.get_pending() == []
    reloaded = NetworkShockQueue(tmp_path / "queue.json")
    assert reloaded.shocks[0].status == "PROCESSED"


def test_queue_rejects_invalid_direction(tmp_path):
    queue = NetworkShockQueue(tmp_path / "queue.json")
    try:
        queue.enqueue("REAL-1", "FLAT")
        assert False
    except ValueError:
        assert True
