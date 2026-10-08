# ATHENA WORLD - WORLD RUNTIME V01

from __future__ import annotations

from datetime import date, timedelta
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
from world.reality_bridge.real_world_connection import RealWorldConnection
from world.reality_bridge.real_world_source_registry import RealWorldSourceRegistry
from world.intelligence.corporate_network_engine import CorporateNetworkEngine
from world.intelligence.network_propagation_engine import NetworkPropagationEngine
from world.intelligence.network_shock_processor import NetworkShockProcessor
from world.intelligence.network_shock_queue import NetworkShockQueue
from world.intelligence.family_company_expansion import FamilyCompanyExpansion
from world.intelligence.global_family_market_allocator import GlobalFamilyMarketAllocator
from world.intelligence.global_market_census import GlobalMarketCensus
from world.intelligence.global_world_population import GlobalWorldPopulationEngine
from world.intelligence.global_world_finalizer import GlobalWorldFinalizer
from world.intelligence.world_control_center import WorldControlCenter
from world.intelligence.corporate_network_intelligence import CorporateNetworkIntelligence
from world.orchestration.world_launch_controller import WorldLaunchController


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

        def sf(name: str) -> Path:
            return self.state_dir / name

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

        self.corporate_network = CorporateNetworkEngine(
            state_file=sf("corporate_network_state.json"),
            universe=self.engines["REALITY_BRIDGE"].universe,
        )
        self.corporate_network_engine = self.corporate_network
        self.network_propagation = NetworkPropagationEngine(
            self.corporate_network,
            state_file=sf("network_propagation_state.json"),
        )
        self.network_shock_queue = NetworkShockQueue(
            state_file=sf("network_shock_queue_state.json"),
        )
        self.global_family_market_allocator = GlobalFamilyMarketAllocator(self)
        self._global_market_census = GlobalMarketCensus(self)
        self.global_world_population = GlobalWorldPopulationEngine(self)
        self.global_world_finalizer = GlobalWorldFinalizer(self)
        self.real_world_connection = RealWorldConnection(self)
        self.real_world_sources = RealWorldSourceRegistry()
        self.control_center = WorldControlCenter(self)
        self.launch_controller = WorldLaunchController(self)
        self.corporate_network_intelligence = CorporateNetworkIntelligence(self.corporate_network, self.engines['FAMILY'], self.engines['LEARNING'])
        self.family_company_expansion = FamilyCompanyExpansion(
            family_engine=self.engines["FAMILY"],
            company_engine=self.engines["COMPANY"],
            universe=self.engines["REALITY_BRIDGE"].universe,
            runtime=self,
        )
        self.network_shock_processor = NetworkShockProcessor(
            self.network_propagation,
            family_engine=self.engines["FAMILY"],
            learning_engine=self.engines["LEARNING"],
        )

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
        self.orchestrator.register_processor(
            "REAL_NETWORK_INTELLIGENCE",
            self._process_real_network_intelligence,
        )
        self.orchestrator.register_processor(
            "CORPORATE_NETWORK_INTELLIGENCE",
            self._process_corporate_network_intelligence,
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

        self.prediction_engine.close_expired(world_date)

        learning = self.engines["LEARNING"]
        learning.process_tick(world_date)
        learning.learn_from_validated_predictions(
            self.prediction_engine.get_all_predictions(),
            world_date=world_date,
        )
        self._update_family_intelligence(world_date)
        self._update_collective_intelligence(world_date)
        self._create_family_predictions(world_date)
        self._update_family_reputation()

    def _process_corporate_network_intelligence(self, world_date: str) -> None:
        self.corporate_network_intelligence.process(world_date)

    def _process_real_network_intelligence(self, world_date: str) -> None:
        """Executa choques reais previamente colocados na fila de propagação."""
        for shock in self.network_shock_queue.get_pending():
            self.network_shock_processor.process_shock(
                origin_company_id=shock.origin_company_id,
                direction=shock.direction,
                strength=shock.strength,
                world_date=world_date,
                max_depth=shock.max_depth,
                min_strength=shock.min_strength,
                source_event_id=shock.source_event_id,
                source_observation_id=shock.source_observation_id,
            )
            self.network_shock_queue.mark_processed(shock.shock_id)

    def ingest_real_observation(
        self,
        real_company_id: str,
        metric: str,
        value: float,
        observation_date: str,
        source: str,
        data_type: str = "REAL",
        unit: str | None = None,
    ) -> Dict[str, Any]:
        bridge = self.engines["REALITY_BRIDGE"]
        mapping = bridge.get_mapping_by_real_company(real_company_id)
        if mapping is None:
            raise ValueError("A empresa real ainda não possui uma empresa WORLD atribuída.")
        real_observation = bridge.record_real_observation(
            mapping_id=mapping.mapping_id,
            data_type=data_type,
            metric=metric,
            value=value,
            observation_date=observation_date,
            source=source,
            unit=unit,
        )
        observer = self.engines["OBSERVER"]
        previous = observer.get_latest_observation(mapping.virtual_company_id, metric)
        world_observation = observer.ingest(
            source_engine="REALITY_BRIDGE",
            subject_id=mapping.virtual_company_id,
            subject_type="COMPANY",
            metric=metric,
            value=float(value),
            previous_value=float(previous.value) if previous is not None else None,
            world_date=observation_date,
            tick=int(self.world_core.state["tick"]),
        )
        for prediction in self.prediction_engine.get_open_predictions():
            if prediction.subject_id == mapping.virtual_company_id and prediction.metric == metric:
                if prediction.horizon_start <= observation_date <= prediction.horizon_end:
                    self.prediction_engine.validate_from_observation(
                        prediction.prediction_id,
                        world_observation,
                    )
        return {
            "real_observation_id": real_observation.observation_id,
            "world_observation_id": world_observation.observation_id,
            "virtual_company_id": mapping.virtual_company_id,
            "prediction_accuracy": self.prediction_engine.accuracy(mapping.virtual_company_id),
        }

    def ingest_real_event(
        self,
        event_type: str,
        title: str,
        description: str,
        event_date: str,
        source: str,
        real_company_id: str | None = None,
        impact: float = 0.0,
        direction: str | None = None,
    ) -> Dict[str, Any]:
        bridge = self.engines["REALITY_BRIDGE"]
        mapping = bridge.get_mapping_by_real_company(real_company_id) if real_company_id else None
        event = bridge.record_real_event(
            event_type=event_type,
            title=title,
            description=description,
            event_date=event_date,
            source=source,
            mapping_id=mapping.mapping_id if mapping else None,
            real_company_id=real_company_id,
            impact=impact,
        )
        shock = None
        if real_company_id and direction:
            shock = self.queue_real_network_shock(
                origin_company_id=real_company_id,
                direction=direction,
                strength=abs(float(impact)),
                world_date=event_date,
                source_event_id=event.event_id,
            )
        return {"event_id": event.event_id, "shock": shock}

    def connect_real_world(self, records, allocate: bool = True) -> Dict[str, Any]:
        return self.real_world_connection.ingest_and_finalize(records, allocate=allocate)

    def real_world_sources_status(self) -> Dict[str, Any]:
        return {"sources": self.real_world_sources.list_sources(), "connection": self.real_world_connection.status()}

    def finalize_global_world(self) -> Dict[str, Any]:
        return self.global_world_finalizer.finalize(self.world_core.state['world_date'])

    def launch_readiness(self) -> Dict[str, Any]:
        return self.launch_controller.readiness()

    def prepare_world(self, allocate: bool = False, cycles: int = 0) -> Dict[str, Any]:
        return self.launch_controller.prepare(allocate=allocate, cycles=cycles)

    def world_snapshot(self) -> Dict[str, Any]:
        return self.control_center.snapshot()

    def world_integrity(self) -> Dict[str, Any]:
        return self.control_center.integrity()

    def world_full_report(self) -> Dict[str, Any]:
        return self.control_center.full_report()
    def global_world_status(self) -> Dict[str, Any]:
        return self.global_world_population.status()

    def preview_global_world(self, limit: int | None = None) -> Dict[str, Any]:
        return self.global_world_population.preview(limit=limit)

    def ingest_global_companies(self, records, allocate: bool = False) -> Dict[str, Any]:
        return self.global_world_population.ingest_records(records, allocate=allocate)

    def sync_sec_global_companies(self, user_agent: str, max_new: int | None = None, allocate: bool = False) -> Dict[str, Any]:
        return self.global_world_population.ingest_sec(user_agent, max_new=max_new, allocate=allocate)
    def global_market_census(self) -> Dict[str, Any]:
        return self._global_market_census.build()

    def global_market_readiness(self) -> Dict[str, Any]:
        return self._global_market_census.readiness()
    def preview_global_family_market_allocation(self, limit: int | None = None) -> Dict[str, Any]:
        return self.global_family_market_allocator.preview(limit=limit)

    def allocate_global_family_market(self, limit: int | None = None) -> Dict[str, Any]:
        return self.global_family_market_allocator.allocate(limit=limit)

    def global_family_market_report(self) -> Dict[str, Any]:
        return self.global_family_market_allocator.report()
    def expand_real_company_world(self, limit: int | None = None) -> Dict[str, Any]:
        """Cria empresas virtuais e atribui famílias, mantendo relação 1:1."""
        return self.family_company_expansion.expand(
            world_date=self.world_core.state["world_date"],
            limit=limit,
        )

    def queue_real_network_shock(
        self,
        origin_company_id: str,
        direction: str,
        strength: float = 1.0,
        world_date: str | None = None,
        max_depth: int = 3,
        min_strength: float = 0.10,
        source_event_id: str | None = None,
        source_observation_id: str | None = None,
    ) -> Dict[str, Any]:
        """Coloca um choque empresarial real na fila para o próximo ciclo."""
        row = self.network_shock_queue.enqueue(
            origin_company_id=origin_company_id,
            direction=direction,
            strength=strength,
            world_date=world_date or self.world_core.state["world_date"],
            max_depth=max_depth,
            min_strength=min_strength,
            source_event_id=source_event_id,
            source_observation_id=source_observation_id,
        )
        return {
            "shock_id": row.shock_id,
            "origin_company_id": row.origin_company_id,
            "direction": row.direction,
            "strength": row.strength,
            "status": row.status,
        }

    def _build_observations(self, world_date: str, tick: int) -> list[dict]:
        observer = self.engines["OBSERVER"]
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
                previous = observer.get_latest_observation(asset.asset_id, "PRICE")
                observations.append({
                    "source_engine": "MARKET",
                    "subject_id": asset.asset_id,
                    "subject_type": "ASSET",
                    "metric": "PRICE",
                    "value": float(asset.last_price),
                    "previous_value": float(previous.value) if previous is not None else float(asset.previous_price),
                })

        for resource in self.engines["RESOURCE"].get_all_resources():
            if resource.active:
                previous = observer.get_latest_observation(resource.resource_id, "PRICE")
                observations.append({
                    "source_engine": "RESOURCE",
                    "subject_id": resource.resource_id,
                    "subject_type": "RESOURCE",
                    "metric": "PRICE",
                    "value": float(resource.price),
                    "previous_value": float(previous.value) if previous is not None else float(resource.base_price),
                })

        for company in self.engines["COMPANY"].companies.values():
            if company.status == "ACTIVE":
                previous_revenue = observer.get_latest_observation(company.company_id, "REVENUE")
                previous_profit = observer.get_latest_observation(company.company_id, "PROFIT")
                previous_growth = observer.get_latest_observation(company.company_id, "GROWTH_RATE")
                if previous_revenue is not None and previous_revenue.value != 0:
                    company.growth_rate = (
                        float(company.revenue) - float(previous_revenue.value)
                    ) / abs(float(previous_revenue.value))
                observations.extend([
                    {
                        "source_engine": "COMPANY",
                        "subject_id": company.company_id,
                        "subject_type": "COMPANY",
                        "metric": "REVENUE",
                        "value": float(company.revenue),
                        "previous_value": float(previous_revenue.value) if previous_revenue is not None else None,
                    },
                    {
                        "source_engine": "COMPANY",
                        "subject_id": company.company_id,
                        "subject_type": "COMPANY",
                        "metric": "PROFIT",
                        "value": float(company.profit),
                        "previous_value": float(previous_profit.value) if previous_profit is not None else None,
                    },
                    {
                        "source_engine": "COMPANY",
                        "subject_id": company.company_id,
                        "subject_type": "COMPANY",
                        "metric": "GROWTH_RATE",
                        "value": float(company.growth_rate),
                        "previous_value": float(previous_growth.value) if previous_growth is not None else None,
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

    def _update_collective_intelligence(self, world_date: str) -> None:
        """Transforma relações empresariais em evidência partilhável pelas famílias."""
        family_engine = self.engines["FAMILY"]
        company_engine = self.engines["COMPANY"]
        learning = self.engines["LEARNING"]
        observer = self.engines["OBSERVER"]

        companies = company_engine.get_all_companies()
        by_id = {company.company_id: company for company in companies}
        existing = {
            hypothesis.statement
            for hypothesis in observer.get_all_hypotheses()
        }

        for family in family_engine.get_all_families():
            if not family.alive or not family.virtual_company_id:
                continue

            company = by_id.get(family.virtual_company_id)
            if company is None:
                continue

            related = []
            for relation_type, ids in (
                ("SUPPLIER", company.supplier_ids),
                ("CUSTOMER", company.customer_ids),
                ("COMPETITOR", company.competitor_ids),
            ):
                for related_id in ids:
                    related_company = by_id.get(related_id)
                    if related_company is None:
                        continue
                    related.append((relation_type, related_company))

                    learning.record_experience(
                        owner_id=family.family_id,
                        owner_type="FAMILY",
                        world_date=world_date,
                        event_type="NETWORK_SIGNAL",
                        description=(
                            f"{relation_type}: {related_company.company_id} "
                            f"-> {company.company_id}; "
                            f"profit={related_company.profit:.6f}; "
                            f"growth={related_company.growth_rate:.6f}"
                        ),
                        outcome="OBSERVED",
                        success=True,
                        impact=0.0,
                        learning_value=0.04,
                        knowledge_domain="NETWORK",
                        lesson=(
                            "A evolução de uma empresa relacionada pode "
                            "antecipar ou contrariar a empresa atribuída."
                        ),
                    )

            if not related:
                continue

            positive = [
                item for item in related
                if item[1].growth_rate > 0
            ]
            if len(positive) < len(related):
                continue

            statement = (
                f"As empresas relacionadas com {company.company_name} "
                f"podem estar a sinalizar pressão positiva sobre o seu crescimento."
            )
            if statement in existing:
                continue

            hypothesis = observer.create_hypothesis(
                statement=statement,
                confidence=min(0.90, 0.50 + 0.05 * len(positive)),
                world_date=world_date,
                tick=int(self.world_core.state["tick"]),
            )

            learning.record_experience(
                owner_id=family.family_id,
                owner_type="FAMILY",
                world_date=world_date,
                event_type="COLLECTIVE_HYPOTHESIS",
                description=hypothesis.statement,
                outcome="OPEN",
                success=True,
                impact=hypothesis.confidence,
                learning_value=0.06,
                knowledge_domain="INTELLIGENCE",
                lesson=(
                    "Uma hipótese foi construída a partir de sinais "
                    "de empresas relacionadas."
                ),
            )
            existing.add(statement)

        learning._refresh_aggregates()
        learning.save()

    def _create_family_predictions(self, world_date: str) -> None:
        family_engine = self.engines["FAMILY"]
        company_engine = self.engines["COMPANY"]
        prediction_engine = self.prediction_engine
        companies = {x.company_id: x for x in company_engine.get_all_companies() if x.status == "ACTIVE"}
        existing = {(x.owner_id, x.subject_id, x.metric) for x in prediction_engine.get_open_predictions() if x.owner_type == "FAMILY"}
        for family in family_engine.get_all_families():
            if not family.alive or not family.virtual_company_id:
                continue
            company = companies.get(family.virtual_company_id)
            if company is None:
                continue
            related = []
            for relation_type, ids in (("SUPPLIER", company.supplier_ids), ("CUSTOMER", company.customer_ids), ("COMPETITOR", company.competitor_ids)):
                for related_id in ids:
                    related_company = companies.get(related_id)
                    if related_company is not None:
                        related.append((relation_type, related_company))
            if not related or not all(x[1].growth_rate > 0 for x in related):
                continue
            key = (family.family_id, company.company_id, "GROWTH_RATE")
            if key in existing:
                continue
            prediction_engine.create_prediction(
                owner_id=family.family_id, owner_type="FAMILY", subject_id=company.company_id, subject_type="COMPANY",
                metric="GROWTH_RATE",
                statement=f"A família {family.family_name} prevê crescimento positivo em {company.company_name} no próximo período.",
                horizon_start=(date.fromisoformat(world_date) + timedelta(days=1)).isoformat(), horizon_end=(date.fromisoformat(world_date) + timedelta(days=1)).isoformat(), confidence=min(0.90, 0.55 + 0.05 * len(related)),
                predicted_direction="UP",
                supporting_evidence=[f"{r}:{x.company_id}" for r, x in related],
                invalidation_condition="Crescimento da empresa não positivo no período.",
            )
            family.intelligence_specialization = company.sector or "GENERAL"
            existing.add(key)
        family_engine.save()

    def _update_family_reputation(self) -> None:
        family_engine = self.engines["FAMILY"]
        for family in family_engine.get_all_families():
            if not family.alive:
                continue
            rows = self.prediction_engine.get_predictions_by_owner(family.family_id, owner_type="FAMILY")
            validated = [x for x in rows if x.status == "VALIDATED" and x.outcome in {"CORRECT", "WRONG", "PARTIAL"}]
            family.predictions_count = len(rows)
            family.predictions_correct = sum(1 for x in validated if x.outcome == "CORRECT")
            family.predictions_wrong = sum(1 for x in validated if x.outcome == "WRONG")
            if validated:
                family.intelligence_score = round(sum(1.0 if x.outcome == "CORRECT" else 0.5 if x.outcome == "PARTIAL" else 0.0 for x in validated) / len(validated), 6)
        family_engine.save()
    def assign_family_to_real_company(
        self,
        family_id: str,
        virtual_company_id: str,
        real_company_id: str,
        listing_id: str | None = None,
        world_date: str | None = None,
    ) -> Dict[str, Any]:
        """Prepara uma atribuição família -> empresa real validada pelo Reality Bridge.

        Não aceita uma identidade inventada: a empresa e a listagem têm de existir
        no universo canónico. A ligação fica registada simultaneamente na família,
        na empresa virtual e no Reality Bridge.
        """
        family_engine = self.engines["FAMILY"]
        company_engine = self.engines["COMPANY"]
        bridge = self.engines["REALITY_BRIDGE"]
        universe = bridge.universe

        family = family_engine.get_family(family_id)
        company = company_engine.get_company(virtual_company_id)
        real_company = universe.get_company(real_company_id)

        if family is None or not family.alive:
            raise ValueError("Família inexistente ou inactiva.")
        if company is None or company.status != "ACTIVE":
            raise ValueError("Empresa virtual inexistente ou inactiva.")
        if real_company is None or not real_company.active:
            raise ValueError("Empresa real inexistente ou inactiva.")

        listing = universe.get_listing(listing_id) if listing_id else universe.get_primary_listing(real_company_id)
        if listing is None or not listing.active:
            raise ValueError("A empresa real não possui uma listagem activa.")
        if listing.real_company_id != real_company_id:
            raise ValueError("A listagem indicada não pertence à empresa real.")

        if family.virtual_company_id not in (None, virtual_company_id):
            raise ValueError("A família já tem outra empresa atribuída.")

        existing_family = family_engine.get_family_by_company(virtual_company_id)
        if existing_family is not None and existing_family.family_id != family_id:
            raise ValueError("A empresa virtual já está atribuída a outra família.")

        existing_real = company_engine.get_company_by_real_id(real_company_id)
        if existing_real is not None and existing_real.company_id != virtual_company_id:
            raise ValueError("A empresa real já está ligada a outra empresa virtual.")

        existing_mapping = bridge.get_mapping_by_virtual_company(virtual_company_id)
        if existing_mapping is not None and existing_mapping.real_company_id != real_company_id:
            raise ValueError("A empresa virtual já possui outro mapping real.")

        now = world_date or self.world_core.state["world_date"]

        if existing_mapping is None:
            bridge.create_mapping(
                virtual_company_id=company.company_id,
                virtual_company_name=company.company_name,
                real_company_id=real_company.real_company_id,
                real_company_name=real_company.legal_name,
                listing_id=listing.listing_id,
                ticker=listing.ticker,
                exchange=listing.exchange,
                country=real_company.country,
                sector=real_company.sector,
            )

        if not company_engine.link_real_company(company.company_id, real_company.real_company_id):
            raise ValueError("Não foi possível ligar a empresa virtual à identidade real.")

        if not family_engine.link_company(
            family.family_id,
            company.company_id,
            real_company.real_company_id,
            world_date=now,
        ):
            raise ValueError("Não foi possível atribuir a empresa à família.")

        from world.reality_bridge.exchange_registry import classify_exchange
        profile = classify_exchange(listing.exchange)
        family_engine.set_market_identity(
            family.family_id,
            region=profile.region,
            country=listing.country or real_company.country,
            exchange=listing.exchange,
            market_group=profile.group,
            listing_id=listing.listing_id,
            world_date=now,
        )

        return {
            "family_id": family.family_id,
            "virtual_company_id": company.company_id,
            "real_company_id": real_company.real_company_id,
            "real_company_name": real_company.legal_name,
            "listing_id": listing.listing_id,
            "ticker": listing.ticker,
            "exchange": listing.exchange,
            "world_date": now,
            "status": "ASSIGNED",
        }

    def prepare_real_company_assignments(self) -> Dict[str, Any]:
        """Lista famílias livres e empresas reais válidas para futura distribuição."""
        family_engine = self.engines["FAMILY"]
        universe = self.engines["REALITY_BRIDGE"].universe
        families = family_engine.get_unassigned_families()
        companies = [x for x in universe.get_all_companies() if x.active and universe.get_primary_listing(x.real_company_id)]
        return {
            "families_available": len(families),
            "real_companies_available": len(companies),
            "families": [x.family_id for x in families],
            "real_companies": [
                {"real_company_id": x.real_company_id, "legal_name": x.legal_name, "sector": x.sector, "country": x.country}
                for x in companies
            ],
            "status": "READY_FOR_ASSIGNMENT",
        }
    def ingest_real_relationships(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingere relações empresariais reais com proveniência e confiança."""
        bridge = self.engines["REALITY_BRIDGE"]
        universe = bridge.universe
        accepted = []
        rejected = []
        for row in relationships:
            source = universe.get_company(row.get("source_real_company_id", ""))
            target = universe.get_company(row.get("target_real_company_id", ""))
            relation_type = str(row.get("relation_type", "")).upper().strip()
            confidence = float(row.get("confidence", 0.0))
            if source is None or target is None or source.real_company_id == target.real_company_id:
                rejected.append({"reason": "INVALID_COMPANIES", "relationship": row})
                continue
            if not relation_type or not 0.0 <= confidence <= 1.0:
                rejected.append({"reason": "INVALID_RELATION", "relationship": row})
                continue
            accepted.append({
                "source_real_company_id": source.real_company_id,
                "target_real_company_id": target.real_company_id,
                "relation_type": relation_type,
                "confidence": confidence,
                "source": row.get("source"),
                "evidence": row.get("evidence"),
                "active": True,
            })
        return {"accepted": accepted, "rejected": rejected, "accepted_count": len(accepted), "rejected_count": len(rejected)}
    def run_cycle(self) -> Dict[str, Any]:
        return self.orchestrator.run_cycle()

    def run_cycles(self, count: int) -> Dict[str, Any]:
        return self.orchestrator.run_cycles(count)

    def processor_names(self) -> list[str]:
        return self.orchestrator.get_processor_names()
