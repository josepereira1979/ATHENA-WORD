from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "world_api_state.json"


@dataclass
class APIState:
    world_date: str
    tick: int
    total_ticks: int
    registered_engines: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_sync: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    engine_name: str = "ATHENA WORLD - WORLD API"
    engine_version: str = "V01"


class WorldAPI:
    """
    ATHENA WORLD - WORLD API V01

    Interface central entre os motores da ATHENA WORLD.

    A API:
    - regista os motores;
    - expõe o estado dos motores;
    - sincroniza data/tick;
    - transporta estados entre componentes;
    - mantém relações de integração entre motores;
    - persiste o próprio estado.

    A API NÃO:
    - toma decisões económicas;
    - controla a lógica interna dos agentes;
    - cria famílias;
    - cria eventos;
    - altera mercados;
    - executa lógica própria dos motores.

    A API funciona como camada de interface e integração.
    """

    ENGINE_NAME = "ATHENA WORLD - WORLD API"
    ENGINE_VERSION = "V01"

    def __init__(
        self,
        world_date: Optional[str] = None,
        tick: int = 0,
    ) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        now = self._now()

        self.state = APIState(
            world_date=world_date or date.today().isoformat(),
            tick=max(0, int(tick)),
            total_ticks=max(0, int(tick)),
            created_at=now,
            updated_at=now,
            engine_name=self.ENGINE_NAME,
            engine_version=self.ENGINE_VERSION,
        )

        self.load()

    # ============================================================
    # UTILITÁRIOS
    # ============================================================

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _touch(self) -> None:
        self.state.updated_at = self._now()

    # ============================================================
    # INICIALIZAÇÃO
    # ============================================================

    def initialize(
        self,
        world_date: Optional[str] = None,
        tick: int = 0,
    ) -> Dict[str, Any]:
        self.state.world_date = world_date or date.today().isoformat()
        self.state.tick = max(0, self._safe_int(tick))
        self.state.total_ticks = self.state.tick
        self.state.last_sync = None
        self._touch()
        self.save()

        return self.get_status()

    # ============================================================
    # REGISTO DE MOTORES
    # ============================================================

    def register_engine(
        self,
        engine_name: str,
        engine_version: str = "V01",
        engine_type: str = "ENGINE",
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:

        if not engine_name:
            raise ValueError("engine_name não pode estar vazio.")

        self.state.registered_engines[engine_name] = {
            "engine_name": engine_name,
            "engine_version": engine_version,
            "engine_type": engine_type,
            "status": status,
            "registered_at": self._now(),
        }

        self._touch()
        self.save()

        return dict(self.state.registered_engines[engine_name])

    def unregister_engine(self, engine_name: str) -> bool:
        if engine_name not in self.state.registered_engines:
            return False

        del self.state.registered_engines[engine_name]

        self._touch()
        self.save()

        return True

    def get_engine(
        self,
        engine_name: str,
    ) -> Optional[Dict[str, Any]]:

        engine = self.state.registered_engines.get(engine_name)

        if engine is None:
            return None

        return dict(engine)

    def get_engines(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: dict(info)
            for name, info in self.state.registered_engines.items()
        }

    def engine_count(self) -> int:
        return len(self.state.registered_engines)

    # ============================================================
    # SINCRONIZAÇÃO DO MUNDO
    # ============================================================

    def sync_world(
        self,
        world_date: str,
        tick: int,
        total_ticks: Optional[int] = None,
    ) -> Dict[str, Any]:

        if not world_date:
            raise ValueError("world_date não pode estar vazio.")

        new_tick = max(0, self._safe_int(tick))

        self.state.world_date = world_date
        self.state.tick = new_tick

        if total_ticks is None:
            self.state.total_ticks = max(
                self.state.total_ticks,
                new_tick,
            )
        else:
            self.state.total_ticks = max(
                0,
                self._safe_int(total_ticks),
            )

        self.state.last_sync = self._now()

        self._touch()
        self.save()

        return self.get_world_time()

    def advance_tick(self, days: int = 1) -> Dict[str, Any]:
        days = self._safe_int(days, 1)

        if days < 1:
            raise ValueError("days tem de ser >= 1.")

        current_date = date.fromisoformat(self.state.world_date)

        new_date = current_date.fromordinal(
            current_date.toordinal() + days
        )

        self.state.world_date = new_date.isoformat()
        self.state.tick += days
        self.state.total_ticks += days
        self.state.last_sync = self._now()

        self._touch()
        self.save()

        return self.get_world_time()

    def get_world_time(self) -> Dict[str, Any]:
        return {
            "world_date": self.state.world_date,
            "tick": self.state.tick,
            "total_ticks": self.state.total_ticks,
        }

    # ============================================================
    # INTEGRAÇÃO AGENT ↔ FAMILY
    # ============================================================

    def assign_agent_to_family(
        self,
        agent_engine: Any,
        agent_id: str,
        family_id: str,
    ) -> Dict[str, Any]:
        """
        Liga um agente a uma família através da WORLD API.

        A API não cria nem controla o agente.
        Apenas coordena a relação entre os dois motores.

        Requer que o AgentEngine exponha:
            get_agent(agent_id)
            save()

        Retorna:
            {
                "success": True,
                "agent_id": "...",
                "family_id": "...",
            }
        """

        if agent_engine is None:
            raise ValueError("agent_engine não pode ser None.")

        if not agent_id:
            raise ValueError("agent_id não pode estar vazio.")

        if not family_id:
            raise ValueError("family_id não pode estar vazio.")

        if not hasattr(agent_engine, "get_agent"):
            raise TypeError(
                "agent_engine não possui o método get_agent()."
            )

        if not hasattr(agent_engine, "save"):
            raise TypeError(
                "agent_engine não possui o método save()."
            )

        agent = agent_engine.get_agent(agent_id)

        if agent is None:
            raise ValueError(
                f"Agente não encontrado: {agent_id}"
            )

        agent.family_id = family_id

        agent_engine.save()

        self._touch()
        self.save()

        return {
            "success": True,
            "agent_id": agent_id,
            "family_id": family_id,
        }

    def remove_agent_from_family(
        self,
        agent_engine: Any,
        agent_id: str,
    ) -> Dict[str, Any]:
        """
        Remove a associação do agente à família.

        Não elimina o agente nem a família.
        Apenas limpa Agent.family_id.
        """

        if agent_engine is None:
            raise ValueError("agent_engine não pode ser None.")

        if not agent_id:
            raise ValueError("agent_id não pode estar vazio.")

        if not hasattr(agent_engine, "get_agent"):
            raise TypeError(
                "agent_engine não possui o método get_agent()."
            )

        if not hasattr(agent_engine, "save"):
            raise TypeError(
                "agent_engine não possui o método save()."
            )

        agent = agent_engine.get_agent(agent_id)

        if agent is None:
            raise ValueError(
                f"Agente não encontrado: {agent_id}"
            )

        previous_family_id = agent.family_id

        agent.family_id = None

        agent_engine.save()

        self._touch()
        self.save()

        return {
            "success": True,
            "agent_id": agent_id,
            "previous_family_id": previous_family_id,
            "family_id": None,
        }

    # ============================================================
    # ESTADO
    # ============================================================

    def get_status(self) -> Dict[str, Any]:
        return {
            "engine_name": self.state.engine_name,
            "engine_version": self.state.engine_version,
            "world_date": self.state.world_date,
            "tick": self.state.tick,
            "total_ticks": self.state.total_ticks,
            "registered_engines": self.engine_count(),
            "last_sync": self.state.last_sync,
            "updated_at": self.state.updated_at,
        }

    def get_full_state(self) -> Dict[str, Any]:
        return asdict(self.state)

    # ============================================================
    # TRANSPORTE DE ESTADO DOS MOTORES
    # ============================================================

    def publish_engine_state(
        self,
        engine_name: str,
        engine_state: Dict[str, Any],
    ) -> bool:

        if engine_name not in self.state.registered_engines:
            self.register_engine(engine_name)

        self.state.registered_engines[engine_name][
            "last_state"
        ] = engine_state

        self.state.registered_engines[engine_name][
            "last_state_at"
        ] = self._now()

        self._touch()
        self.save()

        return True

    def get_engine_state(
        self,
        engine_name: str,
    ) -> Optional[Dict[str, Any]]:

        engine = self.state.registered_engines.get(engine_name)

        if engine is None:
            return None

        state = engine.get("last_state")

        if state is None:
            return None

        return dict(state)

    # ============================================================
    # PERSISTÊNCIA
    # ============================================================

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        temp_file = STATE_FILE.with_suffix(".tmp")

        with temp_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                asdict(self.state),
                file,
                ensure_ascii=False,
                indent=4,
            )

        temp_file.replace(STATE_FILE)

    def load(self) -> bool:
        if not STATE_FILE.exists():
            return False

        try:
            with STATE_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            self.state = APIState(
                world_date=data.get(
                    "world_date",
                    self.state.world_date,
                ),
                tick=self._safe_int(
                    data.get("tick", self.state.tick)
                ),
                total_ticks=self._safe_int(
                    data.get(
                        "total_ticks",
                        self.state.total_ticks,
                    )
                ),
                registered_engines=data.get(
                    "registered_engines",
                    {},
                ),
                last_sync=data.get("last_sync"),
                created_at=data.get(
                    "created_at",
                    self.state.created_at,
                ),
                updated_at=data.get(
                    "updated_at",
                    self.state.updated_at,
                ),
                engine_name=data.get(
                    "engine_name",
                    self.ENGINE_NAME,
                ),
                engine_version=data.get(
                    "engine_version",
                    self.ENGINE_VERSION,
                ),
            )

            return True

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ):
            return False

    def reset(self) -> None:
        now = self._now()

        self.state = APIState(
            world_date=date.today().isoformat(),
            tick=0,
            total_ticks=0,
            registered_engines={},
            last_sync=None,
            created_at=now,
            updated_at=now,
            engine_name=self.ENGINE_NAME,
            engine_version=self.ENGINE_VERSION,
        )

        self.save()

    # ============================================================
    # REPRESENTAÇÃO
    # ============================================================

    def __repr__(self) -> str:
        return (
            f"<WorldAPI "
            f"version={self.ENGINE_VERSION!r} "
            f"tick={self.state.tick} "
            f"engines={self.engine_count()}>"
        )


if __name__ == "__main__":
    api = WorldAPI()

    print("=" * 60)
    print("ATHENA WORLD - WORLD API")
    print("V01")
    print("=" * 60)

    print()
    print("STATUS")
    print(f"Data          : {api.state.world_date}")
    print(f"Tick          : {api.state.tick}")
    print(f"Total ticks   : {api.state.total_ticks}")
    print(f"Motores       : {api.engine_count()}")

    print()
    print("WORLD API V01 CARREGADA")
    print("=" * 60)