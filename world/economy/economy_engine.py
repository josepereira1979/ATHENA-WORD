
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================
# ATHENA WORLD - ECONOMY ENGINE V01
# ============================================================
#
# Motor macroeconómico do ATHENA WORLD.
#
# Responsabilidades:
# - População economicamente activa
# - Emprego / desemprego
# - Salários
# - Rendimento das famílias
# - Consumo
# - Poupança
# - Investimento
# - Despesa pública
# - Comércio externo
# - PIB nominal
# - PIB real
# - Crescimento económico
# - Inflação
# - Produtividade
# - Taxa de juro
# - Dívida
# - Ciclo económico
#
# PRINCÍPIO FUNDAMENTAL:
#
# O primeiro período é BASELINE.
# Não existe crescimento económico calculável antes
# de existir um período anterior comparável.
#
# A partir do segundo período:
#
# crescimento =
# (PIB real actual - PIB real anterior)
# / PIB real anterior
#
# O mesmo princípio é utilizado para a inflação.
#
# O motor não cria agentes nem empresas.
# Trabalha através de agregados económicos.
#
# V01 permanece V01 durante correcções estruturais.
# ============================================================


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

STATE_FILE = DATA_DIR / "economy_state.json"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ESTADO ECONÓMICO
# ============================================================

@dataclass
class EconomicState:

    # --------------------------------------------------------
    # TEMPO
    # --------------------------------------------------------

    world_date: str

    period_number: int

    baseline_established: bool

    # --------------------------------------------------------
    # POPULAÇÃO
    # --------------------------------------------------------

    population: int

    working_age_population: int

    labor_force: int

    employed_population: int

    unemployed_population: int

    employment_rate: float

    unemployment_rate: float

    # --------------------------------------------------------
    # PRODUÇÃO / PIB
    # --------------------------------------------------------

    nominal_gdp: float

    real_gdp: float

    previous_real_gdp: float

    gdp_growth_rate: float

    # --------------------------------------------------------
    # COMPONENTES DO PIB
    # --------------------------------------------------------

    consumption: float

    investment: float

    government_spending: float

    exports: float

    imports: float

    # --------------------------------------------------------
    # FAMÍLIAS
    # --------------------------------------------------------

    wages: float

    household_income: float

    household_savings: float

    # --------------------------------------------------------
    # PRODUTIVIDADE
    # --------------------------------------------------------

    productivity: float

    # --------------------------------------------------------
    # PREÇOS
    # --------------------------------------------------------

    price_index: float

    previous_price_index: float

    inflation_rate: float

    # --------------------------------------------------------
    # FINANÇAS
    # --------------------------------------------------------

    interest_rate: float

    debt: float

    # --------------------------------------------------------
    # CICLO
    # --------------------------------------------------------

    recession: bool

    economic_cycle: str

    # --------------------------------------------------------
    # PERSISTÊNCIA
    # --------------------------------------------------------

    created_at: str

    updated_at: str


# ============================================================
# ECONOMY ENGINE
# ============================================================

