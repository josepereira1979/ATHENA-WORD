from __future__ import annotations

import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD
# EVENT ENGINE V01
# ============================================================
#
# Responsabilidade:
#   - acontecimentos internos
#   - acontecimentos externos
#   - eventos económicos
#   - eventos empresariais
#   - eventos sociais
#   - eventos tecnológicos
#   - eventos de recursos
#   - eventos financeiros
#   - eventos geopolíticos
#   - probabilidade
#   - duração
#   - intensidade
#   - impacto potencial
#   - histórico de eventos
#
# O Event Engine gera e mantém acontecimentos.
#
# NÃO controla diretamente:
#   - agentes
#   - empresas
#   - economia
#   - recursos
#   - infraestrutura
#   - mercados
#   - sistema financeiro
#
# Os efeitos dos eventos serão posteriormente transmitidos
# através de interfaces/eventos entre os diferentes motores.
#
# ============================================================


ENGINE_NAME = "ATHENA WORLD - EVENT ENGINE"
ENGINE_VERSION = "V01"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "events_state.json"


# ============================================================
# EVENTO
# ============================================================


@dataclass
class WorldEvent:
    event_id: str

    name: str
    category: str
    event_type: str

    description: str

    origin: str = "INTERNAL"

    probability: float = 0.0
    intensity: float = 0.0

    duration_ticks: int = 1
    remaining_ticks: int = 1

    # Impacto potencial por sistema
    economic_impact: float = 0.0
    company_impact: float = 0.0
    resource_impact: float = 0.0
    infrastructure_impact: float = 0.0
    market_impact: float = 0.0
    financial_impact: float = 0.0
    social_impact: float = 0.0
    technology_impact: float = 0.0

    status: str = "ACTIVE"

    world_date: str = ""
    created_at: str = ""
    updated_at: str = ""


# ============================================================
# ESTADO
# ============================================================


@dataclass
class EventState:
    world_date: str

    tick: int = 0
    total_ticks: int = 0

    events: Dict[str, WorldEvent] = field(
        default_factory=dict
    )

    total_events: int = 0
    active_events: int = 0
    completed_events: int = 0

    events_generated: int = 0
    events_completed: int = 0

    created_at: str = ""
    updated_at: str = ""

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


# ============================================================
# EVENT ENGINE
# ============================================================


