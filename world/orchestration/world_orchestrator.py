# ATHENA WORLD - WORLD ORCHESTRATOR V01

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class WorldOrchestrator:
    """Coordena os motores por tick sem absorver a lógica dos engines."""

    ENGINE_NAME = "ATHENA WORLD - WORLD ORCHESTRATOR"
    ENGINE_VERSION = "V01"

    def __init__(self, world_core: Any, processors: Optional[Dict[str, Callable[[str], None]]] = None):
        self.world_core = world_core
        self.processors = processors or {}

    def register_processor(self, name: str, processor: Callable[[str], None]) -> None:
        if not name or not callable(processor):
            raise ValueError("name e processor válidos são obrigatórios.")
        self.processors[name] = processor

    def run_cycle(self) -> Dict[str, Any]:
        state = self.world_core.tick_once()
        world_date = state["world_date"]
        executed = []
        for name, processor in self.processors.items():
            processor(world_date)
            executed.append(name)
        return {"world_date": world_date, "tick": state["tick"], "processors_run": executed, "processor_count": len(executed)}

    def run_cycles(self, count: int) -> Dict[str, Any]:
        if not isinstance(count, int) or count < 1:
            raise ValueError("count tem de ser um inteiro >= 1.")
        last = None
        for _ in range(count):
            last = self.run_cycle()
        return {"cycles": count, "last": last, "processors": list(self.processors.keys())}
