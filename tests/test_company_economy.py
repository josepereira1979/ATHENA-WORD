import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from world.companies.company_engine import CompanyEngine
from world.economy.economy_engine import EconomyEngine


print("=" * 70)
print("ATHENA WORLD - TESTE COMPANY <-> ECONOMY")
print("=" * 70)

WORLD_DATE = "2027-03-01"


# ============================================================
# COMPANY
# ============================================================

companies = CompanyEngine()

company = companies.create_company(
    world_date=WORLD_DATE,
    company_name="Nova Industries",
    sector="INDUSTRY",
    country="WORLD",
    starting_cash=100000.0,
)

print()
print("EMPRESA")
print(f"Company ID : {company.company_id}")
print(f"Nome       : {company.company_name}")


# ============================================================
# TRABALHADORES
# ============================================================

companies.add_employee(
    company_id=company.company_id,
    agent_id="AGENT-001",
)

companies.add_employee(
    company_id=company.company_id,
    agent_id="AGENT-002",
)

company = companies.get_company(company.company_id)

print()
print("TRABALHADORES")
print(f"Empregados : {len(company.employee_ids)}")


# ============================================================
# PRODUTO
# ============================================================

product = companies.create_product(
    company_id=company.company_id,
    name="Produto Industrial",
    category="INDUSTRY",
    unit_cost=100.0,
    selling_price=180.0,
    production_capacity=1000.0,
)

print()
print("PRODUTO")
print(f"Produto ID : {product.product_id}")
print(f"Nome       : {product.name}")


# ============================================================
# PRODUÇÃO
# ============================================================

produced = companies.produce(
    company_id=company.company_id,
    product_id=product.product_id,
    units=500.0,
)

print()
print("PRODUÇÃO")
print(f"Unidades produzidas : {produced}")


# ============================================================
# VENDA
# ============================================================

revenue = companies.sell(
    company_id=company.company_id,
    product_id=product.product_id,
    units=400.0,
)

profit = companies.calculate_profit(
    company.company_id
)

company = companies.get_company(company.company_id)

print()
print("RESULTADOS DA EMPRESA")
print(f"Receita     : {company.revenue:.2f}")
print(f"Custos      : {company.costs:.2f}")
print(f"Lucro       : {profit:.2f}")
print(f"Cash        : {company.cash:.2f}")
print(f"Investimento: {company.investment:.2f}")
print(f"Produção    : {company.total_units_produced:.2f}")


# ============================================================
# ECONOMIA
# ============================================================

economy = EconomyEngine()

state = economy.initialize(
    world_date=WORLD_DATE,
    population=1000,
    working_age_population=700,
    labor_force=650,
    employed_population=600,
    nominal_gdp=0.0,
)

print()
print("ECONOMIA - ESTADO INICIAL")
print(f"População       : {state.population}")
print(f"Força trabalho  : {state.labor_force}")
print(f"Empregados      : {state.employed_population}")
print(f"Desempregados   : {state.unemployed_population}")


# ============================================================
# COMPANY -> ECONOMY
# ============================================================

employed = len(company.employee_ids)

economy.set_employment(
    employed_population=employed,
)

economy.set_wages(
    wages=company.costs * 0.20,
)

economy.set_consumption(
    consumption=company.revenue * 0.50,
)

economy.set_investment(
    investment=company.investment,
)

economy.calculate_gdp()

state = economy.get_state()


# ============================================================
# RESULTADO
# ============================================================

print()
print("=" * 70)
print("COMPANY -> ECONOMY")
print("=" * 70)

print(f"Empregados       : {state.employed_population}")
print(f"Desempregados    : {state.unemployed_population}")
print(f"Salários         : {state.wages:.2f}")
print(f"Rendimento       : {state.household_income:.2f}")
print(f"Consumo          : {state.consumption:.2f}")
print(f"Investimento     : {state.investment:.2f}")
print(f"PIB nominal      : {state.nominal_gdp:.2f}")
print(f"PIB real         : {state.real_gdp:.2f}")


# ============================================================
# VERIFICAÇÕES
# ============================================================

ok_company = (
    len(company.employee_ids) == 2
    and company.revenue > 0
    and company.costs > 0
    and company.profit > 0
)

ok_economy = (
    state.employed_population == 2
    and state.unemployed_population == 648
    and state.wages > 0
    and state.nominal_gdp > 0
)

print()
print("=" * 70)
print("VERIFICAÇÃO")
print("=" * 70)

print(f"COMPANY : {'OK' if ok_company else 'ERRO'}")
print(f"ECONOMY : {'OK' if ok_economy else 'ERRO'}")

if ok_company and ok_economy:
    print()
    print("RESULTADO FINAL: COMPANY <-> ECONOMY OK")
else:
    print()
    print("RESULTADO FINAL: EXISTEM ERROS A ANALISAR")

print("=" * 70)