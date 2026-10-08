from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD
# INFRASTRUCTURE ENGINE V01
# ============================================================
#
# Responsabilidade:
#   - cidades
#   - habitação
#   - estradas
#   - portos
#   - fábricas
#   - infraestrutura energética
#   - telecomunicações
#   - hospitais
#   - escolas
#   - transportes
#   - capacidade
#   - utilização
#   - manutenção
#   - qualidade
#
# Este motor representa a infraestrutura física do mundo.
#
# NÃO controla diretamente:
#   - agentes
#   - famílias
#   - empresas
#   - economia
#   - recursos
#
# Esses sistemas poderão consumir ou afetar a infraestrutura
# através de interfaces/eventos posteriormente.
#
# ============================================================


ENGINE_NAME = "ATHENA WORLD - INFRASTRUCTURE ENGINE"
ENGINE_VERSION = "V01"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "infrastructure_state.json"


# ============================================================
# INFRAESTRUTURA
# ============================================================


@dataclass
class Infrastructure:
    infrastructure_id: str
    name: str
    category: str
    city_id: str

    # Capacidade física
    capacity: float = 0.0
    utilization: float = 0.0

    # Estado
    condition: float = 1.0
    quality: float = 1.0

    # Manutenção
    maintenance_rate: float = 0.01
    maintenance_cost: float = 0.0

    # Construção
    construction_cost: float = 0.0
    construction_years: float = 0.0

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# CIDADE
# ============================================================


@dataclass
class City:
    city_id: str
    name: str
    country: str

    population: int = 0

    # Indicadores físicos
    housing_capacity: float = 0.0
    road_capacity: float = 0.0
    energy_capacity: float = 0.0
    water_capacity: float = 0.0
    telecom_capacity: float = 0.0
    hospital_capacity: float = 0.0
    school_capacity: float = 0.0
    transport_capacity: float = 0.0

    # Qualidade agregada
    infrastructure_quality: float = 1.0

    # IDs das infraestruturas
    infrastructure_ids: List[str] = field(
        default_factory=list
    )

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# ESTADO DO MOTOR
# ============================================================


@dataclass
class InfrastructureState:
    world_date: str

    tick: int = 0
    total_ticks: int = 0

    cities: Dict[str, City] = field(
        default_factory=dict
    )

    infrastructures: Dict[str, Infrastructure] = field(
        default_factory=dict
    )

    total_cities: int = 0
    total_infrastructure: int = 0

    # Indicadores agregados
    total_population: int = 0

    housing_capacity: float = 0.0
    road_capacity: float = 0.0
    energy_capacity: float = 0.0
    water_capacity: float = 0.0
    telecom_capacity: float = 0.0
    hospital_capacity: float = 0.0
    school_capacity: float = 0.0
    transport_capacity: float = 0.0

    infrastructure_quality: float = 1.0

    created_at: str = ""
    updated_at: str = ""

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


# ============================================================
# INFRASTRUCTURE ENGINE
# ============================================================


