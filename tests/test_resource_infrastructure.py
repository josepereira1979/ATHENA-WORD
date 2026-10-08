
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from world.resources.resource_engine import ResourceEngine
from world.infrastructure.infrastructure_engine import InfrastructureEngine


print("=" * 70)
print("ATHENA WORLD - TESTE RESOURCE <-> INFRASTRUCTURE")
print("=" * 70)

WORLD_DATE = "2027-04-01"


# ============================================================
# RESOURCE ENGINE
# ============================================================

resources = ResourceEngine()

resources.initialize(
    world_date=WORLD_DATE
)

energy = resources.create_resource(
    resource_id="ENERGY-001",
    name="Energia",
    category="ENERGY",
    unit="MWh",
    reserves=10000.0,
    production_capacity=1000.0,
    price=100.0,
    renewable=False,
)

print()
print("RECURSO")
print(f"Resource ID : {energy.resource_id}")
print(f"Nome        : {energy.name}")
print(f"Reservas    : {energy.reserves:.2f}")
print(f"Capacidade  : {energy.production_capacity:.2f}")
print(f"Preço       : {energy.price:.2f}")
print(f"Disponibilidade : {energy.availability:.2%}")


# ============================================================
# PRODUÇÃO DE ENERGIA
# ============================================================

energy = resources.produce(
    resource_id=energy.resource_id,
    amount=800.0,
)

print()
print("PRODUÇÃO DE RECURSO")
print(f"Produção    : {energy.production:.2f} MWh")
print(f"Reservas    : {energy.reserves:.2f} MWh")


# ============================================================
# CONSUMO DE ENERGIA
# ============================================================

energy = resources.consume(
    resource_id=energy.resource_id,
    amount=600.0,
)

print()
print("CONSUMO DE RECURSO")
print(f"Consumo         : {energy.consumption:.2f} MWh")
print(f"Reservas        : {energy.reserves:.2f} MWh")
print(f"Disponibilidade : {energy.availability:.2%}")
print(f"Escassez        : {energy.scarcity:.2%}")
print(f"Excedente       : {energy.surplus:.2%}")


# ============================================================
# INFRASTRUCTURE ENGINE
# ============================================================

infrastructure = InfrastructureEngine()

infrastructure.initialize(
    world_date=WORLD_DATE
)

city = infrastructure.create_city(
    city_id="CITY-001",
    name="Nova Aurora",
    country="WORLD",
    population=1000,
)

print()
print("CIDADE")
print(f"City ID     : {city.city_id}")
print(f"Nome        : {city.name}")
print(f"População   : {city.population}")


# ============================================================
# INFRAESTRUTURA ENERGÉTICA
# ============================================================

power = infrastructure.create_infrastructure(
    infrastructure_id="POWER-001",
    name="Central Energética",
    category="ENERGY",
    city_id=city.city_id,
    capacity=1000.0,
    quality=0.95,
    construction_cost=500000.0,
    construction_years=2.0,
    maintenance_rate=0.01,
)

print()
print("INFRAESTRUTURA")
print(f"ID          : {power.infrastructure_id}")
print(f"Nome        : {power.name}")
print(f"Categoria   : {power.category}")
print(f"Capacidade  : {power.capacity:.2f}")
print(f"Qualidade   : {power.quality:.2f}")


# ============================================================
# RESOURCE -> INFRASTRUCTURE
# ============================================================

resource_availability = energy.availability

utilization = min(
    resource_availability,
    1.0,
)

power = infrastructure.set_utilization(
    infrastructure_id=power.infrastructure_id,
    utilization=utilization,
)

print()
print("=" * 70)
print("RESOURCE -> INFRASTRUCTURE")
print("=" * 70)

print(f"Disponibilidade recurso : {resource_availability:.2%}")
print(f"Capacidade infra        : {power.capacity:.2f}")
print(f"Utilização infra        : {power.utilization:.2%}")


# ============================================================
# MANUTENÇÃO
# ============================================================

power = infrastructure.maintain(
    infrastructure_id=power.infrastructure_id,
    amount=0.02,
)

print()
print("MANUTENÇÃO")
print(f"Qualidade após manutenção : {power.quality:.4f}")


# ============================================================
# PROCESSAMENTO DO TICK
# ============================================================

resource_state = resources.process_tick(
    world_date="2027-04-02"
)

infra_state = infrastructure.process_tick(
    world_date="2027-04-02"
)

energy = resources.get_resource("ENERGY-001")
power = infrastructure.get_infrastructure("POWER-001")

print()
print("PROCESSAMENTO DO TICK")
print(f"Resource tick : {resource_state.tick}")
print(f"Infra tick    : {infra_state.tick}")
print(f"Reservas      : {energy.reserves:.2f} MWh")
print(f"Disponibilidade: {energy.availability:.2%}")
print(f"Qualidade     : {power.quality:.4f}")


# ============================================================
# VERIFICAÇÕES
# ============================================================

ok_resource = (
    energy is not None
    and energy.reserves > 0
    and energy.availability >= 0
    and energy.reserves >= 0
    and 0.0 <= energy.availability <= 1.0
    and 0.0 <= energy.scarcity <= 1.0
)

ok_infrastructure = (
    power is not None
    and power.capacity > 0
    and 0.0 <= power.utilization <= 1.0
    and power.quality > 0
)

ok_link = (
    resource_availability > 0
    and power.utilization > 0
)


# ============================================================
# RESULTADO
# ============================================================

print()
print("=" * 70)
print("VERIFICAÇÃO")
print("=" * 70)

print(f"RESOURCE        : {'OK' if ok_resource else 'ERRO'}")
print(f"INFRASTRUCTURE  : {'OK' if ok_infrastructure else 'ERRO'}")
print(f"LIGAÇÃO         : {'OK' if ok_link else 'ERRO'}")

if ok_resource and ok_infrastructure and ok_link:
    print()
    print("RESULTADO FINAL: RESOURCE <-> INFRASTRUCTURE OK")
else:
    print()
    print("RESULTADO FINAL: EXISTEM ERROS A ANALISAR")

print("=" * 70)
