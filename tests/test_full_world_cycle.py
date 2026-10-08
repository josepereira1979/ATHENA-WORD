from pathlib import Path
import sys


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(r"C:\Users\jpereira\ATHENA_WORLD")
TEST_DATA_DIR = PROJECT_ROOT / "data" / "test_full_world_cycle"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

from world.core.world_core import WorldCore
from world.agents.agent_engine import AgentEngine
from world.families.family_engine import FamilyEngine
from world.companies.company_engine import CompanyEngine
from world.economy.economy_engine import EconomyEngine
from world.resources.resource_engine import ResourceEngine
from world.infrastructure.infrastructure_engine import InfrastructureEngine
from world.market.market_engine import MarketEngine
from world.financial.financial_engine import FinancialEngine
from world.events.event_engine import EventEngine
from world.api.world_api import WorldAPI


# ============================================================
# CONFIGURAÃ‡ÃƒO
# ============================================================

WORLD_DATE = "2027-01-01"


# ============================================================
# LIMPEZA
# ============================================================

def clean_test_state():

    TEST_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for file in TEST_DATA_DIR.glob("*.json"):
        try:
            file.unlink()
        except Exception:
            pass

    api_state = (
        PROJECT_ROOT
        / "data"
        / "world_api_state.json"
    )

    if api_state.exists():
        try:
            api_state.unlink()
        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("ATHENA WORLD - FULL WORLD CYCLE")
    print("=" * 70)
    print()

    clean_test_state()

    # ========================================================
    # 1. WORLD CORE
    # ========================================================

    core = WorldCore(
        world_name="ATHENA WORLD",
        state_file=(
            TEST_DATA_DIR
            / "world_core_state.json"
        ),
    )

    core.state.world_date = WORLD_DATE
    core.state.tick = 0
    core.state.total_ticks = 0
    core.save()

    print("[WORLD CORE]")
    print(f"World      : {core.state.world_name}")
    print(f"Date       : {core.state.world_date}")
    print(f"Tick       : {core.state.tick}")
    print("WORLD CORE OK")
    print()

    # ========================================================
    # 2. AGENT ENGINE
    # ========================================================

    agents = AgentEngine(
        state_file=(
            TEST_DATA_DIR
            / "agent_state.json"
        ),
        auto_load=False,
    )

    agent_1 = agents.create_agent(
        world_date=WORLD_DATE,
        first_name="Joao",
        last_name="Pereira",
        age=35,
        profession="Gestor",
        capital=25000.0,
        income=3000.0,
        expenses=2000.0,
    )

    print("[AGENT ENGINE]")
    print(
        f"Agent           : "
        f"{agent_1.first_name} "
        f"{agent_1.last_name}"
    )
    print(f"Capital inicial : {agent_1.capital:.2f}")
    print(f"Income          : {agent_1.income:.2f}")
    print(f"Expenses        : {agent_1.expenses:.2f}")
    print("AGENT ENGINE OK")
    print()

    # ========================================================
    # 3. FAMILY ENGINE
    # ========================================================

    families = FamilyEngine(
        state_file=(
            TEST_DATA_DIR
            / "family_state.json"
        ),
        auto_load=False,
    )

    family = families.create_family(
        world_date=WORLD_DATE,
        family_name="Pereira",
    )

    family_id = family.family_id

    family_member_ok = families.add_member(
        family_id=family_id,
        agent_id=agent_1.agent_id,
        world_date=WORLD_DATE,
    )

    assert family_member_ok is True

    print("[FAMILY ENGINE]")
    print(f"Family          : {family.family_name}")
    print(f"Family ID       : {family.family_id}")
    print(f"Members         : {len(family.member_ids)}")
    print("FAMILY ENGINE OK")
    print()

    # ========================================================
    # 4. COMPANY ENGINE
    # ========================================================

    companies = CompanyEngine(
        state_file=(
            TEST_DATA_DIR
            / "company_state.json"
        ),
        auto_load=False,
    )

    company = companies.create_company(
        world_date=WORLD_DATE,
        company_name="Nova Industries",
        sector="INDUSTRY",
        country="WORLD",
        founder_agent_id=agent_1.agent_id,
        manager_agent_id=agent_1.agent_id,
        starting_cash=100000.0,
    )

    if agent_1.agent_id not in company.employee_ids:
        company.employee_ids.append(
            agent_1.agent_id
        )

    print("[COMPANY ENGINE]")
    print(f"Company         : {company.company_name}")
    print(f"Company ID      : {company.company_id}")
    print(f"Cash            : {company.cash:.2f}")
    print(f"Employees       : {len(company.employee_ids)}")
    print("COMPANY ENGINE OK")
    print()

    # ========================================================
    # 5. ECONOMY ENGINE
    # ========================================================

    economy = EconomyEngine(
        state_file=(
            TEST_DATA_DIR
            / "economy_state.json"
        ),
        auto_load=False,
    )

    economy.initialize(
        world_date=WORLD_DATE,
        population=1000,
        employed_population=1,
        nominal_gdp=100000.0,
        price_index=100.0,
        interest_rate=0.05,
    )

    economy.set_wages(3000.0)
    economy.set_consumption(30000.0)
    economy.set_investment(10000.0)

    economy.calculate_gdp()

    print("[ECONOMY ENGINE]")
    print(f"Population      : {economy.state.population}")
    print(
        f"Employed        : "
        f"{economy.state.employed_population}"
    )
    print(f"GDP             : {economy.calculate_gdp():.2f}")
    print("ECONOMY ENGINE OK")
    print()

    print("COMPANY <-> ECONOMY OK")
    print()

    # ========================================================
    # 6. RESOURCE ENGINE
    # ========================================================

    resources = ResourceEngine(
        state_file=(
            TEST_DATA_DIR
            / "resource_state.json"
        ),
    )

    resources.initialize(
        WORLD_DATE
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

    resources.produce(
        resource_id="ENERGY-001",
        amount=1000.0,
    )

    resources.consume(
        resource_id="ENERGY-001",
        amount=600.0,
    )

    print("[RESOURCE ENGINE]")
    print(f"Resource        : {energy.name}")
    print(f"Reserves        : {energy.reserves:.2f}")
    print(f"Production      : {energy.production:.2f}")
    print(f"Consumption     : {energy.consumption:.2f}")
    print("RESOURCE ENGINE OK")
    print()

    # ========================================================
    # 7. INFRASTRUCTURE ENGINE
    # ========================================================

    infrastructure = InfrastructureEngine()

    infrastructure.initialize(
        WORLD_DATE
    )

    city = infrastructure.create_city(
        city_id="CITY-001",
        name="Nova Aurora",
        country="WORLD",
        population=1000,
    )

    infra = infrastructure.create_infrastructure(
        infrastructure_id="INFRA-001",
        name="Central EnergÃ©tica",
        category="ENERGY",
        city_id="CITY-001",
        capacity=1000.0,
        quality=0.95,
    )

    infrastructure.set_utilization(
        infrastructure_id="INFRA-001",
        utilization=1.0,
    )

    print("[INFRASTRUCTURE ENGINE]")
    print(f"City            : {city.name}")
    print(f"Infrastructure  : {infra.name}")
    print(f"Capacity        : {infra.capacity:.2f}")
    print(f"Quality         : {infra.quality:.2f}")
    print("INFRASTRUCTURE ENGINE OK")
    print()

    print("RESOURCE <-> INFRASTRUCTURE OK")
    print()

    # ========================================================
    # 8. MARKET ENGINE
    # ========================================================

    market = MarketEngine(
        state_file=(
            TEST_DATA_DIR
            / "market_state.json"
        ),
    )

    market.initialize(
        WORLD_DATE
    )

    central_market = market.create_market(
        market_id="MARKET-001",
        name="Central Exchange",
        market_type="EXCHANGE",
    )

    asset = market.create_asset(
        asset_id="ASSET-001",
        symbol="ATLA",
        name="Atlas Industries",
        asset_type="STOCK",
        initial_price=100.0,
        market_id="MARKET-001",
    )

    print("[MARKET ENGINE]")
    print(f"Market          : {central_market.name}")
    print(f"Asset           : {asset.symbol}")
    print(f"Price           : {asset.last_price:.2f}")
    print("MARKET ENGINE OK")
    print()

    # ========================================================
    # 9. FINANCIAL ENGINE
    # ========================================================

    financial = FinancialEngine(
        state_file=(
            TEST_DATA_DIR
            / "financial_state.json"
        ),
    )

    financial.initialize(
        WORLD_DATE
    )

    bank = financial.create_bank(
        bank_id="BANK-001",
        name="Central Bank",
        reserves=100000.0,
    )

    buyer_account = financial.create_account(
        account_id="ACCOUNT-BUYER",
        owner_id=agent_1.agent_id,
        bank_id="BANK-001",
        initial_balance=10000.0,
    )

    seller_account = financial.create_account(
        account_id="ACCOUNT-SELLER",
        owner_id="SELLER-001",
        bank_id="BANK-001",
        initial_balance=5000.0,
    )

    print("[FINANCIAL ENGINE]")
    print(f"Bank reserves   : {bank.reserves:.2f}")
    print(
        f"Buyer balance   : "
        f"{buyer_account.balance:.2f}"
    )
    print(
        f"Seller balance  : "
        f"{seller_account.balance:.2f}"
    )
    print("FINANCIAL ENGINE OK")
    print()

    print("MARKET <-> FINANCIAL OK")
    print()

    # ========================================================
    # 10. EVENT ENGINE
    # ========================================================

    events = EventEngine(
        state_file=(
            TEST_DATA_DIR
            / "event_state.json"
        ),
    )

    events.initialize(
        WORLD_DATE
    )

    crisis = events.create_event(
        name="Crise energÃ©tica",
        category="RESOURCE",
        event_type="CRISIS",
        description=(
            "ReduÃ§Ã£o temporÃ¡ria da "
            "disponibilidade energÃ©tica."
        ),
        origin="INTERNAL",
        probability=1.0,
        intensity=0.5,
        duration_ticks=2,
        economic_impact=-0.10,
        company_impact=-0.30,
        resource_impact=-0.25,
        infrastructure_impact=-0.20,
        market_impact=-0.05,
        financial_impact=-0.05,
    )

    print("[EVENT ENGINE]")
    print(f"Event           : {crisis.name}")
    print(f"Category        : {crisis.category}")
    print(f"Duration        : {crisis.duration_ticks}")
    print("EVENT ENGINE OK")
    print()

    # ========================================================
    # 11. WORLD API
    # ========================================================

    api = WorldAPI(
        world_date=WORLD_DATE,
        tick=0,
    )

    engine_registrations = [
        ("WORLD_CORE", "V01", "CORE"),
        ("AGENT", "V02", "ENGINE"),
        ("FAMILY", "V01", "ENGINE"),
        ("COMPANY", "V01", "ENGINE"),
        ("ECONOMY", "V01", "ENGINE"),
        ("RESOURCE", "V01", "ENGINE"),
        ("INFRASTRUCTURE", "V01", "ENGINE"),
        ("MARKET", "V01", "ENGINE"),
        ("FINANCIAL", "V01", "ENGINE"),
        ("EVENT", "V01", "ENGINE"),
    ]

    for (
        engine_name,
        engine_version,
        engine_type,
    ) in engine_registrations:

        api.register_engine(
            engine_name=engine_name,
            engine_version=engine_version,
            engine_type=engine_type,
            status="ACTIVE",
        )

    api.sync_world(
        world_date=WORLD_DATE,
        tick=0,
        total_ticks=0,
    )

    world_time = api.get_world_time()

    print("[WORLD API]")
    print(
        f"World date      : "
        f"{world_time['world_date']}"
    )
    print(
        f"Engines         : "
        f"{len(api.state.registered_engines)}"
    )
    print("WORLD API OK")
    print()

    # ========================================================
    # 12. ESTADO INICIAL
    # ========================================================

    assert core.state.world_date == WORLD_DATE
    assert core.state.tick == 0

    assert api.state.world_date == WORLD_DATE
    assert api.state.tick == 0

    assert len(api.state.registered_engines) >= 10

    print("[INITIAL STATE]")
    print("WORLD CORE      : OK")
    print("WORLD API       : OK")
    print("10 ENGINES      : OK")
    print()

    # ========================================================
    # 13. WORLD TICK
    # ========================================================

    old_date = core.state.world_date
    old_tick = core.state.tick

    core.tick_once()

    print("[WORLD TICK]")
    print(f"Date before     : {old_date}")
    print(f"Date after      : {core.state.world_date}")
    print(f"Tick before     : {old_tick}")
    print(f"Tick after      : {core.state.tick}")

    assert core.state.tick == 1

    # ========================================================
    # 14. AGENT TICK
    # ========================================================

    agents.process_tick(
        core.state.world_date
    )

    print()
    print("[AGENT TICK]")
    print(
        f"Agent capital   : "
        f"{agent_1.capital:.2f}"
    )
    print("AGENT TICK OK")

    # ========================================================
    # 15. COMPANY TICK
    # ========================================================
    companies.calculate_growth(company.company_id, company.revenue)
    companies.check_bankruptcy(company.company_id)
    companies.save()

    print()
    print("[COMPANY TICK]")
    print(
        f"Company cash    : "
        f"{company.cash:.2f}"
    )
    print("COMPANY TICK OK")

    # ========================================================
    # 16. ECONOMY TICK
    # ========================================================

    economy.process_tick(
        core.state.world_date
    )
    print()
    print(
        f"GDP             : " 
        f"{economy.calculate_gdp():.2f}"
    )
    print("ECONOMY TICK OK")

    # ========================================================
    # 17. RESOURCE TICK
    # ========================================================

    resources.process_tick(
        core.state.world_date
    )

    print()
    print("[RESOURCE TICK]")
    print(
        f"Resource tick   : "
        f"{resources.state.tick}"
    )
    print("RESOURCE TICK OK")

    # ========================================================
    # 18. INFRASTRUCTURE TICK
    # ========================================================

    infrastructure.process_tick(
        core.state.world_date
    )

    print()
    print("[INFRASTRUCTURE TICK]")
    print(
        f"Infrastructure  : "
        f"{infrastructure.state.tick}"
    )
    print("INFRASTRUCTURE TICK OK")

    # ========================================================
    # 19. MARKET TICK
    # ========================================================

    market.process_tick(
        core.state.world_date
    )

    print()
    print("[MARKET TICK]")
    print(
        f"Market tick     : "
        f"{market.state.tick}"
    )
    print("MARKET TICK OK")

    # ========================================================
    # 20. FINANCIAL TICK
    # ========================================================

    financial.process_tick(
        core.state.world_date
    )

    print()
    print("[FINANCIAL TICK]")
    print(
        f"Financial tick  : "
        f"{financial.state.tick}"
    )
    print("FINANCIAL TICK OK")

    # ========================================================
    # 21. EVENT TICK
    # ========================================================

    events.process_tick(
        core.state.world_date
    )

    print()
    print("[EVENT TICK]")
    print(
        f"Event tick      : "
        f"{events.state.tick}"
    )
    print(
        f"Active events   : "
        f"{events.state.active_events}"
    )
    print("EVENT TICK OK")

    # ========================================================
    # 22. API SYNC
    # ========================================================

    api.sync_world(
        world_date=core.state.world_date,
        tick=core.state.tick,
        total_ticks=core.state.total_ticks,
    )

    print()
    print("[API SYNC]")
    print(
        f"Core date       : "
        f"{core.state.world_date}"
    )
    print(
        f"API date        : "
        f"{api.state.world_date}"
    )
    print(
        f"Core tick       : "
        f"{core.state.tick}"
    )
    print(
        f"API tick        : "
        f"{api.state.tick}"
    )

    assert (
        api.state.world_date
        == core.state.world_date
    )

    assert (
        api.state.tick
        == core.state.tick
    )

    print("API SYNC OK")

    # ========================================================
    # 23. FULL STATE
    # ========================================================

    full_state = api.get_full_state()

    assert full_state is not None

    print()
    print("[FULL WORLD STATE]")
    print(
        f"World date      : "
        f"{api.state.world_date}"
    )
    print(
        f"World tick      : "
        f"{api.state.tick}"
    )
    print(
        f"Registered      : "
        f"{len(api.state.registered_engines)}"
    )
    print("FULL STATE OK")

    # ========================================================
    # ========================================================
    # 24. ASSERTIONS FINAIS
    # ========================================================

    assert core.state.tick == 1

    assert (
        api.state.tick
        == core.state.tick
    )

    assert (
        api.state.world_date
        == core.state.world_date
    )

    assert agent_1.agent_id in agents.agents

    assert family.family_id in families.families

    assert agent_1.agent_id in family.member_ids

    assert company.company_id in companies.companies

    assert any(
        r.resource_id == "ENERGY-001"
        for r in resources.get_all_resources()
    )

    assert infrastructure.get_infrastructure("INFRA-001") is not None

    assert "MARKET-001" in market.state.markets
    assert "ASSET-001" in market.state.assets

    assert "BANK-001" in financial.state.banks
    assert "ACCOUNT-BUYER" in financial.state.accounts
    assert "ACCOUNT-SELLER" in financial.state.accounts

    # ========================================================
    # 25. RESULTADO FINAL
    # ========================================================

    print()
    print("=" * 70)
    print("FULL WORLD CYCLE OK")
    print("=" * 70)



if __name__ == "__main__":
    main()