class InfrastructureEngine:

    def __init__(
        self,
        state_file: Optional[Path] = None,
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

        self.state: Optional[
            InfrastructureState
        ] = None

    # ========================================================
    # UTILIDADES
    # ========================================================

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat()

    @staticmethod
    def _safe_float(value: float) -> float:
        return max(0.0, float(value))

    @staticmethod
    def _safe_int(value: int) -> int:
        return max(0, int(value))

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def initialize(
        self,
        world_date: str,
    ) -> InfrastructureState:

        now = self._now()

        self.state = InfrastructureState(
            world_date=world_date,
            tick=0,
            total_ticks=0,
            cities={},
            infrastructures={},
            total_cities=0,
            total_infrastructure=0,
            total_population=0,
            housing_capacity=0.0,
            road_capacity=0.0,
            energy_capacity=0.0,
            water_capacity=0.0,
            telecom_capacity=0.0,
            hospital_capacity=0.0,
            school_capacity=0.0,
            transport_capacity=0.0,
            infrastructure_quality=1.0,
            created_at=now,
            updated_at=now,
        )

        self._save()

        return self.state

    # ========================================================
    # CIDADES
    # ========================================================

    def create_city(
        self,
        city_id: str,
        name: str,
        country: str,
        population: int = 0,
    ) -> City:

        self._require_state()

        if city_id in self.state.cities:
            raise ValueError(
                f"City already exists: {city_id}"
            )

        now = self._now()

        city = City(
            city_id=city_id,
            name=name,
            country=country,
            population=self._safe_int(
                population
            ),
            created_at=now,
            updated_at=now,
        )

        self.state.cities[city_id] = city

        self._refresh_aggregates()
        self._touch()
        self._save()

        return city

    def get_city(
        self,
        city_id: str,
    ) -> City:

        self._require_state()

        try:
            return self.state.cities[city_id]
        except KeyError:
            raise KeyError(
                f"City not found: {city_id}"
            )

    def get_all_cities(self) -> List[City]:

        self._require_state()

        return list(
            self.state.cities.values()
        )

    # ========================================================
    # POPULAÇÃO
    # ========================================================

    def set_population(
        self,
        city_id: str,
        population: int,
    ) -> City:

        city = self.get_city(city_id)

        city.population = self._safe_int(
            population
        )

        city.updated_at = self._now()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return city

    def change_population(
        self,
        city_id: str,
        change: int,
    ) -> City:

        city = self.get_city(city_id)

        city.population = max(
            0,
            city.population + int(change),
        )

        city.updated_at = self._now()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return city

    # ========================================================
    # INFRAESTRUTURA
    # ========================================================

    def create_infrastructure(
        self,
        infrastructure_id: str,
        name: str,
        category: str,
        city_id: str,
        capacity: float = 0.0,
        quality: float = 1.0,
        construction_cost: float = 0.0,
        construction_years: float = 0.0,
        maintenance_rate: float = 0.01,
    ) -> Infrastructure:

        self._require_state()

        if (
            infrastructure_id
            in self.state.infrastructures
        ):
            raise ValueError(
                "Infrastructure already exists: "
                f"{infrastructure_id}"
            )

        city = self.get_city(city_id)

        now = self._now()

        infrastructure = Infrastructure(
            infrastructure_id=infrastructure_id,
            name=name,
            category=category,
            city_id=city_id,
            capacity=self._safe_float(
                capacity
            ),
            utilization=0.0,
            condition=max(
                0.0,
                min(1.0, float(quality)),
            ),
            quality=max(
                0.0,
                min(1.0, float(quality)),
            ),
            maintenance_rate=max(
                0.0,
                float(maintenance_rate),
            ),
            maintenance_cost=0.0,
            construction_cost=self._safe_float(
                construction_cost
            ),
            construction_years=self._safe_float(
                construction_years
            ),
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.infrastructures[
            infrastructure_id
        ] = infrastructure

        city.infrastructure_ids.append(
            infrastructure_id
        )

        self._update_city_capacity(city)
        self._refresh_aggregates()
        self._touch()
        self._save()

        return infrastructure

    # ========================================================
    # CONSULTA
    # ========================================================

    def get_infrastructure(
        self,
        infrastructure_id: str,
    ) -> Infrastructure:

        self._require_state()

        try:
            return self.state.infrastructures[
                infrastructure_id
            ]
        except KeyError:
            raise KeyError(
                "Infrastructure not found: "
                f"{infrastructure_id}"
            )

    def get_all_infrastructure(
        self,
    ) -> List[Infrastructure]:

        self._require_state()

        return list(
            self.state.infrastructures.values()
        )

    # ========================================================
    # UTILIZAÇÃO
    # ========================================================

    def set_utilization(
        self,
        infrastructure_id: str,
        utilization: float,
    ) -> Infrastructure:

        infrastructure = (
            self.get_infrastructure(
                infrastructure_id
            )
        )

        infrastructure.utilization = max(
            0.0,
            min(1.0, float(utilization)),
        )

        infrastructure.updated_at = (
            self._now()
        )

        self._touch()
        self._save()

        return infrastructure

    # ========================================================
    # MANUTENÇÃO
    # ========================================================

    def maintain(
        self,
        infrastructure_id: str,
        amount: float = 0.01,
    ) -> Infrastructure:

        infrastructure = (
            self.get_infrastructure(
                infrastructure_id
            )
        )

        amount = max(
            0.0,
            float(amount),
        )

        infrastructure.condition = min(
            1.0,
            infrastructure.condition
            + amount,
        )

        infrastructure.quality = (
            infrastructure.condition
        )

        infrastructure.updated_at = (
            self._now()
        )

        self._touch()
        self._save()

        return infrastructure

    # ========================================================
    # DEGRADAÇÃO
    # ========================================================

    def degrade(
        self,
        infrastructure_id: str,
        amount: Optional[float] = None,
    ) -> Infrastructure:

        infrastructure = (
            self.get_infrastructure(
                infrastructure_id
            )
        )

        if amount is None:

            amount = (
                infrastructure.maintenance_rate
                * max(
                    0.1,
                    infrastructure.utilization,
                )
            )

        amount = max(
            0.0,
            float(amount),
        )

        infrastructure.condition = max(
            0.0,
            infrastructure.condition
            - amount,
        )

        infrastructure.quality = (
            infrastructure.condition
        )

        infrastructure.updated_at = (
            self._now()
        )

        self._touch()
        self._save()

        return infrastructure

    # ========================================================
    # CUSTO DE MANUTENÇÃO
    # ========================================================

    def calculate_maintenance_cost(
        self,
        infrastructure_id: str,
    ) -> float:

        infrastructure = (
            self.get_infrastructure(
                infrastructure_id
            )
        )

        cost = (
            infrastructure.construction_cost
            * infrastructure.maintenance_rate
        )

        infrastructure.maintenance_cost = cost

        self._touch()
        self._save()

        return cost

    # ========================================================
    # CAPACIDADE POR CATEGORIA
    # ========================================================

    def _update_city_capacity(
        self,
        city: City,
    ) -> None:

        city.housing_capacity = 0.0
        city.road_capacity = 0.0
        city.energy_capacity = 0.0
        city.water_capacity = 0.0
        city.telecom_capacity = 0.0
        city.hospital_capacity = 0.0
        city.school_capacity = 0.0
        city.transport_capacity = 0.0

        for infrastructure_id in (
            city.infrastructure_ids
        ):

            infrastructure = (
                self.state.infrastructures.get(
                    infrastructure_id
                )
            )

            if infrastructure is None:
                continue

            capacity = (
                infrastructure.capacity
                * infrastructure.condition
            )

            category = (
                infrastructure.category
                .upper()
            )

            if category == "HOUSING":
                city.housing_capacity += (
                    capacity
                )

            elif category == "ROAD":
                city.road_capacity += (
                    capacity
                )

            elif category == "ENERGY":
                city.energy_capacity += (
                    capacity
                )

            elif category == "WATER":
                city.water_capacity += (
                    capacity
                )

            elif category == "TELECOM":
                city.telecom_capacity += (
                    capacity
                )

            elif category == "HOSPITAL":
                city.hospital_capacity += (
                    capacity
                )

            elif category == "SCHOOL":
                city.school_capacity += (
                    capacity
                )

            elif category == "TRANSPORT":
                city.transport_capacity += (
                    capacity
                )

        city.updated_at = self._now()

    # ========================================================
    # AGREGADOS
    # ========================================================

    def _refresh_aggregates(self) -> None:

        if self.state is None:
            return

        for city in self.state.cities.values():

            self._update_city_capacity(
                city
            )

        self.state.total_cities = len(
            self.state.cities
        )

        self.state.total_infrastructure = len(
            self.state.infrastructures
        )

        self.state.total_population = sum(
            city.population
            for city in self.state.cities.values()
        )

        self.state.housing_capacity = sum(
            city.housing_capacity
            for city in self.state.cities.values()
        )

        self.state.road_capacity = sum(
            city.road_capacity
            for city in self.state.cities.values()
        )

        self.state.energy_capacity = sum(
            city.energy_capacity
            for city in self.state.cities.values()
        )

        self.state.water_capacity = sum(
            city.water_capacity
            for city in self.state.cities.values()
        )

        self.state.telecom_capacity = sum(
            city.telecom_capacity
            for city in self.state.cities.values()
        )

        self.state.hospital_capacity = sum(
            city.hospital_capacity
            for city in self.state.cities.values()
        )

        self.state.school_capacity = sum(
            city.school_capacity
            for city in self.state.cities.values()
        )

        self.state.transport_capacity = sum(
            city.transport_capacity
            for city in self.state.cities.values()
        )

        infrastructures = list(
            self.state.infrastructures.values()
        )

        if infrastructures:

            self.state.infrastructure_quality = (
                sum(
                    item.quality
                    for item in infrastructures
                )
                / len(infrastructures)
            )

        else:

            self.state.infrastructure_quality = 1.0

    # ========================================================
    # TICK
    # ========================================================

    def process_tick(
        self,
        world_date: str,
    ) -> InfrastructureState:

        self._require_state()

        self.state.tick += 1
        self.state.total_ticks += 1
        self.state.world_date = world_date

        for infrastructure in (
            self.state.infrastructures.values()
        ):

            if not infrastructure.active:
                continue

            self.degrade(
                infrastructure.infrastructure_id
            )

        self._refresh_aggregates()
        self._touch()
        self._save()

        return self.state

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    def _touch(self) -> None:

        if self.state is not None:
            self.state.updated_at = self._now()

    def _require_state(self) -> None:

        if self.state is None:
            raise RuntimeError(
                "InfrastructureEngine "
                "is not initialized."
            )

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

    def load(
        self,
    ) -> InfrastructureState:

        if not self.state_file.exists():

            raise FileNotFoundError(
                "Infrastructure state file "
                f"not found: {self.state_file}"
            )

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        cities = {}

        for city_id, city_data in (
            data.get("cities", {}).items()
        ):

            cities[city_id] = City(
                **city_data
            )

        infrastructures = {}

        for infrastructure_id, (
            infrastructure_data
        ) in (
            data.get(
                "infrastructures",
                {},
            ).items()
        ):

            infrastructures[
                infrastructure_id
            ] = Infrastructure(
                **infrastructure_data
            )

        data["cities"] = cities
        data["infrastructures"] = (
            infrastructures
        )

        self.state = InfrastructureState(
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

    engine = InfrastructureEngine()

    engine.initialize(
        world_date="2026-09-29"
    )

    # --------------------------------------------------------
    # CIDADE
    # --------------------------------------------------------

    city = engine.create_city(
        city_id="CITY-001",
        name="Nova Aurora",
        country="ATHENA WORLD",
        population=1000,
    )

    # --------------------------------------------------------
    # INFRAESTRUTURAS
    # --------------------------------------------------------

    engine.create_infrastructure(
        infrastructure_id="INF-HOUSING-001",
        name="Habitação Central",
        category="HOUSING",
        city_id="CITY-001",
        capacity=1200,
        quality=0.95,
        construction_cost=2_000_000,
        maintenance_rate=0.01,
    )

    engine.create_infrastructure(
        infrastructure_id="INF-ROAD-001",
        name="Rede Rodoviária Principal",
        category="ROAD",
        city_id="CITY-001",
        capacity=2000,
        quality=0.90,
        construction_cost=1_000_000,
        maintenance_rate=0.02,
    )

    engine.create_infrastructure(
        infrastructure_id="INF-ENERGY-001",
        name="Central Energética",
        category="ENERGY",
        city_id="CITY-001",
        capacity=5000,
        quality=0.92,
        construction_cost=5_000_000,
        maintenance_rate=0.015,
    )

    engine.create_infrastructure(
        infrastructure_id="INF-HOSPITAL-001",
        name="Hospital Central",
        category="HOSPITAL",
        city_id="CITY-001",
        capacity=150,
        quality=0.88,
        construction_cost=3_000_000,
        maintenance_rate=0.02,
    )

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    print()
    print("CIDADE")
    print(
        "Nome          :",
        city.name,
    )
    print(
        "População     :",
        city.population,
    )

    print()
    print("INFRAESTRUTURA")
    print(
        "Total         :",
        engine.state.total_infrastructure,
    )

    print()
    print("CAPACIDADES")

    print(
        "Habitação     :",
        f"{engine.state.housing_capacity:,.2f}",
    )

    print(
        "Estradas      :",
        f"{engine.state.road_capacity:,.2f}",
    )

    print(
        "Energia       :",
        f"{engine.state.energy_capacity:,.2f}",
    )

    print(
        "Hospital      :",
        f"{engine.state.hospital_capacity:,.2f}",
    )

    print(
        "Qualidade     :",
        f"{engine.state.infrastructure_quality:.2%}",
    )

    # --------------------------------------------------------
    # MANUTENÇÃO / DEGRADAÇÃO
    # --------------------------------------------------------

    road = engine.get_infrastructure(
        "INF-ROAD-001"
    )

    print()
    print("ESTRADA ANTES DO TICK")
    print(
        "Condição      :",
        f"{road.condition:.2%}",
    )

    engine.process_tick(
        "2026-10-29"
    )

    road = engine.get_infrastructure(
        "INF-ROAD-001"
    )

    print()
    print("ESTRADA APÓS 1 TICK")
    print(
        "Condição      :",
        f"{road.condition:.2%}",
    )

    print()
    print(
        "INFRASTRUCTURE ENGINE V01 "
        "TESTE CONCLUIDO"
    )

    print("=" * 60)