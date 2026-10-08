from world.events.event_engine import EventEngine
from world.infrastructure.infrastructure_engine import InfrastructureEngine


WORLD_DATE = "2027-01-01"


def apply_infrastructure_event_impact(infrastructure, event):
    """
    Regra de integração usada apenas neste teste.

    infrastructure_impact representa uma variação absoluta
    da qualidade da infraestrutura.

    Exemplo:
        -0.20 = redução de 20 pontos percentuais
        +0.10 = aumento de 10 pontos percentuais

    A regra pertence à camada de integração.
    Os engines permanecem inalterados.
    """

    for item in infrastructure.state.infrastructures.values():

        item.quality = max(
            0.0,
            min(
                1.0,
                item.quality + event.infrastructure_impact,
            ),
        )


def main():

    print("=" * 70)
    print("ATHENA WORLD - TESTE EVENT <-> INFRASTRUCTURE")
    print("=" * 70)

    # ------------------------------------------------------------
    # 1. Inicializar engines
    # ------------------------------------------------------------

    events = EventEngine()
    infrastructure = InfrastructureEngine()

    events.initialize(WORLD_DATE)
    infrastructure.initialize(WORLD_DATE)

    print()
    print("[ENGINES]")
    print("EVENT ENGINE inicializado.")
    print("INFRASTRUCTURE ENGINE inicializado.")

    # ------------------------------------------------------------
    # 2. Criar cidade
    # ------------------------------------------------------------

    city = infrastructure.create_city(
        city_id="CITY-001",
        name="Nova Aurora",
        country="WORLD",
        population=1000,
    )

    print()
    print("[CITY]")
    print(f"Cidade          : {city.name}")
    print(f"País             : {city.country}")
    print(f"População       : {city.population}")

    assert city.population == 1000
    assert city.country == "WORLD"

    print("CITY OK")

    # ------------------------------------------------------------
    # 3. Criar infraestrutura
    # ------------------------------------------------------------

    infra = infrastructure.create_infrastructure(
        infrastructure_id="INFRA-001",
        city_id="CITY-001",
        name="Central Energética",
        category="ENERGY",
        capacity=1000.0,
        quality=0.95,
    )

    print()
    print("[INFRASTRUCTURE]")
    print(f"Infraestrutura  : {infra.name}")
    print(f"Categoria       : {infra.category}")
    print(f"Capacidade      : {infra.capacity:.2f}")
    print(f"Qualidade       : {infra.quality:.2%}")

    assert infra.capacity == 1000.0
    assert infra.quality == 0.95

    print("INFRASTRUCTURE OK")

    # ------------------------------------------------------------
    # 4. Criar evento de falha de infraestrutura
    # ------------------------------------------------------------

    event = events.create_external_event(
        name="Falha da rede energética",
        category="INFRASTRUCTURE",
        description=(
            "Uma falha externa danifica temporariamente "
            "a infraestrutura energética."
        ),
        intensity=0.8,
        duration_ticks=2,
        infrastructure_impact=-0.20,
    )

    print()
    print("[EVENT]")
    print(f"Evento          : {event.name}")
    print(f"Categoria       : {event.category}")
    print(f"Impacto         : {event.infrastructure_impact:.2f}")
    print(f"Duração         : {event.duration_ticks}")
    print(f"Estado          : {event.status}")

    assert event.infrastructure_impact == -0.20
    assert event.status == "ACTIVE"

    print("EVENT OK")

    # ------------------------------------------------------------
    # 5. Aplicar impacto
    # ------------------------------------------------------------

    quality_before = infra.quality

    apply_infrastructure_event_impact(
        infrastructure,
        event,
    )

    quality_after = infra.quality

    print()
    print("[IMPACTO NA INFRASTRUCTURE]")
    print(f"Qualidade antes : {quality_before:.2%}")
    print(f"Qualidade depois: {quality_after:.2%}")

    expected_quality = 0.75

    assert quality_after == expected_quality

    print("IMPACTO OK")

    # ------------------------------------------------------------
    # 6. Processar tick da infraestrutura
    # ------------------------------------------------------------

    infrastructure_state = infrastructure.process_tick(
        WORLD_DATE
    )

    print()
    print("[INFRASTRUCTURE TICK]")
    print(f"Tick            : {infrastructure_state.tick}")
    print(f"Qualidade       : {infra.quality:.2%}")

    assert infrastructure_state.tick == 1

    print("INFRASTRUCTURE TICK OK")

    # ------------------------------------------------------------
    # 7. Processar tick do evento
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
    print("EVENT <-> INFRASTRUCTURE OK")
    print("=" * 70)
    print("O EVENT ENGINE gerou a falha.")
    print("A integração aplicou o infrastructure_impact.")
    print("A qualidade passou de 95% para 75%.")
    print("O INFRASTRUCTURE ENGINE processou o tick.")
    print("Nenhum engine foi alterado.")
    print("=" * 70)


if __name__ == "__main__":
    main()