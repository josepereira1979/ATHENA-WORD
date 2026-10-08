from world.events.event_engine import EventEngine
from world.resources.resource_engine import ResourceEngine


WORLD_DATE = "2027-01-01"


def apply_resource_event_impact(resource, event):
    """
    Regra de integração usada apenas neste teste.

    resource_impact representa uma variação percentual
    sobre a produção do recurso.

    Exemplo:
        -0.25 = redução de 25%
        +0.10 = aumento de 10%

    Esta regra pertence à camada de integração.
    Os engines permanecem inalterados.
    """

    current_production = resource.production

    factor = max(
        0.0,
        1.0 + event.resource_impact,
    )

    resource.production = current_production * factor


def main():

    print("=" * 70)
    print("ATHENA WORLD - TESTE EVENT <-> RESOURCE")
    print("=" * 70)

    # ------------------------------------------------------------
    # 1. Inicializar engines
    # ------------------------------------------------------------

    events = EventEngine()
    resources = ResourceEngine()

    resources.initialize(WORLD_DATE)
    events.initialize(WORLD_DATE)

    print()
    print("[ENGINES]")
    print("EVENT ENGINE inicializado.")
    print("RESOURCE ENGINE inicializado.")

    # ------------------------------------------------------------
    # 2. Criar recurso energético
    # ------------------------------------------------------------

    resource = resources.create_resource(
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
    print("[RESOURCE]")
    print(f"Recurso         : {resource.name}")
    print(f"Reservas        : {resource.reserves:.2f}")
    print(f"Capacidade      : {resource.production_capacity:.2f}")
    print(f"Preço           : {resource.price:.2f}")

    assert resource.reserves == 10000.0
    assert resource.production_capacity == 1000.0

    # ------------------------------------------------------------
    # 3. Produção normal
    # ------------------------------------------------------------

    resources.produce(
        resource_id="ENERGY-001",
        amount=1000.0,
    )

    normal_production = resource.production
    reserves_after_normal = resource.reserves

    print()
    print("[PRODUÇÃO NORMAL]")
    print(f"Produção        : {normal_production:.2f}")
    print(f"Reservas        : {reserves_after_normal:.2f}")

    assert normal_production == 1000.0
    assert reserves_after_normal == 9000.0

    print("RESOURCE OK")

    # ------------------------------------------------------------
    # 4. Criar crise energética
    # ------------------------------------------------------------

    event = events.create_external_event(
        name="Crise energética",
        category="RESOURCE",
        description=(
            "Falha externa reduz temporariamente "
            "a capacidade de produção energética."
        ),
        intensity=0.8,
        duration_ticks=2,
        resource_impact=-0.25,
    )

    print()
    print("[EVENT]")
    print(f"Evento          : {event.name}")
    print(f"Categoria       : {event.category}")
    print(f"Impacto         : {event.resource_impact:.2%}")
    print(f"Duração         : {event.duration_ticks}")
    print(f"Estado          : {event.status}")

    assert event.resource_impact == -0.25
    assert event.status == "ACTIVE"

    print("EVENT OK")

    # ------------------------------------------------------------
    # 5. Aplicar impacto do evento
    # ------------------------------------------------------------

    apply_resource_event_impact(
        resource,
        event,
    )

    affected_production = resource.production

    print()
    print("[IMPACTO NO RECURSO]")
    print(f"Produção antes  : {normal_production:.2f}")
    print(f"Produção depois : {affected_production:.2f}")

    expected_production = 750.0

    assert affected_production == expected_production

    print("IMPACTO OK")

    # ------------------------------------------------------------
    # 6. Consumo do recurso
    # ------------------------------------------------------------

    resources.consume(
        resource_id="ENERGY-001",
        amount=600.0,
    )

    print()
    print("[CONSUMO]")
    print(f"Consumo         : {resource.consumption:.2f}")
    print(f"Reservas        : {resource.reserves:.2f}")

    assert resource.consumption == 600.0

    # ------------------------------------------------------------
    # 7. Processar tick do RESOURCE
    # ------------------------------------------------------------

    resource_state = resources.process_tick(WORLD_DATE)

    print()
    print("[RESOURCE TICK]")
    print(f"Tick            : {resource_state.tick}")
    print(f"Produção        : {resource.production:.2f}")
    print(f"Consumo         : {resource.consumption:.2f}")
    print(f"Disponibilidade : {resource.availability:.2%}")
    print(f"Escassez        : {resource.scarcity:.2%}")

    assert resource_state.tick == 1

    print("RESOURCE TICK OK")

    # ------------------------------------------------------------
    # 8. Processar tick do EVENT
    # ------------------------------------------------------------

    event_state = events.process_tick(WORLD_DATE)

    print()
    print("[EVENT TICK]")
    print(f"Tick            : {event_state.tick}")
    print(f"Eventos ativos  : {event_state.active_events}")
    print(f"Restante        : {event.remaining_ticks}")
    print(f"Estado          : {event.status}")

    assert event_state.tick == 1
    assert event_state.active_events == 1
    assert event.remaining_ticks == 1
    assert event.status == "ACTIVE"

    print("EVENT TICK OK")

    # ------------------------------------------------------------
    # Resultado
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("EVENT <-> RESOURCE OK")
    print("=" * 70)
    print("O EVENT ENGINE gerou a crise energética.")
    print("A integração aplicou o resource_impact.")
    print("A produção foi reduzida de 1000 para 750 MWh.")
    print("O RESOURCE ENGINE processou o recurso normalmente.")
    print("Nenhum engine foi alterado.")
    print("=" * 70)


if __name__ == "__main__":
    main()