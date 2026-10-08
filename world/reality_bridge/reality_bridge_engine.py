from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .real_company_universe import RealCompanyUniverse


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "reality_bridge_state.json"

ENGINE_NAME = "ATHENA WORLD - REALITY BRIDGE ENGINE"
ENGINE_VERSION = "V01"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


# ==============================================================
# REAL COMPANY MAPPING
# ==============================================================

@dataclass
class RealCompanyMapping:
    mapping_id: str

    virtual_company_id: str
    virtual_company_name: str

    real_company_id: str
    real_company_name: str
    listing_id: Optional[str] = None

    ticker: Optional[str] = None
    exchange: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None

    active: bool = True

    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


# ==============================================================
# REAL DATA OBSERVATION
# ==============================================================

@dataclass
class RealDataObservation:
    observation_id: str

    mapping_id: str
    real_company_id: str

    data_type: str
    metric: str
    value: float

    observation_date: str

    source: str

    unit: Optional[str] = None

    created_at: str = field(default_factory=now_iso)


# ==============================================================
# REAL EVENT
# ==============================================================

@dataclass
class RealEvent:
    event_id: str

    mapping_id: Optional[str]

    real_company_id: Optional[str]

    event_type: str
    title: str
    description: str

    event_date: str

    source: str

    impact: float = 0.0

    created_at: str = field(default_factory=now_iso)


# ==============================================================
# COMPARISON
# ==============================================================

@dataclass
class WorldRealityComparison:
    comparison_id: str

    mapping_id: str

    virtual_metric: str
    virtual_value: float

    real_metric: str
    real_value: float

    difference: float
    difference_rate: float

    world_date: str
    real_date: str

    interpretation: str

    created_at: str = field(default_factory=now_iso)


# ==============================================================
# BRIDGE STATE
# ==============================================================

@dataclass
class RealityBridgeState:
    world_date: str

    tick: int = 0
    total_ticks: int = 0

    mappings: Dict[str, RealCompanyMapping] = field(
        default_factory=dict
    )

    real_observations: Dict[str, RealDataObservation] = field(
        default_factory=dict
    )

    real_events: Dict[str, RealEvent] = field(
        default_factory=dict
    )

    comparisons: Dict[str, WorldRealityComparison] = field(
        default_factory=dict
    )

    total_mappings: int = 0
    total_real_observations: int = 0
    total_real_events: int = 0
    total_comparisons: int = 0

    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


# ==============================================================
# REALITY BRIDGE ENGINE
# ==============================================================

