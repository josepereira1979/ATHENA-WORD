from __future__ import annotations

import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD - COMPANY ENGINE V01
# ============================================================
#
# Responsabilidade:
# - Empresas
# - Trabalhadores
# - Gestão
# - Produtos
# - Produção
# - Fornecedores
# - Clientes
# - Receitas
# - Custos
# - Lucro / prejuízo
# - Dívida
# - Investimento
# - I&D
# - Competição
# - Crescimento
# - Estado da empresa
# - Falência
#
# IMPORTANTE:
# O COMPANY ENGINE não cria nem controla agentes.
# Trabalha através de agent_id.
#
# Também não conhece empresas reais.
# O mapeamento entre empresa virtual e empresa real
# pertence futuramente ao REALITY BRIDGE ENGINE.
# ============================================================


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "companies_state.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PRODUCT
# ============================================================

@dataclass
class Product:

    product_id: str

    company_id: str

    name: str

    category: str

    unit_cost: float

    selling_price: float

    production_capacity: float

    units_produced: float = 0.0

    units_sold: float = 0.0

    active: bool = True


# ============================================================
# COMPANY
# ============================================================

@dataclass
class Company:

    company_id: str

    company_name: str

    sector: str

    country: str

    founded_world_date: str

    founder_agent_id: Optional[str]

    manager_agent_id: Optional[str]

    employee_ids: List[str] = field(default_factory=list)

    supplier_ids: List[str] = field(default_factory=list)

    customer_ids: List[str] = field(default_factory=list)

    competitor_ids: List[str] = field(default_factory=list)

    product_ids: List[str] = field(default_factory=list)

    revenue: float = 0.0

    costs: float = 0.0

    profit: float = 0.0

    cash: float = 0.0

    debt: float = 0.0

    investment: float = 0.0

    research_development: float = 0.0

    productivity: float = 1.0

    market_share: float = 0.0

    reputation: float = 0.5

    growth_rate: float = 0.0

    total_units_produced: float = 0.0

    total_units_sold: float = 0.0

    status: str = "ACTIVE"

    generation: int = 1

    created_at: str = ""

    updated_at: str = ""


# ============================================================
# COMPANY ENGINE
# ============================================================

