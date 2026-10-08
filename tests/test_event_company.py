from world.events.event_engine import EventEngine
from world.companies.company_engine import CompanyEngine


def apply_company_event_impact(company, event):
    """
    Adaptador de integração EVENT -> COMPANY.

    O EVENT ENGINE declara o impacto.
    A camada de integração interpreta esse impacto.
    O COMPANY ENGINE continua independente.
    """

    company.productivity = max(
        0.0,
        company.productivity + event.company_impact,
    )


def main():
    print("=" * 70)
    print("TESTE DE INTEGRACAO: EVENT <-> COMPANY")
    print("=" * 70)

    world_date = "2027-01-01"

    # ============================================================
    # ENGINES
    # ============================================================

    events = EventEngine()
    companies = CompanyEngine(
        auto_load=False
    )

    events.initialize(world_date)

    # ============================================================
    # COMPANY
    # ============================================================

    company = companies.create_company(
        world_date=world_date,
        company_name="Nova Industries",
        sector="INDUSTRY",
        country="WORLD",
        starting_cash=100000.0,
    )

    if company is None:
        raise AssertionError(
            "Falha ao criar a empresa."
        )

    print()
    print("COMPANY")
    print("-" * 70)
    print(
        "Empresa              :",
        company.company_name,
    )
    print(
        "Company ID            :",
        company.company_id,
    )
    print(
        "Produtividade inicial :",
        f"{company.productivity:.2f}",
    )
    print(
        "Estado                :",
        company.status,
    )
    print(
        "Cash                  :",
        f"{company.cash:.2f}",
    )

    # ============================================================
    # EVENT
    # ============================================================

    event = events.create_internal_event(
        name="Falha de produção",
        category="COMPANY",
        description=(
            "Falha interna reduz temporariamente "
            "a capacidade produtiva."
        ),
        intensity=0.8,
        duration_ticks=2,
        company_impact=-0.30,
    )

    if event is None:
        raise AssertionError(
            "Falha ao criar o evento."
        )

    print()
    print("EVENT")
    print("-" * 70)
    print(
        "Evento                :",
        event.name,
    )
    print(
        "Event ID              :",
        event.event_id,
    )
    print(
        "Categoria             :",
        event.category,
    )
    print(
        "Tipo                  :",
        event.event_type,
    )
    print(
        "Intensidade           :",
        f"{event.intensity:.2f}",
    )
    print(
        "Duração               :",
        event.duration_ticks,
    )
    print(
        "Restante              :",
        event.remaining_ticks,
    )
    print(
        "Company impact        :",
        f"{event.company_impact:.2f}",
    )
    print(
        "Estado                :",
        event.status,
    )

    # ============================================================
    # INTEGRACAO EVENT -> COMPANY
    # ============================================================

    productivity_before = company.productivity

    apply_company_event_impact(
        company,
        event,
    )

    productivity_after = company.productivity

    expected_productivity = 0.70

    if abs(
        productivity_after - expected_productivity
    ) > 0.000001:
        raise AssertionError(
            "Produtividade incorreta: "
            f"{productivity_after:.4f} "
            f"(esperado {expected_productivity:.4f})"
        )

    print()
    print("LIGACAO EVENT -> COMPANY")
    print("-" * 70)
    print(
        "Produtividade         :",
        f"{productivity_before:.2f}",
        "->",
        f"{productivity_after:.2f}",
    )
    print(
        "Impacto aplicado      :",
        f"{event.company_impact:.2f}",
    )

    # ============================================================
    # EVENT TICK
    # ============================================================

    events.process_tick(world_date)

    event_after_tick = events.get_event(
        event.event_id
    )

    if event_after_tick is None:
        raise AssertionError(
            "Evento desapareceu após process_tick."
        )

    if event_after_tick.remaining_ticks != 1:
        raise AssertionError(
            "remaining_ticks incorreto após "
            "o primeiro tick: "
            f"{event_after_tick.remaining_ticks}"
        )

    print()
    print("EVENT TICK")
    print("-" * 70)
    print(
        "Tick                  :",
        events.state.tick,
    )
    print(
        "Ticks restantes       :",
        event_after_tick.remaining_ticks,
    )
    print(
        "Estado                :",
        event_after_tick.status,
    )

    # ============================================================
    # COMPANY CONTINUA OPERACIONAL
    # ============================================================

    if company.status != "ACTIVE":
        raise AssertionError(
            "Empresa deixou de estar ACTIVE."
        )

    print()
    print("COMPANY APOS EVENTO")
    print("-" * 70)
    print(
        "Empresa               :",
        company.company_name,
    )
    print(
        "Estado                :",
        company.status,
    )
    print(
        "Produtividade         :",
        f"{company.productivity:.2f}",
    )
    print(
        "Cash                  :",
        f"{company.cash:.2f}",
    )

    # ============================================================
    # RESULTADO
    # ============================================================

    print()
    print("=" * 70)
    print("VERIFICACAO")
    print("=" * 70)

    print("EVENT                : OK")
    print("COMPANY              : OK")
    print("IMPACTO               : OK")
    print("EVENT TICK            : OK")
    print("COMPANY OPERACIONAL   : OK")
    print("LIGACAO               : OK")

    print()
    print("RESULTADO FINAL: EVENT <-> COMPANY OK")
    print("=" * 70)


if __name__ == "__main__":
    main()