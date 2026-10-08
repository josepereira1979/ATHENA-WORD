from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD
# RESOURCE ENGINE V01
# ============================================================
#
# Responsabilidade:
#   - recursos naturais e matérias-primas
#   - produção
#   - consumo
#   - reservas / stocks
#   - disponibilidade
#   - preços
#   - escassez / excesso
#   - importações / exportações
#   - evolução dos recursos ao longo do tempo
#
# Este motor NÃO controla:
#   - empresas
#   - agentes
#   - economia
#   - mercados financeiros
#
# Esses motores deverão comunicar com o Resource Engine
# através de interfaces/eventos numa fase posterior.
#
# Unidade temporal:
#   - cada tick representa um período definido pelo mundo
#   - o motor não assume que um tick é obrigatoriamente um dia
#
# ============================================================


ENGINE_NAME = "ATHENA WORLD - RESOURCE ENGINE"
ENGINE_VERSION = "V01"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "resources_state.json"


# ============================================================
# RECURSO
# ============================================================


@dataclass
class Resource:
    resource_id: str
    name: str
    category: str
    unit: str

    # Estado físico/económico
    reserves: float = 0.0
    production_capacity: float = 0.0
    production: float = 0.0
    consumption: float = 0.0

    # Comércio
    imports: float = 0.0
    exports: float = 0.0

    # Mercado
    price: float = 0.0
    base_price: float = 0.0

    # Indicadores
    availability: float = 1.0
    scarcity: float = 0.0
    surplus: float = 0.0

    # Controlo
    renewable: bool = False
    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# ESTADO DO RESOURCE ENGINE
# ============================================================


@dataclass
class ResourceState:
    world_date: str

    tick: int = 0
    total_ticks: int = 0

    resources: Dict[str, Resource] = field(default_factory=dict)

    # Indicadores agregados
    total_resources: int = 0
    scarce_resources: int = 0
    surplus_resources: int = 0

    created_at: str = ""
    updated_at: str = ""

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


# ============================================================
# RESOURCE ENGINE
# ============================================================


