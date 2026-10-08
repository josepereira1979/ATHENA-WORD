# ATHENA WORLD - WORLD RUNTIME V01

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from world.core.world_core import WorldCore
from world.orchestration.world_orchestrator import WorldOrchestrator
from world.agents.agent_engine import AgentEngine
from world.families.family_engine import FamilyEngine
from world.companies.company_engine import CompanyEngine
from world.economy.economy_engine import EconomyEngine
from world.resources.resource_engine import ResourceEngine
from world.infrastructure.infrastructure_engine import InfrastructureEngine
from world.market.market_engine import MarketEngine
from world.financial.financial_engine import FinancialEngine
from world.events.event_engine import EventEngine
from world.observer.observer_engine import ObserverEngine
from world.learning.learning_engine import LearningEngine
from world.reality_bridge.reality_bridge_engine import RealityBridgeEngine
from world.intelligence.prediction_engine import PredictionEngine
from world.reality_bridge.real_company_universe import RealCompanyUniverse


class WorldRuntime:
    """Monta o mundo real de engines sobre um único WorldCore.

    Não executa nenhum tick ao ser criado. A execução só acontece
    quando run_cycle()/run_cycles() é chamada explicitamente.
    """

    ENGINE_NAME = "ATHENA WORLD - WORLD RUNTIME"
    ENGINE_VERSION = "V01"

    def __init__(
        self,
        world_core: WorldCore | None = None,
        state_dir: Path | None = None,
        auto_load: bool = True,
    ) -> None:
        self.world_core = world_core or WorldCore()
        self.state_dir = Path(state_dir) if state_dir else Path(__file__).resolve().parents[2] / "data"\n\n        def sf(name: str) -> Path:\n            return self.state_dir / name

        self.engines: Dict[str, Any] = {
            "AGENT": AgentEngine(state_file=sf("agents_state.json"), auto_load=auto_load),
            "FAMILY": FamilyEngine(state_file=sf("families_state.json"), auto_load=auto_load),
            "COMPANY": CompanyEngine(state_file=sf("companies_state.json"), auto_load=auto_load),
            "ECONOMY": EconomyEngine(state_file=sf("economy_state.json"), auto_load=auto_load),
            "RESOURCE": ResourceEngine(state_file=sf("resources_state.json")),
            "INFRASTRUCTURE": InfrastructureEngine(state_file=sf("infrastructure_state.json")),
            "MARKET": MarketEngine(state_file=sf("market_state.json")),
            "FINANCIAL": FinancialEngine(state_file=sf("financial_state.json")),
            "EVENT": EventEngine(state_file=sf("events_state.json")),
            "OBSERVER": ObserverEngine(state_file=sf("observer_state.json")),
            "LEARNING": LearningEngine(state_file=sf("learning_state.json")),
            "REALITY_BRIDGE": RealityBridgeEngine(
                world_date=self.world_core.state["world_date"],
                tick=self.world_core.state["tick"],
                state_file=sf("reality_bridge_state.json"),
                universe=RealCompanyUniverse(state_file=sf("real_company_universe_state.json")),
            ),
        }

        self.prediction_engine = PredictionEngine(
            state_file=sf("prediction_state.json"),
            auto_load=auto_load,
        )

        self.orchestrator = WorldOrchestrator(self.world_core)
        self.orchestrator.register_engines({
            name: engine
            for name, engine in self.engines.items()
            if callable(getattr(engine, "process_tick", None))
        })

    def run_cycle(self) -> Dict[str, Any]:
        return self.orchestrator.run_cycle()

    def run_cycles(self, count: int) -> Dict[str, Any]:
        return self.orchestrator.run_cycles(count)

    def processor_names(self) -> list[str]:
        return self.orchestrator.get_processor_names()