class RealityBridgeEngine:

    def __init__(
        self,
        world_date: str = "2026-09-29",
        tick: int = 0,
        state_file: Optional[Path] = None,
        universe: Optional[RealCompanyUniverse] = None,
    ):

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.state_file = state_file or STATE_FILE
        self.universe = universe or RealCompanyUniverse()

        self.state = RealityBridgeState(
            world_date=world_date,
            tick=tick,
        )

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def initialize(
        self,
        world_date: str = "2026-09-29",
        tick: int = 0,
    ) -> None:

        self.state = RealityBridgeState(
            world_date=world_date,
            tick=tick,
        )

        self.save()

    # ==========================================================
    # COMPANY MAPPING
    # ==========================================================

    def create_mapping(
        self,
        virtual_company_id: str,
        virtual_company_name: str,
        real_company_id: str,
        real_company_name: str,
        listing_id: Optional[str] = None,
        ticker: Optional[str] = None,
        exchange: Optional[str] = None,
        country: Optional[str] = None,
        sector: Optional[str] = None,
    ) -> RealCompanyMapping:

        # ------------------------------------------------------
        # A identidade real deve apontar, quando disponível,
        # para o universo canónico de empresas/listagens.
        # ------------------------------------------------------
        if self.universe.get_company(real_company_id) is not None:
            if listing_id is not None:
                listing = self.universe.get_listing(listing_id)
                if listing is None or listing.real_company_id != real_company_id:
                    raise ValueError("listing_id não pertence à empresa real indicada.")
            else:
                primary = self.universe.get_primary_listing(real_company_id)
                if primary is not None:
                    listing_id = primary.listing_id

        # ------------------------------------------------------
        # Não permitir duas associações ativas para a mesma
        # empresa virtual.
        # ------------------------------------------------------

        existing = self.get_mapping_by_virtual_company(
            virtual_company_id
        )

        if existing is not None:
            raise ValueError(
                "A empresa virtual já possui uma associação."
            )

        mapping = RealCompanyMapping(
            mapping_id=new_id("MAP"),
            virtual_company_id=virtual_company_id,
            virtual_company_name=virtual_company_name,
            real_company_id=real_company_id,
            real_company_name=real_company_name,
            listing_id=listing_id,
            ticker=ticker,
            exchange=exchange,
            country=country,
            sector=sector,
        )

        self.state.mappings[mapping.mapping_id] = mapping

        self._update_totals()
        self._touch()
        self.save()

        return mapping

    # ==========================================================
    # MAPPING LOOKUPS
    # ==========================================================

    def get_mapping(
        self,
        mapping_id: str,
    ) -> Optional[RealCompanyMapping]:

        return self.state.mappings.get(mapping_id)

    def get_mapping_by_virtual_company(
        self,
        virtual_company_id: str,
    ) -> Optional[RealCompanyMapping]:

        for mapping in self.state.mappings.values():

            if (
                mapping.virtual_company_id
                == virtual_company_id
                and mapping.active
            ):
                return mapping

        return None

    def get_mapping_by_listing(
        self,
        listing_id: str,
    ) -> Optional[RealCompanyMapping]:
        for mapping in self.state.mappings.values():
            if mapping.active and mapping.listing_id == listing_id:
                return mapping
        return None

    def validate_real_identity(
        self,
        real_company_id: str,
        listing_id: Optional[str] = None,
    ) -> bool:
        company = self.universe.get_company(real_company_id)
        if company is None:
            return False
        if listing_id is None:
            return True
        listing = self.universe.get_listing(listing_id)
        return listing is not None and listing.real_company_id == real_company_id

    def get_mapping_by_real_company(
        self,
        real_company_id: str,
    ) -> Optional[RealCompanyMapping]:

        for mapping in self.state.mappings.values():

            if (
                mapping.real_company_id
                == real_company_id
                and mapping.active
            ):
                return mapping

        return None

    def get_all_mappings(
        self,
    ) -> List[RealCompanyMapping]:

        return list(
            self.state.mappings.values()
        )

    # ==========================================================
    # HIDE REAL IDENTITY FROM AGENTS
    # ==========================================================

    def get_agent_visible_company(
        self,
        virtual_company_id: str,
    ) -> Optional[Dict[str, str]]:

        mapping = self.get_mapping_by_virtual_company(
            virtual_company_id
        )

        if mapping is None:
            return None

        # ------------------------------------------------------
        # IMPORTANTE:
        #
        # Esta função devolve APENAS a identidade virtual.
        #
        # Nunca devolve:
        # - real_company_id
        # - real_company_name
        # - ticker
        # - exchange
        #
        # Os agentes não conhecem a empresa real.
        # ------------------------------------------------------

        return {
            "virtual_company_id":
                mapping.virtual_company_id,

            "virtual_company_name":
                mapping.virtual_company_name,
        }

    # ==========================================================
    # REAL DATA
    # ==========================================================

    def record_real_observation(
        self,
        mapping_id: str,
        data_type: str,
        metric: str,
        value: float,
        observation_date: str,
        source: str,
        unit: Optional[str] = None,
    ) -> RealDataObservation:

        mapping = self.get_mapping(mapping_id)

        if mapping is None:
            raise ValueError(
                "Mapping inexistente."
            )

        observation = RealDataObservation(
            observation_id=new_id("RDO"),
            mapping_id=mapping_id,
            real_company_id=mapping.real_company_id,
            data_type=data_type,
            metric=metric,
            value=float(value),
            observation_date=observation_date,
            source=source,
            unit=unit,
        )

        self.state.real_observations[
            observation.observation_id
        ] = observation

        self._update_totals()
        self._touch()
        self.save()

        return observation

    # ==========================================================
    # REAL EVENTS
    # ==========================================================

    def record_real_event(
        self,
        event_type: str,
        title: str,
        description: str,
        event_date: str,
        source: str,
        mapping_id: Optional[str] = None,
        real_company_id: Optional[str] = None,
        impact: float = 0.0,
    ) -> RealEvent:

        if mapping_id is not None:

            mapping = self.get_mapping(
                mapping_id
            )

            if mapping is None:
                raise ValueError(
                    "Mapping inexistente."
                )

            real_company_id = mapping.real_company_id

        event = RealEvent(
            event_id=new_id("REV"),
            mapping_id=mapping_id,
            real_company_id=real_company_id,
            event_type=event_type,
            title=title,
            description=description,
            event_date=event_date,
            source=source,
            impact=max(
                -1.0,
                min(1.0, float(impact)),
            ),
        )

        self.state.real_events[
            event.event_id
        ] = event

        self._update_totals()
        self._touch()
        self.save()

        return event

    # ==========================================================
    # WORLD / REALITY COMPARISON
    # ==========================================================

    def compare(
        self,
        mapping_id: str,
        virtual_metric: str,
        virtual_value: float,
        real_metric: str,
        real_value: float,
        world_date: Optional[str] = None,
        real_date: Optional[str] = None,
        interpretation: str = "",
    ) -> WorldRealityComparison:

        mapping = self.get_mapping(
            mapping_id
        )

        if mapping is None:
            raise ValueError(
                "Mapping inexistente."
            )

        if world_date is None:
            world_date = self.state.world_date

        if real_date is None:
            real_date = world_date

        virtual_value = float(
            virtual_value
        )

        real_value = float(
            real_value
        )

        difference = (
            virtual_value - real_value
        )

        if real_value != 0:

            difference_rate = (
                difference
                / abs(real_value)
            )

        else:
            difference_rate = 0.0

        comparison = WorldRealityComparison(
            comparison_id=new_id("CMP"),
            mapping_id=mapping_id,
            virtual_metric=virtual_metric,
            virtual_value=virtual_value,
            real_metric=real_metric,
            real_value=real_value,
            difference=difference,
            difference_rate=difference_rate,
            world_date=world_date,
            real_date=real_date,
            interpretation=interpretation,
        )

        self.state.comparisons[
            comparison.comparison_id
        ] = comparison

        self._update_totals()
        self._touch()
        self.save()

        return comparison

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_real_observation(
        self,
        observation_id: str,
    ) -> Optional[RealDataObservation]:

        return self.state.real_observations.get(
            observation_id
        )

    def get_real_event(
        self,
        event_id: str,
    ) -> Optional[RealEvent]:

        return self.state.real_events.get(
            event_id
        )

    def get_comparison(
        self,
        comparison_id: str,
    ) -> Optional[WorldRealityComparison]:

        return self.state.comparisons.get(
            comparison_id
        )

    def get_all_real_observations(
        self,
    ) -> List[RealDataObservation]:

        return list(
            self.state.real_observations.values()
        )

    def get_all_real_events(
        self,
    ) -> List[RealEvent]:

        return list(
            self.state.real_events.values()
        )

    def get_all_comparisons(
        self,
    ) -> List[WorldRealityComparison]:

        return list(
            self.state.comparisons.values()
        )

    # ==========================================================
    # TICK
    # ==========================================================

    def process_tick(
        self,
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> RealityBridgeState:

        if world_date is not None:
            self.state.world_date = world_date

        if tick is not None:
            self.state.tick = tick
        else:
            self.state.tick += 1

        self.state.total_ticks += 1

        self._touch()
        self.save()

        return self.state

    # ==========================================================
    # AGGREGATES
    # ==========================================================

    def aggregates(self) -> Dict[str, int]:

        return {
            "mappings":
                len(self.state.mappings),

            "real_observations":
                len(
                    self.state.real_observations
                ),

            "real_events":
                len(
                    self.state.real_events
                ),

            "comparisons":
                len(
                    self.state.comparisons
                ),
        }

    # ==========================================================
    # PERSISTENCE
    # ==========================================================

    def save(self) -> None:

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.state.updated_at = now_iso()

        payload = asdict(
            self.state
        )

        with self.state_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=4,
            )

    def load(self) -> None:

        if not self.state_file.exists():
            return

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        self.state = RealityBridgeState(
            world_date=data[
                "world_date"
            ],

            tick=data.get(
                "tick",
                0,
            ),

            total_ticks=data.get(
                "total_ticks",
                0,
            ),

            mappings={
                key:
                    RealCompanyMapping(**{**value, "listing_id": value.get("listing_id")})

                for key, value
                in data.get(
                    "mappings",
                    {},
                ).items()
            },

            real_observations={
                key:
                    RealDataObservation(**value)

                for key, value
                in data.get(
                    "real_observations",
                    {},
                ).items()
            },

            real_events={
                key:
                    RealEvent(**value)

                for key, value
                in data.get(
                    "real_events",
                    {},
                ).items()
            },

            comparisons={
                key:
                    WorldRealityComparison(**value)

                for key, value
                in data.get(
                    "comparisons",
                    {},
                ).items()
            },

            total_mappings=data.get(
                "total_mappings",
                len(
                    data.get(
                        "mappings",
                        {},
                    )
                ),
            ),

            total_real_observations=data.get(
                "total_real_observations",
                len(
                    data.get(
                        "real_observations",
                        {},
                    )
                ),
            ),

            total_real_events=data.get(
                "total_real_events",
                len(
                    data.get(
                        "real_events",
                        {},
                    )
                ),
            ),

            total_comparisons=data.get(
                "total_comparisons",
                len(
                    data.get(
                        "comparisons",
                        {},
                    )
                ),
            ),

            created_at=data.get(
                "created_at",
                now_iso(),
            ),

            updated_at=data.get(
                "updated_at",
                now_iso(),
            ),

            engine_name=data.get(
                "engine_name",
                ENGINE_NAME,
            ),

            engine_version=data.get(
                "engine_version",
                ENGINE_VERSION,
            ),
        )

    def reset(self) -> None:

        self.state = RealityBridgeState(
            world_date="2026-09-29",
            tick=0,
        )

        self.save()

    # ==========================================================
    # INTERNAL
    # ==========================================================

    def _update_totals(self) -> None:

        self.state.total_mappings = (
            len(self.state.mappings)
        )

        self.state.total_real_observations = (
            len(
                self.state.real_observations
            )
        )

        self.state.total_real_events = (
            len(
                self.state.real_events
            )
        )

        self.state.total_comparisons = (
            len(
                self.state.comparisons
            )
        )

    def _touch(self) -> None:

        self.state.updated_at = now_iso()