class ResourceEngine:

    def __init__(
        self,
        state_file: Optional[Path] = None,
    ) -> None:

        self.state_file = (
            Path(state_file)
            if state_file
            else STATE_FILE
        )

        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.state: Optional[ResourceState] = None

    # ========================================================
    # UTILIDADES
    # ========================================================

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat()

    @staticmethod
    def _safe_float(value: float) -> float:
        return max(0.0, float(value))

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def initialize(
        self,
        world_date: str,
    ) -> ResourceState:

        now = self._now()

        self.state = ResourceState(
            world_date=world_date,
            tick=0,
            total_ticks=0,
            resources={},
            total_resources=0,
            scarce_resources=0,
            surplus_resources=0,
            created_at=now,
            updated_at=now,
        )

        self._save()

        return self.state

    # ========================================================
    # RECURSOS
    # ========================================================

    def create_resource(
        self,
        resource_id: str,
        name: str,
        category: str,
        unit: str,
        reserves: float = 0.0,
        production_capacity: float = 0.0,
        price: float = 0.0,
        renewable: bool = False,
    ) -> Resource:

        self._require_state()

        if resource_id in self.state.resources:
            raise ValueError(
                f"Resource already exists: {resource_id}"
            )

        now = self._now()

        resource = Resource(
            resource_id=resource_id,
            name=name,
            category=category,
            unit=unit,
            reserves=self._safe_float(reserves),
            production_capacity=self._safe_float(
                production_capacity
            ),
            production=0.0,
            consumption=0.0,
            imports=0.0,
            exports=0.0,
            price=self._safe_float(price),
            base_price=self._safe_float(price),
            availability=1.0,
            scarcity=0.0,
            surplus=0.0,
            renewable=bool(renewable),
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.resources[resource_id] = resource

        self._refresh_aggregates()
        self._touch()

        self._save()

        return resource

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_resource(
        self,
        resource_id: str,
    ) -> Resource:

        self._require_state()

        try:
            return self.state.resources[resource_id]
        except KeyError:
            raise KeyError(
                f"Resource not found: {resource_id}"
            )

    def get_all_resources(self) -> List[Resource]:

        self._require_state()

        return list(self.state.resources.values())

    def count(self) -> int:

        self._require_state()

        return len(self.state.resources)

    # ========================================================
    # PRODUÇÃO
    # ========================================================

    def produce(
        self,
        resource_id: str,
        amount: float,
    ) -> Resource:

        resource = self.get_resource(resource_id)

        amount = self._safe_float(amount)

        # Produção limitada pela capacidade.
        if resource.production_capacity > 0:
            amount = min(
                amount,
                resource.production_capacity,
            )

        resource.production = amount

        # Recursos não renováveis reduzem reservas.
        if not resource.renewable:
            resource.reserves = max(
                0.0,
                resource.reserves - amount,
            )

        resource.updated_at = self._now()

        self._recalculate_resource(resource)

        self._refresh_aggregates()
        self._touch()
        self._save()

        return resource

    # ========================================================
    # CONSUMO
    # ========================================================

    def consume(
        self,
        resource_id: str,
        amount: float,
    ) -> Resource:

        resource = self.get_resource(resource_id)

        amount = self._safe_float(amount)

        resource.consumption = amount

        resource.updated_at = self._now()

        self._recalculate_resource(resource)

        self._refresh_aggregates()
        self._touch()
        self._save()

        return resource

    # ========================================================
    # IMPORTAÇÕES
    # ========================================================

    def import_resource(
        self,
        resource_id: str,
        amount: float,
    ) -> Resource:

        resource = self.get_resource(resource_id)

        amount = self._safe_float(amount)

        resource.imports += amount

        resource.updated_at = self._now()

        self._recalculate_resource(resource)

        self._refresh_aggregates()
        self._touch()
        self._save()

        return resource

    # ========================================================
    # EXPORTAÇÕES
    # ========================================================

    def export_resource(
        self,
        resource_id: str,
        amount: float,
    ) -> Resource:

        resource = self.get_resource(resource_id)

        amount = self._safe_float(amount)

        available = (
            resource.reserves
            + resource.production
            + resource.imports
        )

        amount = min(amount, available)

        resource.exports += amount

        resource.updated_at = self._now()

        self._recalculate_resource(resource)

        self._refresh_aggregates()
        self._touch()
        self._save()

        return resource

    # ========================================================
    # PREÇO
    # ========================================================

    def set_price(
        self,
        resource_id: str,
        price: float,
    ) -> Resource:

        resource = self.get_resource(resource_id)

        resource.price = self._safe_float(price)

        if resource.base_price <= 0:
            resource.base_price = resource.price

        resource.updated_at = self._now()

        self._touch()
        self._save()

        return resource

    # ========================================================
    # CÁLCULO DO RECURSO
    # ========================================================

    def _recalculate_resource(
        self,
        resource: Resource,
    ) -> None:

        # Oferta disponível durante o período.
        supply = (
            resource.production
            + resource.imports
        )

        # Exportações retiram disponibilidade.
        net_supply = (
            supply
            - resource.exports
        )

        demand = resource.consumption

        # ----------------------------------------------------
        # DISPONIBILIDADE
        # ----------------------------------------------------

        if demand <= 0:
            availability = 1.0

        else:
            availability = (
                net_supply / demand
            )

        resource.availability = max(
            0.0,
            min(1.0, availability),
        )

        # ----------------------------------------------------
        # ESCASSEZ
        # ----------------------------------------------------

        if demand > net_supply:

            shortage = demand - net_supply

            resource.scarcity = (
                shortage / demand
                if demand > 0
                else 0.0
            )

        else:
            resource.scarcity = 0.0

        # ----------------------------------------------------
        # EXCESSO
        # ----------------------------------------------------

        if net_supply > demand:

            excess = net_supply - demand

            resource.surplus = (
                excess / demand
                if demand > 0
                else excess
            )

        else:
            resource.surplus = 0.0

        # ----------------------------------------------------
        # PREÇO DINÂMICO
        # ----------------------------------------------------
        #
        # O preço não é um mercado completo.
        # É apenas uma primeira relação física:
        #
        # escassez -> preço sobe
        # excesso  -> preço desce
        #
        # O MARKET ENGINE futuramente terá formação de preço
        # muito mais completa.
        # ----------------------------------------------------

        base = resource.base_price

        if base > 0:

            if resource.scarcity > 0:

                price_multiplier = (
                    1.0
                    + resource.scarcity
                )

                resource.price = (
                    base
                    * price_multiplier
                )

            elif resource.surplus > 0:

                price_multiplier = max(
                    0.50,
                    1.0
                    - (
                        resource.surplus
                        * 0.50
                    ),
                )

                resource.price = (
                    base
                    * price_multiplier
                )

            else:

                resource.price = base

    # ========================================================
    # PROCESSAMENTO DE TICK
    # ========================================================

    def process_tick(
        self,
        world_date: str,
    ) -> ResourceState:

        self._require_state()

        self.state.tick += 1
        self.state.total_ticks += 1
        self.state.world_date = world_date

        for resource in self.state.resources.values():

            # Para recursos renováveis,
            # a produção volta a estar disponível.
            if resource.renewable:

                resource.reserves += (
                    resource.production
                )

            # Para o próximo período,
            # produção, consumo e comércio
            # começam novamente a zero.
            resource.production = 0.0
            resource.consumption = 0.0
            resource.imports = 0.0
            resource.exports = 0.0

            resource.updated_at = self._now()

            self._recalculate_resource(resource)

        self._refresh_aggregates()
        self._touch()
        self._save()

        return self.state

    # ========================================================
    # AGREGADOS
    # ========================================================

    def _refresh_aggregates(self) -> None:

        if self.state is None:
            return

        resources = list(
            self.state.resources.values()
        )

        self.state.total_resources = len(
            resources
        )

        self.state.scarce_resources = sum(
            1
            for resource in resources
            if resource.scarcity > 0
        )

        self.state.surplus_resources = sum(
            1
            for resource in resources
            if resource.surplus > 0
        )

    # ========================================================
    # ESTADO
    # ========================================================

    def _touch(self) -> None:

        if self.state is not None:
            self.state.updated_at = self._now()

    def _require_state(self) -> None:

        if self.state is None:
            raise RuntimeError(
                "ResourceEngine is not initialized."
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

        payload = asdict(self.state)

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

    def load(self) -> ResourceState:

        if not self.state_file.exists():

            raise FileNotFoundError(
                f"Resource state file not found: "
                f"{self.state_file}"
            )

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        resources = {}

        for resource_id, resource_data in (
            data.get("resources", {}).items()
        ):

            resources[resource_id] = Resource(
                **resource_data
            )

        data["resources"] = resources

        self.state = ResourceState(
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

    engine = ResourceEngine()

    engine.initialize(
        world_date="2026-09-29"
    )

    oil = engine.create_resource(
        resource_id="OIL",
        name="Petróleo",
        category="ENERGY",
        unit="barrels",
        reserves=1_000_000,
        production_capacity=100_000,
        price=70.0,
        renewable=False,
    )

    water = engine.create_resource(
        resource_id="WATER",
        name="Água",
        category="ESSENTIAL",
        unit="m3",
        reserves=5_000_000,
        production_capacity=500_000,
        price=1.0,
        renewable=True,
    )

    print()
    print("RECURSOS CRIADOS")
    print(
        "Total de recursos:",
        engine.count(),
    )

    # --------------------------------------------------------
    # TESTE PETRÓLEO
    # --------------------------------------------------------

    engine.produce(
        "OIL",
        100_000,
    )

    engine.consume(
        "OIL",
        120_000,
    )

    oil = engine.get_resource("OIL")

    print()
    print("TESTE PETRÓLEO")
    print(
        "Reservas      :",
        f"{oil.reserves:,.2f}",
    )
    print(
        "Produção      :",
        f"{oil.production:,.2f}",
    )
    print(
        "Consumo       :",
        f"{oil.consumption:,.2f}",
    )
    print(
        "Disponibilidade:",
        f"{oil.availability:.2%}",
    )
    print(
        "Escassez      :",
        f"{oil.scarcity:.2%}",
    )
    print(
        "Preço         :",
        f"{oil.price:,.2f}",
    )

    # --------------------------------------------------------
    # TESTE ÁGUA
    # --------------------------------------------------------

    engine.produce(
        "WATER",
        500_000,
    )

    engine.consume(
        "WATER",
        300_000,
    )

    water = engine.get_resource("WATER")

    print()
    print("TESTE ÁGUA")
    print(
        "Reservas      :",
        f"{water.reserves:,.2f}",
    )
    print(
        "Produção      :",
        f"{water.production:,.2f}",
    )
    print(
        "Consumo       :",
        f"{water.consumption:,.2f}",
    )
    print(
        "Disponibilidade:",
        f"{water.availability:.2%}",
    )
    print(
        "Excesso       :",
        f"{water.surplus:.2%}",
    )
    print(
        "Preço         :",
        f"{water.price:,.2f}",
    )

    # --------------------------------------------------------
    # TICK
    # --------------------------------------------------------

    engine.process_tick(
        "2026-10-29"
    )

    print()
    print("APÓS TICK")
    print(
        "Tick:",
        engine.state.tick,
    )
    print(
        "Data:",
        engine.state.world_date,
    )

    print()
    print(
        "RESOURCE ENGINE V01 "
        "TESTE CONCLUIDO"
    )
    print("=" * 60)