class EventEngine:

    def __init__(
        self,
        state_file: Optional[Path] = None,
        random_seed: Optional[int] = None,
    ) -> None:

        self.state_file = (
            Path(state_file)
            if state_file
            else STATE_FILE
        )

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.state: Optional[EventState] = None

        self.random = random.Random(
            random_seed
        )

    # ========================================================
    # UTILIDADES
    # ========================================================

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat()

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:

        return max(
            minimum,
            min(maximum, float(value)),
        )

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def initialize(
        self,
        world_date: str,
    ) -> EventState:

        now = self._now()

        self.state = EventState(
            world_date=world_date,
            tick=0,
            total_ticks=0,
            events={},
            total_events=0,
            active_events=0,
            completed_events=0,
            events_generated=0,
            events_completed=0,
            created_at=now,
            updated_at=now,
        )

        self._save()

        return self.state

    # ========================================================
    # CRIAR EVENTO
    # ========================================================

    def create_event(
        self,
        name: str,
        category: str,
        event_type: str,
        description: str,
        origin: str = "INTERNAL",
        probability: float = 0.0,
        intensity: float = 0.5,
        duration_ticks: int = 1,
        economic_impact: float = 0.0,
        company_impact: float = 0.0,
        resource_impact: float = 0.0,
        infrastructure_impact: float = 0.0,
        market_impact: float = 0.0,
        financial_impact: float = 0.0,
        social_impact: float = 0.0,
        technology_impact: float = 0.0,
    ) -> WorldEvent:

        self._require_state()

        now = self._now()

        duration_ticks = max(
            1,
            int(duration_ticks),
        )

        event_id = (
            "EVENT-"
            + uuid.uuid4().hex[:12].upper()
        )

        event = WorldEvent(
            event_id=event_id,
            name=name,
            category=category,
            event_type=event_type,
            description=description,
            origin=origin.upper(),
            probability=self._clamp(
                probability
            ),
            intensity=self._clamp(
                intensity
            ),
            duration_ticks=duration_ticks,
            remaining_ticks=duration_ticks,
            economic_impact=self._clamp(
                economic_impact,
                -1.0,
                1.0,
            ),
            company_impact=self._clamp(
                company_impact,
                -1.0,
                1.0,
            ),
            resource_impact=self._clamp(
                resource_impact,
                -1.0,
                1.0,
            ),
            infrastructure_impact=self._clamp(
                infrastructure_impact,
                -1.0,
                1.0,
            ),
            market_impact=self._clamp(
                market_impact,
                -1.0,
                1.0,
            ),
            financial_impact=self._clamp(
                financial_impact,
                -1.0,
                1.0,
            ),
            social_impact=self._clamp(
                social_impact,
                -1.0,
                1.0,
            ),
            technology_impact=self._clamp(
                technology_impact,
                -1.0,
                1.0,
            ),
            status="ACTIVE",
            world_date=self.state.world_date,
            created_at=now,
            updated_at=now,
        )

        self.state.events[event_id] = event

        self.state.events_generated += 1

        self._refresh_aggregates()
        self._touch()
        self._save()

        return event

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_event(
        self,
        event_id: str,
    ) -> WorldEvent:

        self._require_state()

        try:
            return self.state.events[
                event_id
            ]
        except KeyError:
            raise KeyError(
                f"Event not found: {event_id}"
            )

    def get_all_events(
        self,
    ) -> List[WorldEvent]:

        self._require_state()

        return list(
            self.state.events.values()
        )

    def get_active_events(
        self,
    ) -> List[WorldEvent]:

        self._require_state()

        return [
            event
            for event in self.state.events.values()
            if event.status == "ACTIVE"
        ]

    # ========================================================
    # GERAÇÃO PROBABILÍSTICA
    # ========================================================

    def generate_event(
        self,
        event_template: Dict[str, object],
    ) -> Optional[WorldEvent]:

        self._require_state()

        probability = self._clamp(
            float(
                event_template.get(
                    "probability",
                    0.0,
                )
            )
        )

        roll = self.random.random()

        if roll > probability:
            return None

        return self.create_event(
            name=str(
                event_template.get(
                    "name",
                    "Unknown Event",
                )
            ),
            category=str(
                event_template.get(
                    "category",
                    "GENERAL",
                )
            ),
            event_type=str(
                event_template.get(
                    "event_type",
                    "RANDOM_EVENT",
                )
            ),
            description=str(
                event_template.get(
                    "description",
                    "",
                )
            ),
            origin=str(
                event_template.get(
                    "origin",
                    "INTERNAL",
                )
            ),
            probability=probability,
            intensity=float(
                event_template.get(
                    "intensity",
                    0.5,
                )
            ),
            duration_ticks=int(
                event_template.get(
                    "duration_ticks",
                    1,
                )
            ),
            economic_impact=float(
                event_template.get(
                    "economic_impact",
                    0.0,
                )
            ),
            company_impact=float(
                event_template.get(
                    "company_impact",
                    0.0,
                )
            ),
            resource_impact=float(
                event_template.get(
                    "resource_impact",
                    0.0,
                )
            ),
            infrastructure_impact=float(
                event_template.get(
                    "infrastructure_impact",
                    0.0,
                )
            ),
            market_impact=float(
                event_template.get(
                    "market_impact",
                    0.0,
                )
            ),
            financial_impact=float(
                event_template.get(
                    "financial_impact",
                    0.0,
                )
            ),
            social_impact=float(
                event_template.get(
                    "social_impact",
                    0.0,
                )
            ),
            technology_impact=float(
                event_template.get(
                    "technology_impact",
                    0.0,
                )
            ),
        )

    # ========================================================
    # TICK
    # ========================================================

    def process_tick(
        self,
        world_date: str,
    ) -> EventState:

        self._require_state()

        self.state.tick += 1
        self.state.total_ticks += 1
        self.state.world_date = world_date

        for event in (
            self.state.events.values()
        ):

            if event.status != "ACTIVE":
                continue

            event.remaining_ticks = max(
                0,
                event.remaining_ticks - 1,
            )

            event.updated_at = self._now()

            if event.remaining_ticks <= 0:

                event.status = "COMPLETED"

                self.state.events_completed += 1

        self._refresh_aggregates()
        self._touch()
        self._save()

        return self.state

    # ========================================================
    # EVENTOS PRÉ-DEFINIDOS
    # ========================================================

    def create_internal_event(
        self,
        name: str,
        category: str,
        description: str,
        intensity: float = 0.5,
        duration_ticks: int = 1,
        economic_impact: float = 0.0,
        company_impact: float = 0.0,
        resource_impact: float = 0.0,
        infrastructure_impact: float = 0.0,
        market_impact: float = 0.0,
        financial_impact: float = 0.0,
        social_impact: float = 0.0,
        technology_impact: float = 0.0,
    ) -> WorldEvent:

        return self.create_event(
            name=name,
            category=category,
            event_type="INTERNAL_EVENT",
            description=description,
            origin="INTERNAL",
            probability=1.0,
            intensity=intensity,
            duration_ticks=duration_ticks,
            economic_impact=economic_impact,
            company_impact=company_impact,
            resource_impact=resource_impact,
            infrastructure_impact=(
                infrastructure_impact
            ),
            market_impact=market_impact,
            financial_impact=financial_impact,
            social_impact=social_impact,
            technology_impact=technology_impact,
        )

    def create_external_event(
        self,
        name: str,
        category: str,
        description: str,
        intensity: float = 0.5,
        duration_ticks: int = 1,
        economic_impact: float = 0.0,
        company_impact: float = 0.0,
        resource_impact: float = 0.0,
        infrastructure_impact: float = 0.0,
        market_impact: float = 0.0,
        financial_impact: float = 0.0,
        social_impact: float = 0.0,
        technology_impact: float = 0.0,
    ) -> WorldEvent:

        return self.create_event(
            name=name,
            category=category,
            event_type="EXTERNAL_EVENT",
            description=description,
            origin="EXTERNAL",
            probability=1.0,
            intensity=intensity,
            duration_ticks=duration_ticks,
            economic_impact=economic_impact,
            company_impact=company_impact,
            resource_impact=resource_impact,
            infrastructure_impact=(
                infrastructure_impact
            ),
            market_impact=market_impact,
            financial_impact=financial_impact,
            social_impact=social_impact,
            technology_impact=technology_impact,
        )

    # ========================================================
    # AGREGADOS
    # ========================================================

    def _refresh_aggregates(
        self,
    ) -> None:

        if self.state is None:
            return

        events = list(
            self.state.events.values()
        )

        self.state.total_events = len(
            events
        )

        self.state.active_events = sum(
            1
            for event in events
            if event.status == "ACTIVE"
        )

        self.state.completed_events = sum(
            1
            for event in events
            if event.status == "COMPLETED"
        )

    # ========================================================
    # ESTADO
    # ========================================================

    def _require_state(
        self,
    ) -> None:

        if self.state is None:
            raise RuntimeError(
                "EventEngine is not initialized."
            )

    def _touch(
        self,
    ) -> None:

        if self.state is not None:
            self.state.updated_at = (
                self._now()
            )

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    def save(self) -> None:
        self._save()

    def _save(self) -> None:

        if self.state is None:
            return

        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

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

    def load(
        self,
    ) -> EventState:

        if not self.state_file.exists():

            raise FileNotFoundError(
                "Event state file not found: "
                f"{self.state_file}"
            )

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        events = {}

        for event_id, event_data in (
            data.get(
                "events",
                {},
            ).items()
        ):

            events[event_id] = WorldEvent(
                **event_data
            )

        data["events"] = events

        self.state = EventState(
            **data
        )

        return self.state

    def reset(self) -> None:

        self.state = None

        if self.state_file.exists():
            self.state_file.unlink()