# ==============================================================
# TESTE DO ENGINE
# ==============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(ENGINE_NAME)
    print(ENGINE_VERSION)
    print("=" * 60)

    bridge = RealityBridgeEngine(
        world_date="2026-09-29",
        tick=0,
    )

    bridge.reset()

    # ----------------------------------------------------------
    # MAPPING
    #
    # A associação abaixo é apenas de teste.
    # ----------------------------------------------------------

    mapping = bridge.create_mapping(
        virtual_company_id="COMPANY-001",
        virtual_company_name="Atlas Industries",
        real_company_id="REAL-001",
        real_company_name="Real Company Example",
        ticker="EXMP",
        exchange="TEST",
        country="USA",
        sector="TECHNOLOGY",
    )

    # ----------------------------------------------------------
    # VISÃO DO AGENTE
    # ----------------------------------------------------------

    agent_view = bridge.get_agent_visible_company(
        "COMPANY-001"
    )

    # ----------------------------------------------------------
    # DADOS REAIS
    # ----------------------------------------------------------

    real_observation = (
        bridge.record_real_observation(
            mapping_id=mapping.mapping_id,
            data_type="MARKET",
            metric="PRICE",
            value=150.0,
            observation_date="2026-09-29",
            source="TEST_SOURCE",
            unit="USD",
        )
    )

    # ----------------------------------------------------------
    # EVENTO REAL
    # ----------------------------------------------------------

    real_event = bridge.record_real_event(
        mapping_id=mapping.mapping_id,
        event_type="CORPORATE",
        title="Resultado trimestral",
        description=(
            "Evento real utilizado para teste "
            "da ponte de realidade."
        ),
        event_date="2026-09-29",
        source="TEST_SOURCE",
        impact=0.40,
    )

    # ----------------------------------------------------------
    # COMPARAÇÃO
    # ----------------------------------------------------------

    comparison = bridge.compare(
        mapping_id=mapping.mapping_id,
        virtual_metric="PRICE",
        virtual_value=135.0,
        real_metric="PRICE",
        real_value=150.0,
        world_date="2026-09-29",
        real_date="2026-09-29",
        interpretation=(
            "O preço virtual encontra-se abaixo "
            "do preço observado no mundo real."
        ),
    )

    # ----------------------------------------------------------
    # RESULTADOS
    # ----------------------------------------------------------

    print()
    print("MAPPING")
    print(
        f"Virtual       : "
        f"{mapping.virtual_company_name}"
    )
    print(
        f"Real          : "
        f"{mapping.real_company_name}"
    )
    print(
        f"Ticker        : "
        f"{mapping.ticker}"
    )

    print()
    print("VISÃO DO AGENTE")
    print(
        f"Empresa       : "
        f"{agent_view['virtual_company_name']}"
    )
    print(
        "Identidade real: OCULTA"
    )

    print()
    print("DADOS REAIS")
    print(
        f"Métrica       : "
        f"{real_observation.metric}"
    )
    print(
        f"Valor         : "
        f"{real_observation.value:.2f}"
    )
    print(
        f"Fonte         : "
        f"{real_observation.source}"
    )

    print()
    print("EVENTO REAL")
    print(
        f"Tipo          : "
        f"{real_event.event_type}"
    )
    print(
        f"Título        : "
        f"{real_event.title}"
    )
    print(
        f"Impacto       : "
        f"{real_event.impact:.2%}"
    )

    print()
    print("COMPARAÇÃO")
    print(
        f"Virtual       : "
        f"{comparison.virtual_value:.2f}"
    )
    print(
        f"Real          : "
        f"{comparison.real_value:.2f}"
    )
    print(
        f"Diferença     : "
        f"{comparison.difference:.2f}"
    )
    print(
        f"Diferença %   : "
        f"{comparison.difference_rate:.2%}"
    )

    print()
    print("AGREGADOS")
    aggregates = bridge.aggregates()

    print(
        f"Mappings      : "
        f"{aggregates['mappings']}"
    )
    print(
        f"Dados reais   : "
        f"{aggregates['real_observations']}"
    )
    print(
        f"Eventos reais : "
        f"{aggregates['real_events']}"
    )
    print(
        f"Comparações   : "
        f"{aggregates['comparisons']}"
    )

    # ----------------------------------------------------------
    # TICK
    # ----------------------------------------------------------

    bridge.process_tick(
        world_date="2026-09-30",
        tick=1,
    )

    print()
    print("APÓS 1 TICK")
    print(
        f"Tick          : "
        f"{bridge.state.tick}"
    )
    print(
        f"Data          : "
        f"{bridge.state.world_date}"
    )

    print()
    print(
        "REALITY BRIDGE ENGINE V01 "
        "TESTE CONCLUIDO"
    )
    print("=" * 60)