from world.events.event_engine import EventEngine
from world.economy.economy_engine import EconomyEngine


WORLD_DATE = "2027-01-01"


def apply_economic_event_impact(economy, event):
    """
    Regra de integração usada apenas neste teste.

    economic_impact representa uma variação percentual
    sobre o consumo da economia.

    Exemplo:
        -0.20 = redução de 20%
        +0.10 = aumento de 10%

    Esta regra pertence à integração e não altera
    nenhum dos dois engines.
    """

    current_consumption = economy.state.consumption

    factor = max(
        0.0,
        1.0 + event.economic_impact,
    )

    new_consumption = current_consumption * factor

    economy.set_consumption(new_consumption)
    economy.calculate_gdp()


def main():

    print("=" * 70)
    print("ATHENA WORLD - TESTE EVENT <-> ECONOMY")
    print("=" * 70)

    # ------------------------------------------------------------
    # 1. Inicializar engines
    # ------------------------------------------------------------

    events = EventEngine()

    economy = EconomyEngine(auto_load=False)

    economy.initialize(
        world_date=WORLD_DATE,
        population=1000,
        employed_population=600,
        nominal_gdp=100000.0,
        price_index=100.0,
        interest_rate=0.05,
    )

    # Economia controlada para o teste
    economy.set_consumption(100000.0)
    economy.calculate_gdp()

    baseline_consumption = economy.state.consumption
    baseline_gdp = economy.state.nominal_gdp

    print()
    print("[ECONOMY]")
    print(f"Consumo inicial : {baseline_consumption:.2f}")
    print(f"GDP inicial     : {baseline_gdp:.2f}")

    assert baseline_consumption == 100000.0
    assert baseline_gdp == 100000.0

    print("ECONOMY OK")

    # ------------------------------------------------------------
    # 2. Inicializar EVENT ENGINE
    # ------------------------------------------------------------

    events.initialize(WORLD_DATE)

    print()
    print("[EVENT ENGINE]")
    print("EVENT ENGINE inicializado.")

    # ------------------------------------------------------------
    # 3. Criar evento económico
    # ------------------------------------------------------------

    event = events.create_external_event(
        name="Crise económica",
        category="ECONOMY",
        description=(
            "Choque económico externo reduz temporariamente "
            "o nível de atividade económica."
        ),
        intensity=0.8,
        duration_ticks=2,
        economic_impact=-0.20,
    )

    print()
    print("[EVENT]")
    print(f"Evento          : {event.name}")
    print(f"Categoria       : {event.category}")
    print(f"Impacto         : {event.economic_impact:.2%}")
    print(f"Duração         : {event.duration_ticks}")
    print(f"Restante        : {event.remaining_ticks}")
    print(f"Estado          : {event.status}")

    assert event.economic_impact == -0.20
    assert event.status == "ACTIVE"

    print("EVENT OK")

    # ------------------------------------------------------------
    # 4. Aplicar impacto do EVENT na ECONOMY
    # ------------------------------------------------------------

    apply_economic_event_impact(
        economy,
        event,
    )

    affected_consumption = economy.state.consumption
    affected_gdp = economy.state.nominal_gdp

    print()
    print("[IMPACTO ECONÓMICO]")
    print(f"Consumo antes   : {baseline_consumption:.2f}")
    print(f"Consumo depois  : {affected_consumption:.2f}")
    print(f"GDP antes       : {baseline_gdp:.2f}")
    print(f"GDP depois      : {affected_gdp:.2f}")

    expected_value = 80000.0

    assert affected_consumption == expected_value
    assert affected_gdp == expected_value

    print("IMPACTO OK")

    # ------------------------------------------------------------
    # 5. Processar tick do EVENT
    # ------------------------------------------------------------

    event_state = events.process_tick(WORLD_DATE)

    print()
    print("[EVENT TICK]")
    print(f"Tick            : {event_state.tick}")
    print(f"Eventos ativos  : {event_state.active_events}")
    print(f"Restante        : {event.remaining_ticks}")
    print(f"Estado evento   : {event.status}")

    assert event_state.tick == 1
    assert event_state.active_events == 1
    assert event.remaining_ticks == 1
    assert event.status == "ACTIVE"

    print("EVENT TICK OK")

    # ------------------------------------------------------------
    # 6. Processar tick da ECONOMY
    # ------------------------------------------------------------

    economy_state = economy.process_tick(WORLD_DATE)

    print()
    print("[ECONOMY TICK]")
    print(f"Tick            : {economy_state.period_number}")
    print(f"Consumo         : {economy_state.consumption:.2f}")
    print(f"GDP nominal     : {economy_state.nominal_gdp:.2f}")
    print(f"GDP real        : {economy_state.real_gdp:.2f}")

    assert economy_state.consumption == expected_value
    assert economy_state.nominal_gdp == expected_value

    print("ECONOMY TICK OK")

    # ------------------------------------------------------------
    # 7. Resultado final
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("EVENT <-> ECONOMY OK")
    print("=" * 70)
    print("O EVENT ENGINE gerou o choque económico.")
    print("A camada de integração aplicou o impacto à ECONOMY.")
    print("A ECONOMY recalculou o GDP.")
    print("Nenhum engine foi alterado.")
    print("=" * 70)


if __name__ == "__main__":
    main()