class EconomyEngine:

    ENGINE_NAME = (
        "ATHENA WORLD - ECONOMY ENGINE"
    )

    ENGINE_VERSION = "V01"

    def __init__(
        self,
        state_file: Path = STATE_FILE,
        auto_load: bool = True,
    ):

        self.state_file = Path(
            state_file
        )

        self.state: Optional[
            EconomicState
        ] = None

        if auto_load:

            self.load()

    # ========================================================
    # INICIALIZAR ECONOMIA
    # ========================================================

    def initialize(
        self,
        world_date: str,
        population: int = 1000,
        working_age_population: Optional[int] = None,
        employed_population: int = 600,
        labor_force: Optional[int] = None,
        nominal_gdp: float = 0.0,
        price_index: float = 100.0,
        interest_rate: float = 0.05,
    ) -> EconomicState:

        # ----------------------------------------------------
        # POPULAÇÃO
        # ----------------------------------------------------

        population = max(
            0,
            int(population),
        )

        # ----------------------------------------------------
        # POPULAÇÃO EM IDADE ACTIVA
        # ----------------------------------------------------

        if working_age_population is None:

            working_age_population = int(
                population * 0.65
            )

        working_age_population = max(
            0,
            min(
                int(
                    working_age_population
                ),
                population,
            ),
        )

        # ----------------------------------------------------
        # FORÇA DE TRABALHO
        # ----------------------------------------------------

        if labor_force is None:

            labor_force = (
                working_age_population
            )

        labor_force = max(
            0,
            min(
                int(labor_force),
                working_age_population,
            ),
        )

        # ----------------------------------------------------
        # EMPREGADOS
        # ----------------------------------------------------

        employed_population = max(
            0,
            min(
                int(employed_population),
                labor_force,
            ),
        )

        # ----------------------------------------------------
        # DESEMPREGADOS
        # ----------------------------------------------------

        unemployed_population = (
            labor_force
            - employed_population
        )

        # ----------------------------------------------------
        # TAXA DE EMPREGO
        #
        # Empregados / população em idade activa
        # ----------------------------------------------------

        if working_age_population > 0:

            employment_rate = (
                employed_population
                / working_age_population
            )

        else:

            employment_rate = 0.0

        # ----------------------------------------------------
        # TAXA DE DESEMPREGO
        #
        # Desempregados / força de trabalho
        # ----------------------------------------------------

        if labor_force > 0:

            unemployment_rate = (
                unemployed_population
                / labor_force
            )

        else:

            unemployment_rate = 0.0

        # ----------------------------------------------------
        # VALORES BASE
        # ----------------------------------------------------

        nominal_gdp = max(
            0.0,
            float(nominal_gdp),
        )

        price_index = max(
            0.01,
            float(price_index),
        )

        real_gdp = (
            nominal_gdp
            / (price_index / 100.0)
        )

        now = datetime.now().isoformat()

        # ----------------------------------------------------
        # ESTADO INICIAL
        # ----------------------------------------------------
        #
        # IMPORTANTE:
        #
        # Este período NÃO possui crescimento.
        #
        # O PIB aqui calculado passa a ser a referência
        # para o período seguinte.
        # ----------------------------------------------------

        self.state = EconomicState(

            world_date=world_date,

            period_number=1,

            baseline_established=True,

            population=population,

            working_age_population=(
                working_age_population
            ),

            labor_force=labor_force,

            employed_population=(
                employed_population
            ),

            unemployed_population=(
                unemployed_population
            ),

            employment_rate=(
                employment_rate
            ),

            unemployment_rate=(
                unemployment_rate
            ),

            nominal_gdp=nominal_gdp,

            real_gdp=real_gdp,

            previous_real_gdp=real_gdp,

            gdp_growth_rate=0.0,

            consumption=0.0,

            investment=0.0,

            government_spending=0.0,

            exports=0.0,

            imports=0.0,

            wages=0.0,

            household_income=0.0,

            household_savings=0.0,

            productivity=1.0,

            price_index=price_index,

            previous_price_index=price_index,

            inflation_rate=0.0,

            interest_rate=max(
                0.0,
                float(interest_rate),
            ),

            debt=0.0,

            recession=False,

            economic_cycle="BASELINE",

            created_at=now,

            updated_at=now,
        )

        self.save()

        return self.state

    # ========================================================
    # EMPREGO
    # ========================================================

    def set_employment(
        self,
        employed_population: int,
        labor_force: Optional[int] = None,
    ) -> bool:

        if self.state is None:

            return False

        if labor_force is None:

            labor_force = (
                self.state.labor_force
            )

        labor_force = max(
            0,
            min(
                int(labor_force),
                self.state.working_age_population,
            ),
        )

        employed_population = max(
            0,
            min(
                int(employed_population),
                labor_force,
            ),
        )

        unemployed_population = (
            labor_force
            - employed_population
        )

        self.state.labor_force = (
            labor_force
        )

        self.state.employed_population = (
            employed_population
        )

        self.state.unemployed_population = (
            unemployed_population
        )

        if (
            self.state.working_age_population
            > 0
        ):

            self.state.employment_rate = (
                employed_population
                / self.state.working_age_population
            )

        else:

            self.state.employment_rate = 0.0

        if labor_force > 0:

            self.state.unemployment_rate = (
                unemployed_population
                / labor_force
            )

        else:

            self.state.unemployment_rate = 0.0

        self._touch()

        return True

    # ========================================================
    # SALÁRIOS
    # ========================================================

    def set_wages(
        self,
        wages: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.wages = max(
            0.0,
            float(wages),
        )

        self.state.household_income = (
            self.state.wages
        )

        self._touch()

        return True

    # ========================================================
    # CONSUMO
    # ========================================================

    def set_consumption(
        self,
        consumption: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.consumption = max(
            0.0,
            float(consumption),
        )

        self._touch()

        return True

    # ========================================================
    # POUPANÇA
    # ========================================================

    def calculate_savings(self) -> float:

        if self.state is None:

            return 0.0

        savings = (
            self.state.household_income
            - self.state.consumption
        )

        self.state.household_savings = max(
            0.0,
            savings,
        )

        return (
            self.state.household_savings
        )

    # ========================================================
    # INVESTIMENTO
    # ========================================================

    def set_investment(
        self,
        investment: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.investment = max(
            0.0,
            float(investment),
        )

        self._touch()

        return True

    # ========================================================
    # DESPESA PÚBLICA
    # ========================================================

    def set_government_spending(
        self,
        spending: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.government_spending = max(
            0.0,
            float(spending),
        )

        self._touch()

        return True

    # ========================================================
    # COMÉRCIO EXTERNO
    # ========================================================

    def set_trade(
        self,
        exports: float,
        imports: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.exports = max(
            0.0,
            float(exports),
        )

        self.state.imports = max(
            0.0,
            float(imports),
        )

        self._touch()

        return True

    # ========================================================
    # PRODUTIVIDADE
    # ========================================================

    def set_productivity(
        self,
        productivity: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.productivity = max(
            0.0,
            float(productivity),
        )

        self._touch()

        return True

    # ========================================================
    # PIB
    # ========================================================

    def calculate_gdp(self) -> float:

        if self.state is None:

            return 0.0

        # ----------------------------------------------------
        # PIB = C + I + G + X - M
        # ----------------------------------------------------

        gdp = (
            self.state.consumption
            + self.state.investment
            + self.state.government_spending
            + self.state.exports
            - self.state.imports
        )

        self.state.nominal_gdp = max(
            0.0,
            gdp,
        )

        if self.state.price_index > 0:

            self.state.real_gdp = (
                self.state.nominal_gdp
                / (
                    self.state.price_index
                    / 100.0
                )
            )

        else:

            self.state.real_gdp = (
                self.state.nominal_gdp
            )

        return (
            self.state.nominal_gdp
        )

    # ========================================================
    # CRESCIMENTO
    # ========================================================

    def calculate_growth(
        self,
        previous_real_gdp: Optional[float] = None,
    ) -> float:

        if self.state is None:

            return 0.0

        if previous_real_gdp is None:

            previous_real_gdp = (
                self.state.previous_real_gdp
            )

        previous_real_gdp = float(
            previous_real_gdp
        )

        current_real_gdp = (
            self.state.real_gdp
        )

        if previous_real_gdp <= 0:

            growth = 0.0

        else:

            growth = (
                current_real_gdp
                - previous_real_gdp
            ) / previous_real_gdp

        self.state.gdp_growth_rate = (
            growth
        )

        return growth

    # ========================================================
    # INFLAÇÃO
    # ========================================================

    def update_price_index(
        self,
        new_price_index: float,
    ) -> float:

        if self.state is None:

            return 0.0

        previous_index = (
            self.state.price_index
        )

        new_price_index = max(
            0.01,
            float(new_price_index),
        )

        self.state.previous_price_index = (
            previous_index
        )

        if previous_index > 0:

            inflation = (
                new_price_index
                - previous_index
            ) / previous_index

        else:

            inflation = 0.0

        self.state.price_index = (
            new_price_index
        )

        self.state.inflation_rate = (
            inflation
        )

        self._touch()

        return inflation

    # ========================================================
    # APLICAR INFLAÇÃO
    # ========================================================

    def apply_inflation(
        self,
        inflation_rate: float,
    ) -> float:

        if self.state is None:

            return 0.0

        inflation_rate = float(
            inflation_rate
        )

        old_index = (
            self.state.price_index
        )

        new_index = (
            old_index
            * (1.0 + inflation_rate)
        )

        return self.update_price_index(
            new_index
        )

    # ========================================================
    # TAXA DE JURO
    # ========================================================

    def set_interest_rate(
        self,
        interest_rate: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.interest_rate = max(
            0.0,
            float(interest_rate),
        )

        self._touch()

        return True

    # ========================================================
    # DÍVIDA
    # ========================================================

    def set_debt(
        self,
        debt: float,
    ) -> bool:

        if self.state is None:

            return False

        self.state.debt = max(
            0.0,
            float(debt),
        )

        self._touch()

        return True

    # ========================================================
    # CICLO ECONÓMICO
    # ========================================================

    def determine_cycle(self) -> str:

        if self.state is None:

            return "UNKNOWN"

        # ----------------------------------------------------
        # O primeiro período é sempre BASELINE.
        # ----------------------------------------------------

        if self.state.period_number <= 1:

            self.state.economic_cycle = (
                "BASELINE"
            )

            self.state.recession = False

            return "BASELINE"

        growth = (
            self.state.gdp_growth_rate
        )

        unemployment = (
            self.state.unemployment_rate
        )

        inflation = (
            self.state.inflation_rate
        )

        # ----------------------------------------------------
        # RECESSÃO
        # ----------------------------------------------------

        if growth < -0.02:

            cycle = "RECESSION"

        # ----------------------------------------------------
        # CONTRACÇÃO
        # ----------------------------------------------------

        elif growth < 0.0:

            cycle = "CONTRACTION"

        # ----------------------------------------------------
        # EXPANSÃO
        # ----------------------------------------------------

        elif growth > 0.02:

            cycle = "EXPANSION"

        # ----------------------------------------------------
        # ESTAGNAÇÃO
        # ----------------------------------------------------

        elif growth <= 0.005:

            cycle = "STAGNATION"

        # ----------------------------------------------------
        # NORMAL
        # ----------------------------------------------------

        else:

            cycle = "NORMAL"

        # ----------------------------------------------------
        # PRESSÃO INFLACIONISTA
        # ----------------------------------------------------

        if (
            inflation > 0.05
            and growth >= 0.0
        ):

            cycle = (
                "INFLATIONARY_PRESSURE"
            )

        # ----------------------------------------------------
        # RECESSÃO PROFUNDA
        # ----------------------------------------------------

        if (
            unemployment > 0.10
            and growth < -0.02
        ):

            cycle = "DEEP_RECESSION"

        self.state.economic_cycle = (
            cycle
        )

        self.state.recession = (
            cycle
            in (
                "RECESSION",
                "DEEP_RECESSION",
            )
        )

        return cycle

    # ========================================================
    # PROCESSAR NOVO PERÍODO
    # ========================================================

    def process_tick(
        self,
        world_date: str,
    ) -> Optional[EconomicState]:

        if self.state is None:

            return None

        # ----------------------------------------------------
        # O PIB do período anterior é guardado ANTES de
        # calcular o novo PIB.
        # ----------------------------------------------------

        previous_real_gdp = (
            self.state.real_gdp
        )

        previous_price_index = (
            self.state.price_index
        )

        # ----------------------------------------------------
        # NOVA DATA
        # ----------------------------------------------------

        self.state.world_date = (
            world_date
        )

        # ----------------------------------------------------
        # NOVO PERÍODO
        # ----------------------------------------------------

        self.state.period_number += 1

        # ----------------------------------------------------
        # POUPANÇA
        # ----------------------------------------------------

        self.calculate_savings()

        # ----------------------------------------------------
        # NOVO PIB
        # ----------------------------------------------------

        self.calculate_gdp()

        # ----------------------------------------------------
        # CRESCIMENTO
        # ----------------------------------------------------

        self.state.previous_real_gdp = (
            previous_real_gdp
        )

        self.calculate_growth(
            previous_real_gdp
        )

        # ----------------------------------------------------
        # INFLAÇÃO
        #
        # A inflação só será calculada quando o índice de
        # preços tiver efectivamente mudado.
        # ----------------------------------------------------

        self.state.previous_price_index = (
            previous_price_index
        )

        if previous_price_index > 0:

            self.state.inflation_rate = (
                self.state.price_index
                - previous_price_index
            ) / previous_price_index

        else:

            self.state.inflation_rate = 0.0

        # ----------------------------------------------------
        # CICLO
        # ----------------------------------------------------

        self.determine_cycle()

        self.state.updated_at = (
            datetime.now().isoformat()
        )

        self.save()

        return self.state

    # ========================================================
    # PROCESSAR PRIMEIRO PERÍODO
    # ========================================================

    def establish_baseline(
        self,
        world_date: str,
    ) -> Optional[EconomicState]:

        if self.state is None:

            return None

        # ----------------------------------------------------
        # Recalcula os agregados sem considerar crescimento.
        # ----------------------------------------------------

        self.state.world_date = (
            world_date
        )

        self.calculate_savings()

        self.calculate_gdp()

        self.state.previous_real_gdp = (
            self.state.real_gdp
        )

        self.state.gdp_growth_rate = (
            0.0
        )

        self.state.previous_price_index = (
            self.state.price_index
        )

        self.state.inflation_rate = (
            0.0
        )

        self.state.period_number = 1

        self.state.baseline_established = (
            True
        )

        self.state.economic_cycle = (
            "BASELINE"
        )

        self.state.recession = False

        self._touch()

        return self.state

    # ========================================================
    # ESTADO
    # ========================================================

    def get_state(
        self,
    ) -> Optional[EconomicState]:

        return self.state

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    def save(self) -> None:

        if self.state is None:

            return

        payload = {

            "engine_name": (
                self.ENGINE_NAME
            ),

            "engine_version": (
                self.ENGINE_VERSION
            ),

            "updated_at": (
                datetime.now().isoformat()
            ),

            "state": asdict(
                self.state
            ),
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

    # ========================================================
    # CARREGAR
    # ========================================================

    def load(self) -> None:

        if not self.state_file.exists():

            return

        try:

            with self.state_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                payload = json.load(
                    file
                )

            data = payload.get(
                "state"
            )

            if not data:

                return

            self.state = EconomicState(
                **data
            )

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):

            self.state = None

    # ========================================================
    # RESET
    # ========================================================

    def reset(self) -> None:

        self.state = None

        if self.state_file.exists():

            self.state_file.unlink()

    # ========================================================
    # UTILITÁRIO
    # ========================================================

    def _touch(self) -> None:

        if self.state is None:

            return

        self.state.updated_at = (
            datetime.now().isoformat()
        )

        self.save()


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "ATHENA WORLD - ECONOMY ENGINE"
    )

    print("=" * 70)

    engine = EconomyEngine()

    # --------------------------------------------------------
    # LIMPAR TESTE ANTERIOR
    # --------------------------------------------------------

    engine.reset()

    # --------------------------------------------------------
    # CRIAR ECONOMIA
    # --------------------------------------------------------

    state = engine.initialize(

        world_date="2026-11-03",

        population=1000,

        working_age_population=650,

        labor_force=650,

        employed_population=600,

        nominal_gdp=0.0,

        price_index=100.0,

        interest_rate=0.05,
    )

    # --------------------------------------------------------
    # DADOS DO PRIMEIRO PERÍODO
    # --------------------------------------------------------

    engine.set_wages(
        500000.0
    )

    engine.set_consumption(
        350000.0
    )

    engine.set_investment(
        100000.0
    )

    engine.set_government_spending(
        50000.0
    )

    engine.set_trade(
        exports=80000.0,
        imports=60000.0,
    )

    engine.set_productivity(
        1.05
    )

    # --------------------------------------------------------
    # ESTABELECER BASELINE
    # --------------------------------------------------------

    engine.establish_baseline(
        "2026-11-03"
    )

    state = engine.get_state()

    print(
        f"População       : "
        f"{state.population}"
    )

    print(
        f"Pop. activa     : "
        f"{state.working_age_population}"
    )

    print(
        f"Força trabalho  : "
        f"{state.labor_force}"
    )

    print(
        f"Empregados      : "
        f"{state.employed_population}"
    )

    print(
        f"Desempregados   : "
        f"{state.unemployed_population}"
    )

    print(
        f"Taxa emprego    : "
        f"{state.employment_rate:.2%}"
    )

    print(
        f"Taxa desemprego  : "
        f"{state.unemployment_rate:.2%}"
    )

    print()

    print(
        "BASELINE ECONÓMICO"
    )

    print(
        f"PIB             : "
        f"{state.real_gdp:.2f}"
    )

    print(
        f"Crescimento     : "
        f"{state.gdp_growth_rate:.2%}"
    )

    print(
        f"Inflação        : "
        f"{state.inflation_rate:.2%}"
    )

    print(
        f"Ciclo           : "
        f"{state.economic_cycle}"
    )

    # --------------------------------------------------------
    # SIMULAR ALTERAÇÃO DO PERÍODO SEGUINTE
    #
    # A economia cresce:
    #
    # consumo        350000 -> 370000
    # investimento   100000 -> 120000
    # governo         50000 -> 50000
    # exportações     80000 -> 90000
    # importações     60000 -> 65000
    #
    # Novo PIB:
    #
    # 370000 + 120000 + 50000 + 90000 - 65000
    # = 565000
    #
    # PIB anterior:
    # 520000
    #
    # Crescimento:
    # (565000 - 520000) / 520000
    # = 8.65%
    # --------------------------------------------------------

    engine.set_consumption(
        370000.0
    )

    engine.set_investment(
        120000.0
    )

    engine.set_trade(
        exports=90000.0,
        imports=65000.0,
    )

    print()

    print(
        "A processar segundo período..."
    )

    engine.process_tick(
        "2026-12-03"
    )

    state = engine.get_state()

    print()

    print("=" * 70)

    print(
        "RESULTADO DO TESTE"
    )

    print("-" * 70)

    print(
        f"Período        : "
        f"{state.period_number}"
    )

    print(
        f"PIB nominal    : "
        f"{state.nominal_gdp:.2f}"
    )

    print(
        f"PIB real       : "
        f"{state.real_gdp:.2f}"
    )

    print(
        f"PIB anterior   : "
        f"{state.previous_real_gdp:.2f}"
    )

    print(
        f"Crescimento    : "
        f"{state.gdp_growth_rate:.2%}"
    )

    print(
        f"Consumo        : "
        f"{state.consumption:.2f}"
    )

    print(
        f"Salários       : "
        f"{state.wages:.2f}"
    )

    print(
        f"Poupança       : "
        f"{state.household_savings:.2f}"
    )

    print(
        f"Investimento   : "
        f"{state.investment:.2f}"
    )

    print(
        f"Produtividade  : "
        f"{state.productivity:.4f}"
    )

    print(
        f"Índice preços  : "
        f"{state.price_index:.2f}"
    )

    print(
        f"Inflação       : "
        f"{state.inflation_rate:.2%}"
    )

    print(
        f"Juro           : "
        f"{state.interest_rate:.2%}"
    )

    print(
        f"Ciclo          : "
        f"{state.economic_cycle}"
    )

    print(
        f"Recessão       : "
        f"{state.recession}"
    )

    print(
        f"Data           : "
        f"{state.world_date}"
    )

    print("=" * 70)

    print()

    print(
        "ATHENA WORLD - ECONOMY ENGINE V01 "
        "carregado com sucesso."
    )

    print("=" * 70)