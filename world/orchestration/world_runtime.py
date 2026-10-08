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
        self.state_dir = Path(state_dir) if state_dir else Path(__file__).resolve().parents[2] / "data"

        def sf(name: str) -> Path:\n            return self.state_dir / name

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

        # Ordem causal: realidade -> economia/recursos -> empresas/mercados
        # -> agentes/famílias -> observação -> validação -> aprendizagem.
        runtime_engines = {
            "REALITY_BRIDGE": self.engines["REALITY_BRIDGE"],
            "ECONOMY": self.engines["ECONOMY"],
            "RESOURCE": self.engines["RESOURCE"],
            "INFRASTRUCTURE": self.engines["INFRASTRUCTURE"],
            "EVENT": self.engines["EVENT"],
            "COMPANY": self.engines["COMPANY"],
            "MARKET": self.engines["MARKET"],
            "FINANCIAL": self.engines["FINANCIAL"],
            "AGENT": self.engines["AGENT"],
            "FAMILY": self.engines["FAMILY"],
        }
        self.orchestrator.register_engines(runtime_engines)
        self.orchestrator.register_processor(
            "INTELLIGENCE",
            self._process_intelligence_cycle,
        )

    def _process_intelligence_cycle(self, world_date: str) -> None:
        tick = int(self.world_core.state["tick"])
        observer = self.engines["OBSERVER"]
        observer.process_tick(world_date, tick)

        observations = self._build_observations(world_date, tick)
        if observations:
            created = observer.ingest_batch(
                observations,
                world_date=world_date,
                tick=tick,
            )
            open_predictions = self.prediction_engine.get_open_predictions()
            for observation in created:
                for prediction in open_predictions:
                    if prediction.subject_id != observation.subject_id:
                        continue
                    if prediction.metric != observation.metric:
                        continue
                    if not (prediction.horizon_start <= observation.world_date <= prediction.horizon_end):
                        continue
                    self.prediction_engine.validate_from_observation(
                        prediction.prediction_id,
                        observation,
                    )

        learning = self.engines["LEARNING"]
        learning.process_tick(world_date)
        learning.learn_from_validated_predictions(
            self.prediction_engine.get_all_predictions(),
            world_date=world_date,
        )

    def _build_observations(self, world_date: str, tick: int) -> list[dict]:
        observations: list[dict] = []

        economy = self.engines["ECONOMY"].get_state()
        if economy is not None:
            observations.extend([
                {
                    "source_engine": "ECONOMY",
                    "subject_id": "WORLD-ECONOMY",
                    "subject_type": "ECONOMY",
                    "metric": "REAL_GDP",
                    "value": float(economy.real_gdp),
                    "previous_value": float(economy.previous_real_gdp),
                },
                {
                    "source_engine": "ECONOMY",
                    "subject_id": "WORLD-ECONOMY",
                    "subject_type": "ECONOMY",
                    "metric": "INFLATION_RATE",
                    "value": float(economy.inflation_rate),
                    "previous_value": None,
                },
            ])

        for asset in self.engines["MARKET"].get_all_assets():
            if asset.active:
                observations.append({
                    "source_engine": "MARKET",
                    "subject_id": asset.asset_id,
                    "subject_type": "ASSET",
                    "metric": "PRICE",
                    "value": float(asset.last_price),
                    "previous_value": float(asset.previous_price),
                })

        for resource in self.engines["RESOURCE"].get_all_resources():
            if resource.active:
                observations.append({
                    "source_engine": "RESOURCE",
                    "subject_id": resource.resource_id,
                    "subject_type": "RESOURCE",
                    "metric": "PRICE",
                    "value": float(resource.price),
                    "previous_value": float(resource.base_price),
                })

        for company in self.engines["COMPANY"].companies.values():
            if company.status == "ACTIVE":
                observations.extend([
                    {
                        "source_engine": "COMPANY",
                        "subject_id": company.company_id,
                        "subject_type": "COMPANY",
                        "metric": "REVENUE",
                        "value": float(company.revenue),
                        "previous_value": None,
                    },
                    {
                        "source_engine": "COMPANY",
                        "subject_id": company.company_id,
                        "subject_type": "COMPANY",
                        "metric": "PROFIT",
                        "value": float(company.profit),
                        "previous_value": None,
                    },
                ])

        return observations

    def _update_family_intelligence(self, world_date: str) -> None:
        family_engine = self.engines["FAMILY"]
        company_engine = self.engines["COMPANY"]
        learning = self.engines["LEARNING"]

        for family in family_engine.get_all_families():
            if not family.alive or not family.virtual_company_id:
                continue
            company = company_engine.get_company(family.virtual_company_id)
            if company is None:
                continue

            metrics = {
                "REVENUE": float(company.revenue),
                "PROFIT": float(company.profit),
                "CASH": float(company.cash),
                "DEBT": float(company.debt),
                "PRODUCTIVITY": float(company.productivity),
                "REPUTATION": float(company.reputation),
                "GROWTH_RATE": float(company.growth_rate),
            }

            for metric, value in metrics.items():
                learning.record_experience(
                    owner_id=family.family_id,
                    owner_type="FAMILY",
                    world_date=world_date,
                    event_type="COMPANY_INTELLIGENCE",
                    description=f"{company.company_id} {metric}={value:.6f}",
                    outcome="OBSERVED",
                    success=True,
                    impact=0.0,
                    learning_value=0.02,
                    knowledge_domain="FINANCE",
                    lesson=f"Acompanhar {metric} da empresa {company.company_name}.",
                )

        learning._refresh_aggregates()
        learning.save()

    def run_cycle(self) -> Dict[str, Any]:
        return self.orchestrator.run_cycle()

    def run_cycles(self, count: int) -> Dict[str, Any]:
        return self.orchestrator.run_cycles(count)

    def processor_names(self) -> list[str]:
        return self.orchestrator.get_processor_names()