class CompanyEngine:

    ENGINE_NAME = "ATHENA WORLD - COMPANY ENGINE"
    ENGINE_VERSION = "V01"

    def __init__(
        self,
        state_file: Path = STATE_FILE,
        auto_load: bool = True,
    ):

        self.state_file = Path(state_file)

        self.companies: Dict[str, Company] = {}

        self.products: Dict[str, Product] = {}

        if auto_load:
            self.load()

    # ========================================================
    # UTILITÁRIOS
    # ========================================================

    @staticmethod
    def _new_id(prefix: str) -> str:

        return (
            f"{prefix}-"
            f"{uuid.uuid4().hex[:12].upper()}"
        )

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:

        return max(
            minimum,
            min(
                maximum,
                float(value),
            ),
        )

    # ========================================================
    # CRIAR EMPRESA
    # ========================================================

    def create_company(
        self,
        world_date: str,
        company_name: Optional[str] = None,
        sector: str = "INDUSTRY",
        country: str = "WORLD",
        founder_agent_id: Optional[str] = None,
        manager_agent_id: Optional[str] = None,
        starting_cash: float = 100000.0,
        generation: int = 1,
    ) -> Company:

        if not company_name:

            company_names = [
                "Atlas Industries",
                "Nova Systems",
                "Orion Manufacturing",
                "Pioneer Technologies",
                "Vertex Energy",
                "Horizon Foods",
                "Apex Logistics",
                "Global Materials",
                "Quantum Systems",
                "Northstar Group",
            ]

            company_name = random.choice(
                company_names
            )

        now = datetime.now().isoformat()

        company = Company(
            company_id=self._new_id("COMPANY"),
            company_name=company_name,
            sector=sector,
            country=country,
            founded_world_date=world_date,
            founder_agent_id=founder_agent_id,
            manager_agent_id=manager_agent_id,
            employee_ids=[],
            supplier_ids=[],
            customer_ids=[],
            competitor_ids=[],
            product_ids=[],
            revenue=0.0,
            costs=0.0,
            profit=0.0,
            cash=float(starting_cash),
            debt=0.0,
            investment=0.0,
            research_development=0.0,
            productivity=1.0,
            market_share=0.0,
            reputation=0.5,
            growth_rate=0.0,
            total_units_produced=0.0,
            total_units_sold=0.0,
            status="ACTIVE",
            generation=int(generation),
            created_at=now,
            updated_at=now,
        )

        self.companies[
            company.company_id
        ] = company

        self.save()

        return company

    # ========================================================
    # PRODUTO
    # ========================================================

    def create_product(
        self,
        company_id: str,
        name: str,
        category: str,
        unit_cost: float,
        selling_price: float,
        production_capacity: float,
    ) -> Optional[Product]:

        company = self.get_company(
            company_id
        )

        if company is None:
            return None

        product = Product(
            product_id=self._new_id("PRODUCT"),
            company_id=company_id,
            name=name,
            category=category,
            unit_cost=max(
                0.0,
                float(unit_cost),
            ),
            selling_price=max(
                0.0,
                float(selling_price),
            ),
            production_capacity=max(
                0.0,
                float(production_capacity),
            ),
        )

        self.products[
            product.product_id
        ] = product

        company.product_ids.append(
            product.product_id
        )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return product

    # ========================================================
    # TRABALHADOR
    # ========================================================

    def add_employee(
        self,
        company_id: str,
        agent_id: str,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        if agent_id not in company.employee_ids:

            company.employee_ids.append(
                agent_id
            )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # REMOVER TRABALHADOR
    # ========================================================

    def remove_employee(
        self,
        company_id: str,
        agent_id: str,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        if agent_id in company.employee_ids:

            company.employee_ids.remove(
                agent_id
            )

        if company.manager_agent_id == agent_id:

            company.manager_agent_id = None

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # FORNECEDOR
    # ========================================================

    def add_supplier(
        self,
        company_id: str,
        supplier_company_id: str,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        if (
            supplier_company_id
            not in company.supplier_ids
        ):

            company.supplier_ids.append(
                supplier_company_id
            )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # CLIENTE
    # ========================================================

    def add_customer(
        self,
        company_id: str,
        customer_company_id: str,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        if (
            customer_company_id
            not in company.customer_ids
        ):

            company.customer_ids.append(
                customer_company_id
            )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # CONCORRENTE
    # ========================================================

    def add_competitor(
        self,
        company_id: str,
        competitor_company_id: str,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        if (
            competitor_company_id
            not in company.competitor_ids
        ):

            company.competitor_ids.append(
                competitor_company_id
            )

        self.save()

        return True

    # ========================================================
    # PRODUÇÃO
    # ========================================================

    def produce(
        self,
        company_id: str,
        product_id: str,
        units: float,
    ) -> float:

        company = self.get_company(
            company_id
        )

        product = self.get_product(
            product_id
        )

        if company is None:
            return 0.0

        if product is None:
            return 0.0

        if product.company_id != company_id:
            return 0.0

        if company.status != "ACTIVE":
            return 0.0

        units = max(
            0.0,
            float(units),
        )

        max_units = (
            product.production_capacity
            * max(
                0.0,
                company.productivity,
            )
        )

        actual_units = min(
            units,
            max_units,
        )

        production_cost = (
            actual_units
            * product.unit_cost
        )

        if production_cost > company.cash:

            affordable_units = (
                company.cash
                / max(
                    product.unit_cost,
                    0.000001,
                )
            )

            actual_units = min(
                actual_units,
                affordable_units,
            )

            production_cost = (
                actual_units
                * product.unit_cost
            )

        company.cash -= production_cost
        company.costs += production_cost

        product.units_produced += actual_units

        company.total_units_produced += (
            actual_units
        )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return actual_units

    # ========================================================
    # VENDA
    # ========================================================

    def sell(
        self,
        company_id: str,
        product_id: str,
        units: float,
    ) -> float:

        company = self.get_company(
            company_id
        )

        product = self.get_product(
            product_id
        )

        if company is None:
            return 0.0

        if product is None:
            return 0.0

        if product.company_id != company_id:
            return 0.0

        if company.status != "ACTIVE":
            return 0.0

        units = max(
            0.0,
            float(units),
        )

        available_units = max(
            0.0,
            product.units_produced
            - product.units_sold,
        )

        actual_units = min(
            units,
            available_units,
        )

        revenue = (
            actual_units
            * product.selling_price
        )

        product.units_sold += actual_units

        company.revenue += revenue
        company.cash += revenue
        company.total_units_sold += actual_units

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return revenue

    # ========================================================
    # INVESTIMENTO
    # ========================================================

    def invest(
        self,
        company_id: str,
        amount: float,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        amount = max(
            0.0,
            float(amount),
        )

        if amount > company.cash:

            return False

        company.cash -= amount
        company.investment += amount

        company.productivity += (
            amount / 1000000.0
        )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # INVESTIGAÇÃO / I&D
    # ========================================================

    def invest_rnd(
        self,
        company_id: str,
        amount: float,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        amount = max(
            0.0,
            float(amount),
        )

        if amount > company.cash:

            return False

        company.cash -= amount

        company.research_development += (
            amount
        )

        company.productivity += (
            amount / 2000000.0
        )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # DÍVIDA
    # ========================================================

    def add_debt(
        self,
        company_id: str,
        amount: float,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        amount = max(
            0.0,
            float(amount),
        )

        company.debt += amount
        company.cash += amount

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # PAGAR DÍVIDA
    # ========================================================

    def repay_debt(
        self,
        company_id: str,
        amount: float,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        amount = max(
            0.0,
            float(amount),
        )

        amount = min(
            amount,
            company.debt,
            company.cash,
        )

        company.debt -= amount
        company.cash -= amount

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # RESULTADO
    # ========================================================

    def calculate_profit(
        self,
        company_id: str,
    ) -> Optional[float]:

        company = self.get_company(
            company_id
        )

        if company is None:
            return None

        company.profit = (
            company.revenue
            - company.costs
        )

        return company.profit

    # ========================================================
    # CUSTO / DESPESA
    # ========================================================

    def add_cost(
        self,
        company_id: str,
        amount: float,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        amount = max(
            0.0,
            float(amount),
        )

        company.costs += amount
        company.cash -= amount

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # REPUTAÇÃO
    # ========================================================

    def change_reputation(
        self,
        company_id: str,
        amount: float,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        company.reputation = self._clamp(
            company.reputation + amount
        )

        company.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return True

    # ========================================================
    # FALÊNCIA
    # ========================================================

    def check_bankruptcy(
        self,
        company_id: str,
    ) -> bool:

        company = self.get_company(
            company_id
        )

        if company is None:
            return False

        if company.status == "BANKRUPT":
            return True

        if (
            company.cash <= 0
            and company.debt > 0
            and company.revenue <= 0
        ):

            company.status = "BANKRUPT"

            company.updated_at = (
                datetime.now().isoformat()
            )

            self.save()

            return True

        return False

    # ========================================================
    # CRESCIMENTO
    # ========================================================

    def calculate_growth(
        self,
        company_id: str,
        previous_revenue: float,
    ) -> Optional[float]:

        company = self.get_company(
            company_id
        )

        if company is None:
            return None

        previous_revenue = float(
            previous_revenue
        )

        if previous_revenue <= 0:

            company.growth_rate = 0.0

        else:

            company.growth_rate = (
                (
                    company.revenue
                    - previous_revenue
                )
                / previous_revenue
            )

        return company.growth_rate

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_company(
        self,
        company_id: str,
    ) -> Optional[Company]:

        return self.companies.get(
            company_id
        )

    def get_product(
        self,
        product_id: str,
    ) -> Optional[Product]:

        return self.products.get(
            product_id
        )

    def get_all_companies(
        self,
    ) -> List[Company]:

        return list(
            self.companies.values()
        )

    def get_all_products(
        self,
    ) -> List[Product]:

        return list(
            self.products.values()
        )

    def count(self) -> int:

        return len(
            self.companies
        )

    def active_count(self) -> int:

        return sum(
            1
            for company
            in self.companies.values()
            if company.status == "ACTIVE"
        )

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    def save(self) -> None:

        payload = {
            "engine_name": self.ENGINE_NAME,
            "engine_version": self.ENGINE_VERSION,
            "updated_at": datetime.now().isoformat(),
            "companies": [
                asdict(company)
                for company
                in self.companies.values()
            ],
            "products": [
                asdict(product)
                for product
                in self.products.values()
            ],
        }

        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

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

    def load(self) -> None:

        if not self.state_file.exists():
            return

        try:

            with self.state_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                payload = json.load(file)

            self.companies = {}
            self.products = {}

            for data in payload.get(
                "companies",
                [],
            ):

                company = Company(
                    **data
                )

                self.companies[
                    company.company_id
                ] = company

            for data in payload.get(
                "products",
                [],
            ):

                product = Product(
                    **data
                )

                self.products[
                    product.product_id
                ] = product

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):

            self.companies = {}
            self.products = {}

    # ========================================================
    # RESET
    # ========================================================

    def reset(self) -> None:

        self.companies = {}
        self.products = {}

        if self.state_file.exists():

            self.state_file.unlink()


# ============================================================
# TESTE DIRECTO
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("ATHENA WORLD - COMPANY ENGINE")
    print("=" * 70)

    engine = CompanyEngine()

    # Teste limpo.
    engine.reset()

    world_date = "2026-11-03"

    # --------------------------------------------------------
    # EMPRESA
    # --------------------------------------------------------

    company = engine.create_company(
        world_date=world_date,
        company_name="Atlas Industries",
        sector="MANUFACTURING",
        country="WORLD",
        founder_agent_id="AGENT-TEST-001",
        manager_agent_id="AGENT-TEST-001",
        starting_cash=100000.0,
    )

    print(
        f"Company ID     : "
        f"{company.company_id}"
    )

    print(
        f"Company Name   : "
        f"{company.company_name}"
    )

    print(
        f"Sector         : "
        f"{company.sector}"
    )

    print(
        f"Cash inicial   : "
        f"{company.cash:.2f}"
    )

    # --------------------------------------------------------
    # TRABALHADORES
    # --------------------------------------------------------

    engine.add_employee(
        company_id=company.company_id,
        agent_id="AGENT-TEST-001",
    )

    engine.add_employee(
        company_id=company.company_id,
        agent_id="AGENT-TEST-002",
    )

    # --------------------------------------------------------
    # PRODUTO
    # --------------------------------------------------------

    product = engine.create_product(
        company_id=company.company_id,
        name="Industrial Component",
        category="COMPONENTS",
        unit_cost=100.0,
        selling_price=180.0,
        production_capacity=1000.0,
    )

    # --------------------------------------------------------
    # PRODUÇÃO
    # --------------------------------------------------------

    produced = engine.produce(
        company_id=company.company_id,
        product_id=product.product_id,
        units=500.0,
    )

    # --------------------------------------------------------
    # VENDA
    # --------------------------------------------------------

    revenue = engine.sell(
        company_id=company.company_id,
        product_id=product.product_id,
        units=400.0,
    )

    # --------------------------------------------------------
    # I&D
    # --------------------------------------------------------

    engine.invest_rnd(
        company_id=company.company_id,
        amount=5000.0,
    )

    # --------------------------------------------------------
    # INVESTIMENTO
    # --------------------------------------------------------

    engine.invest(
        company_id=company.company_id,
        amount=10000.0,
    )

    # --------------------------------------------------------
    # CÁLCULO DO RESULTADO
    # --------------------------------------------------------

    profit = engine.calculate_profit(
        company.company_id
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    company = engine.get_company(
        company.company_id
    )

    print()
    print("=" * 70)
    print("RESULTADO DO TESTE")
    print("-" * 70)

    print(
        f"Empresa        : "
        f"{company.company_name}"
    )

    print(
        f"Trabalhadores   : "
        f"{len(company.employee_ids)}"
    )

    print(
        f"Produtos        : "
        f"{len(company.product_ids)}"
    )

    print(
        f"Produção        : "
        f"{produced:.2f} unidades"
    )

    print(
        f"Vendas          : "
        f"400.00 unidades"
    )

    print(
        f"Receita         : "
        f"{revenue:.2f}"
    )

    print(
        f"Custos          : "
        f"{company.costs:.2f}"
    )

    print(
        f"Lucro           : "
        f"{profit:.2f}"
    )

    print(
        f"Cash final      : "
        f"{company.cash:.2f}"
    )

    print(
        f"Investimento    : "
        f"{company.investment:.2f}"
    )

    print(
        f"I&D             : "
        f"{company.research_development:.2f}"
    )

    print(
        f"Produtividade   : "
        f"{company.productivity:.4f}"
    )

    print(
        f"Reputação       : "
        f"{company.reputation:.2f}"
    )

    print(
        f"Estado          : "
        f"{company.status}"
    )

    print("=" * 70)

    print()
    print(
        "ATHENA WORLD - COMPANY ENGINE V01 "
        "carregado com sucesso."
    )

    print("=" * 70)