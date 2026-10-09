# ATHENA WORLD - ORCHESTRATOR TEST V01

from datetime import date, timedelta
from pathlib import Path
import tempfile

from world.core.world_core import WorldCore
from world.orchestration.world_orchestrator import WorldOrchestrator


def test_orchestrator_keeps_one_world_date_for_all_processors():
    with tempfile.TemporaryDirectory() as tmp:
        core = WorldCore(state_file=Path(tmp) / "world.json")
        seen = []

        def processor(world_date):
            seen.append(world_date)

        orchestrator = WorldOrchestrator(core)
        orchestrator.register_processor("TEST", processor)
        result = orchestrator.run_cycles(3)

        assert result["cycles"] == 3
        assert len(seen) == 3
        assert seen[-1] == core.get_world_date()
        assert core.get_tick() == 3
        assert seen == [
            (date.today() + timedelta(days=1)).isoformat(),
            (date.today() + timedelta(days=2)).isoformat(),
            (date.today() + timedelta(days=3)).isoformat(),
        ]