# ============================================================
# TESTE MANUAL
# ============================================================


if __name__ == "__main__":

    print("=" * 60)
    print(ENGINE_NAME)
    print(ENGINE_VERSION)
    print("=" * 60)

    engine = EventEngine(
        random_seed=42
    )

    engine.initialize(
        world_date="2026-09-29"
    )

    # --------------------------------------------------------
    # EVENTO INTERNO
    # --------------------------------------------------------

    company_event = (
        engine.create_internal_event(
            name="Falha de Produção",
            category="COMPANY",
            description=(
                "Uma empresa sofre uma falha "
                "inesperada na produção."
            ),
            intensity=0.60,
            duration_ticks=3,
            economic_impact=-0.10,
            company_impact=-0.30,
            resource_impact=0.0,
            market_impact=-0.05,
            financial_impact=-0.10,
        )
    )

    # --------------------------------------------------------
    # EVENTO EXTERNO
    # --------------------------------------------------------

    energy_event = (
        engine.create_external_event(
            name="Crise Energética",
            category="ENERGY",
            description=(
                "Uma perturbação externa "
                "reduz a disponibilidade energética."
            ),
            intensity=0.80,
            duration_ticks=5,
            economic_impact=-0.20,
            company_impact=-0.15,
            resource_impact=-0.40,
            market_impact=-0.20,
            financial_impact=-0.15,
            social_impact=-0.10,
        )
    )

    # --------------------------------------------------------
    # EVENTO PROBABILÍSTICO
    # --------------------------------------------------------

    random_event = (
        engine.generate_event(
            {
                "name": "Descoberta Tecnológica",
                "category": "TECHNOLOGY",
                "event_type": "DISCOVERY",
                "description": (
                    "Surge uma nova tecnologia "
                    "com potencial económico."
                ),
                "origin": "INTERNAL",
                "probability": 1.0,
                "intensity": 0.70,
                "duration_ticks": 4,
                "economic_impact": 0.15,
                "company_impact": 0.20,
                "market_impact": 0.10,
                "financial_impact": 0.10,
                "technology_impact": 0.50,
            }
        )
    )

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    print()
    print("EVENTOS CRIADOS")
    print(
        "Total         :",
        engine.state.total_events,
    )

    print(
        "Ativos        :",
        engine.state.active_events,
    )

    print()

    for event in (
        engine.get_active_events()
    ):

        print(
            event.name,
            "|",
            event.category,
            "|",
            event.origin,
            "| intensidade:",
            f"{event.intensity:.2f}",
            "| duração:",
            event.remaining_ticks,
        )

    # --------------------------------------------------------
    # TICK
    # --------------------------------------------------------

    engine.process_tick(
        "2026-10-29"
    )

    print()
    print("APÓS 1 TICK")

    print(
        "Tick          :",
        engine.state.tick,
    )

    print(
        "Data          :",
        engine.state.world_date,
    )

    print(
        "Eventos ativos:",
        engine.state.active_events,
    )

    print(
        "Concluídos    :",
        engine.state.completed_events,
    )

    print()

    print(
        "EVENT ENGINE V01 "
        "TESTE CONCLUIDO"
    )

    print("=" * 60)