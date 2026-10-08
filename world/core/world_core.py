"""
ATHENA WORLD
WORLD CORE ENGINE - V01

Motor 1 do ATHENA WORLD.

Responsabilidades:
- Criar e identificar um mundo.
- Controlar o relógio virtual.
- Controlar ticks da simulação.
- Controlar a velocidade da simulação.
- Pausar e retomar o mundo.
- Persistir o estado do mundo.
- Permitir avançar o mundo manualmente.
- Fornecer um estado seguro para os restantes motores.

IMPORTANTE:
Este motor não conhece agentes, empresas, mercados ou economia.
Ele apenas controla o tempo e o estado fundamental do mundo.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ENGINE_NAME = "ATHENA WORLD - WORLD CORE ENGINE"
ENGINE_VERSION = "V01"

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "world_state.json"


@dataclass
class WorldState:
    """
    Estado fundamental de um mundo ATHENA.
    """

    world_id: str
    world_name: str

    status: str

    world_date: str

    tick: int
    total_ticks: int

    simulation_speed: float

    paused: bool

    created_at: str
    updated_at: str

    engine_name: str
    engine_version: str


class WorldCore:
    """
    Motor central de tempo e estado do ATHENA WORLD.
    """

    def __init__(
        self,
        world_name: str = "ATHENA WORLD",
        state_file: Path | None = None,
    ) -> None:

        self.state_file = state_file or STATE_FILE

        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.state_file.exists():
            self.state = self._load_state()
        else:
            self.state = self._create_world(
                world_name=world_name,
            )

            self.save()

    # ------------------------------------------------------------------
    # WORLD CREATION
    # ------------------------------------------------------------------

    def _create_world(
        self,
        world_name: str,
    ) -> WorldState:

        today = date.today().isoformat()

        now = self._now_iso()

        return WorldState(
            world_id=self._generate_world_id(),
            world_name=world_name,
            status="ACTIVE",
            world_date=today,
            tick=0,
            total_ticks=0,
            simulation_speed=1.0,
            paused=False,
            created_at=now,
            updated_at=now,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
        )

    @staticmethod
    def _generate_world_id() -> str:
        """
        Gera um identificador único para o mundo.
        """

        return f"WORLD-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _now_iso() -> str:
        """
        Timestamp UTC em formato ISO.
        """

        from datetime import datetime, timezone

        return datetime.now(
            timezone.utc
        ).isoformat()

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def save(self) -> None:
        """
        Guarda o estado actual do mundo.
        """

        self.state.updated_at = self._now_iso()

        payload = asdict(self.state)

        temporary_file = self.state_file.with_suffix(
            ".tmp"
        )

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                payload,
                file,
                indent=4,
                ensure_ascii=False,
            )

        temporary_file.replace(
            self.state_file
        )

    def _load_state(self) -> WorldState:
        """
        Carrega o estado persistido.
        """

        try:

            with self.state_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                payload = json.load(file)

            return WorldState(
                **payload
            )

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:

            raise RuntimeError(
                f"Não foi possível carregar o estado do mundo: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # TIME CONTROL
    # ------------------------------------------------------------------

    def tick_once(self) -> dict[str, Any]:
        """
        Avança exactamente um tick.

        Por enquanto:
        1 tick = 1 dia virtual.

        Os restantes motores serão ligados futuramente
        a este ciclo.
        """

        if self.state.status != "ACTIVE":
            raise RuntimeError(
                "O mundo não está activo."
            )

        if self.state.paused:
            raise RuntimeError(
                "O mundo está pausado."
            )

        current_date = date.fromisoformat(
            self.state.world_date
        )

        next_date = current_date + timedelta(
            days=1
        )

        self.state.world_date = next_date.isoformat()

        self.state.tick += 1

        self.state.total_ticks += 1

        self.save()

        return self.get_state()

    def advance(
        self,
        ticks: int,
    ) -> dict[str, Any]:

        if not isinstance(
            ticks,
            int,
        ):
            raise TypeError(
                "ticks tem de ser um inteiro."
            )

        if ticks < 1:
            raise ValueError(
                "ticks tem de ser maior que zero."
            )

        for _ in range(ticks):
            self.tick_once()

        return self.get_state()

    # ------------------------------------------------------------------
    # PAUSE / RESUME
    # ------------------------------------------------------------------

    def pause(self) -> None:
        """
        Pausa a simulação.
        """

        if self.state.status != "ACTIVE":
            raise RuntimeError(
                "O mundo não está activo."
            )

        self.state.paused = True

        self.save()

    def resume(self) -> None:
        """
        Retoma a simulação.
        """

        if self.state.status != "ACTIVE":
            raise RuntimeError(
                "O mundo não está activo."
            )

        self.state.paused = False

        self.save()

    # ------------------------------------------------------------------
    # WORLD STATUS
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """
        Coloca o mundo em estado STOPPED.

        Esta função existe desde já para permitir
        controlo futuro do ciclo de vida.
        """

        self.state.status = "STOPPED"

        self.state.paused = True

        self.save()

    def activate(self) -> None:
        """
        Reactiva um mundo parado.
        """

        self.state.status = "ACTIVE"

        self.state.paused = False

        self.save()

    # ------------------------------------------------------------------
    # SIMULATION SPEED
    # ------------------------------------------------------------------

    def set_speed(
        self,
        speed: float,
    ) -> None:

        if not isinstance(
            speed,
            (int, float),
        ):
            raise TypeError(
                "speed tem de ser numérico."
            )

        if speed <= 0:
            raise ValueError(
                "speed tem de ser maior que zero."
            )

        self.state.simulation_speed = float(
            speed
        )

        self.save()

    # ------------------------------------------------------------------
    # INFORMATION
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """
        Devolve o estado actual do mundo.
        """

        return asdict(
            self.state
        )

    def get_world_id(self) -> str:
        return self.state.world_id

    def get_world_date(self) -> str:
        return self.state.world_date

    def get_tick(self) -> int:
        return self.state.tick

    def is_paused(self) -> bool:
        return self.state.paused

    # ------------------------------------------------------------------
    # RESET
    # ------------------------------------------------------------------

    def reset(
        self,
        world_name: str | None = None,
    ) -> None:

        name = (
            world_name
            if world_name
            else self.state.world_name
        )

        self.state = self._create_world(
            world_name=name
        )

        self.save()


def main() -> None:
    """
    Teste simples do WORLD CORE ENGINE.
    """

    core = WorldCore()

    print()
    print("=" * 70)
    print(ENGINE_NAME)
    print("=" * 70)

    print(
        f"World ID       : {core.get_world_id()}"
    )

    print(
        f"World Name     : {core.state.world_name}"
    )

    print(
        f"World Date     : {core.get_world_date()}"
    )

    print(
        f"Tick           : {core.get_tick()}"
    )

    print(
        f"Status         : {core.state.status}"
    )

    print(
        f"Paused         : {core.is_paused()}"
    )

    print(
        f"Speed          : {core.state.simulation_speed}"
    )

    print(
        f"State File     : {core.state_file}"
    )

    print("=" * 70)
    print("WORLD CORE ENGINE carregado com sucesso.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()