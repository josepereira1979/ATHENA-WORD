from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD
# FINANCIAL ENGINE V01
# ============================================================
#
# Responsabilidade:
#   - bancos
#   - depósitos
#   - crédito
#   - empréstimos
#   - juros
#   - obrigações
#   - fundos
#   - ETFs
#   - opções
#   - derivados
#   - seguros
#   - liquidez
#   - risco financeiro
#
# Este motor representa o sistema financeiro do mundo.
#
# NÃO controla diretamente:
#   - agentes
#   - empresas
#   - economia
#   - mercado
#   - recursos
#
# Esses sistemas comunicarão através de interfaces/eventos.
#
# ============================================================


ENGINE_NAME = "ATHENA WORLD - FINANCIAL ENGINE"
ENGINE_VERSION = "V01"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "financial_state.json"


# ============================================================
# BANCO
# ============================================================


@dataclass
class Bank:
    bank_id: str
    name: str

    deposits: float = 0.0
    loans: float = 0.0
    reserves: float = 0.0

    interest_rate: float = 0.05

    liquidity: float = 1.0
    capital_ratio: float = 1.0

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# CONTA
# ============================================================


@dataclass
class Account:
    account_id: str
    owner_id: str
    bank_id: str

    balance: float = 0.0

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# EMPRÉSTIMO
# ============================================================


@dataclass
class Loan:
    loan_id: str
    borrower_id: str
    bank_id: str

    principal: float
    outstanding: float

    interest_rate: float
    duration_ticks: int

    remaining_ticks: int

    status: str = "ACTIVE"

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# OBRIGAÇÃO
# ============================================================


@dataclass
class Bond:
    bond_id: str
    issuer_id: str
    name: str

    face_value: float
    price: float

    coupon_rate: float
    maturity_ticks: int
    remaining_ticks: int

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# FUNDO / ETF
# ============================================================


@dataclass
class Fund:
    fund_id: str
    name: str
    fund_type: str

    assets: List[str] = field(
        default_factory=list
    )

    total_value: float = 0.0
    units: float = 0.0
    unit_price: float = 0.0

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# OPÇÃO
# ============================================================


@dataclass
class Option:
    option_id: str
    underlying_asset_id: str

    option_type: str
    strike_price: float

    premium: float
    quantity: float

    expiry_tick: int

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# SEGURO
# ============================================================


@dataclass
class InsurancePolicy:
    policy_id: str
    owner_id: str

    coverage: float
    premium: float

    risk_level: float

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# ESTADO
# ============================================================


@dataclass
class FinancialState:
    world_date: str

    tick: int = 0
    total_ticks: int = 0

    banks: Dict[str, Bank] = field(
        default_factory=dict
    )

    accounts: Dict[str, Account] = field(
        default_factory=dict
    )

    loans: Dict[str, Loan] = field(
        default_factory=dict
    )

    bonds: Dict[str, Bond] = field(
        default_factory=dict
    )

    funds: Dict[str, Fund] = field(
        default_factory=dict
    )

    options: Dict[str, Option] = field(
        default_factory=dict
    )

    insurance_policies: Dict[
        str,
        InsurancePolicy,
    ] = field(
        default_factory=dict
    )

    total_banks: int = 0
    total_accounts: int = 0
    total_loans: int = 0
    total_bonds: int = 0
    total_funds: int = 0
    total_options: int = 0
    total_insurance_policies: int = 0

    total_deposits: float = 0.0
    total_credit: float = 0.0
    total_liquidity: float = 0.0

    financial_stress: float = 0.0

    created_at: str = ""
    updated_at: str = ""

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


# ============================================================
# FINANCIAL ENGINE
# ============================================================


class FinancialEngine:

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
            FinancialState
        ] = None

    # ========================================================
    # UTILIDADES
    # ========================================================

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat()

    @staticmethod
    def _safe_float(
        value: float,
    ) -> float:
        return max(0.0, float(value))

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def initialize(
        self,
        world_date: str,
    ) -> FinancialState:

        now = self._now()

        self.state = FinancialState(
            world_date=world_date,
            tick=0,
            total_ticks=0,
            banks={},
            accounts={},
            loans={},
            bonds={},
            funds={},
            options={},
            insurance_policies={},
            total_banks=0,
            total_accounts=0,
            total_loans=0,
            total_bonds=0,
            total_funds=0,
            total_options=0,
            total_insurance_policies=0,
            total_deposits=0.0,
            total_credit=0.0,
            total_liquidity=0.0,
            financial_stress=0.0,
            created_at=now,
            updated_at=now,
        )

        self._save()

        return self.state

    # ========================================================
    # BANCOS
    # ========================================================

    def create_bank(
        self,
        bank_id: str,
        name: str,
        reserves: float = 0.0,
        interest_rate: float = 0.05,
    ) -> Bank:

        self._require_state()

        if bank_id in self.state.banks:
            raise ValueError(
                f"Bank already exists: {bank_id}"
            )

        now = self._now()

        bank = Bank(
            bank_id=bank_id,
            name=name,
            deposits=0.0,
            loans=0.0,
            reserves=self._safe_float(
                reserves
            ),
            interest_rate=max(
                0.0,
                float(interest_rate),
            ),
            liquidity=1.0,
            capital_ratio=1.0,
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.banks[bank_id] = bank

        self._refresh_aggregates()
        self._touch()
        self._save()

        return bank

    # ========================================================
    # CONTAS
    # ========================================================

    def create_account(
        self,
        account_id: str,
        owner_id: str,
        bank_id: str,
        initial_balance: float = 0.0,
    ) -> Account:

        self._require_state()

        if account_id in self.state.accounts:
            raise ValueError(
                f"Account already exists: {account_id}"
            )

        bank = self.get_bank(bank_id)

        now = self._now()

        balance = self._safe_float(
            initial_balance
        )

        account = Account(
            account_id=account_id,
            owner_id=owner_id,
            bank_id=bank_id,
            balance=balance,
            created_at=now,
            updated_at=now,
        )

        self.state.accounts[
            account_id
        ] = account

        bank.deposits += balance

        bank.updated_at = now

        self._refresh_aggregates()
        self._touch()
        self._save()

        return account

    # ========================================================
    # DEPÓSITOS
    # ========================================================

    def deposit(
        self,
        account_id: str,
        amount: float,
    ) -> Account:

        account = self.get_account(
            account_id
        )

        amount = self._safe_float(
            amount
        )

        account.balance += amount

        bank = self.get_bank(
            account.bank_id
        )

        bank.deposits += amount

        account.updated_at = self._now()
        bank.updated_at = self._now()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return account

    # ========================================================
    # LEVANTAMENTOS
    # ========================================================

    def withdraw(
        self,
        account_id: str,
        amount: float,
    ) -> Account:

        account = self.get_account(
            account_id
        )

        amount = self._safe_float(
            amount
        )

        amount = min(
            amount,
            account.balance,
        )

        account.balance -= amount

        bank = self.get_bank(
            account.bank_id
        )

        bank.deposits = max(
            0.0,
            bank.deposits - amount,
        )

        account.updated_at = self._now()
        bank.updated_at = self._now()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return account

    # ========================================================
    # EMPRÉSTIMOS
    # ========================================================

    def create_loan(
        self,
        borrower_id: str,
        bank_id: str,
        principal: float,
        duration_ticks: int,
        interest_rate: Optional[float] = None,
    ) -> Loan:

        self._require_state()

        bank = self.get_bank(
            bank_id
        )

        principal = self._safe_float(
            principal
        )

        if principal <= 0:
            raise ValueError(
                "Loan principal must be greater than zero."
            )

        duration_ticks = max(
            1,
            int(duration_ticks),
        )

        if interest_rate is None:
            interest_rate = (
                bank.interest_rate
            )

        now = self._now()

        loan_id = (
            "LOAN-"
            + uuid.uuid4().hex[:12].upper()
        )

        loan = Loan(
            loan_id=loan_id,
            borrower_id=borrower_id,
            bank_id=bank_id,
            principal=principal,
            outstanding=principal,
            interest_rate=max(
                0.0,
                float(interest_rate),
            ),
            duration_ticks=duration_ticks,
            remaining_ticks=duration_ticks,
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )

        self.state.loans[
            loan_id
        ] = loan

        bank.loans += principal

        bank.updated_at = now

        self._refresh_aggregates()
        self._touch()
        self._save()

        return loan

    # ========================================================
    # JUROS DO EMPRÉSTIMO
    # ========================================================

    def calculate_loan_interest(
        self,
        loan_id: str,
    ) -> float:

        loan = self.get_loan(
            loan_id
        )

        return (
            loan.outstanding
            * loan.interest_rate
        )

    # ========================================================
    # PAGAMENTO
    # ========================================================

    def repay_loan(
        self,
        loan_id: str,
        amount: float,
    ) -> Loan:

        loan = self.get_loan(
            loan_id
        )

        amount = self._safe_float(
            amount
        )

        amount = min(
            amount,
            loan.outstanding,
        )

        loan.outstanding -= amount

        if loan.outstanding <= 0:
            loan.outstanding = 0.0
            loan.status = "PAID"

        bank = self.get_bank(
            loan.bank_id
        )

        bank.loans = max(
            0.0,
            bank.loans - amount,
        )

        loan.updated_at = self._now()
        bank.updated_at = self._now()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return loan

    # ========================================================
    # OBRIGAÇÕES
    # ========================================================

    def create_bond(
        self,
        bond_id: str,
        issuer_id: str,
        name: str,
        face_value: float,
        coupon_rate: float,
        maturity_ticks: int,
    ) -> Bond:

        self._require_state()

        if bond_id in self.state.bonds:
            raise ValueError(
                f"Bond already exists: {bond_id}"
            )

        now = self._now()

        face_value = self._safe_float(
            face_value
        )

        maturity_ticks = max(
            1,
            int(maturity_ticks),
        )

        bond = Bond(
            bond_id=bond_id,
            issuer_id=issuer_id,
            name=name,
            face_value=face_value,
            price=face_value,
            coupon_rate=max(
                0.0,
                float(coupon_rate),
            ),
            maturity_ticks=maturity_ticks,
            remaining_ticks=maturity_ticks,
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.bonds[
            bond_id
        ] = bond

        self._refresh_aggregates()
        self._touch()
        self._save()

        return bond

    # ========================================================
    # FUNDOS / ETFs
    # ========================================================

    def create_fund(
        self,
        fund_id: str,
        name: str,
        fund_type: str,
        assets: Optional[List[str]] = None,
        total_value: float = 0.0,
        units: float = 0.0,
    ) -> Fund:

        self._require_state()

        if fund_id in self.state.funds:
            raise ValueError(
                f"Fund already exists: {fund_id}"
            )

        assets = (
            list(assets)
            if assets is not None
            else []
        )

        total_value = self._safe_float(
            total_value
        )

        units = self._safe_float(
            units
        )

        if units > 0:
            unit_price = (
                total_value / units
            )
        else:
            unit_price = 0.0

        now = self._now()

        fund = Fund(
            fund_id=fund_id,
            name=name,
            fund_type=fund_type,
            assets=assets,
            total_value=total_value,
            units=units,
            unit_price=unit_price,
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.funds[
            fund_id
        ] = fund

        self._refresh_aggregates()
        self._touch()
        self._save()

        return fund

    # ========================================================
    # OPÇÕES
    # ========================================================

    def create_option(
        self,
        underlying_asset_id: str,
        option_type: str,
        strike_price: float,
        premium: float,
        quantity: float,
        expiry_tick: int,
    ) -> Option:

        self._require_state()

        option_type = (
            str(option_type)
            .upper()
            .strip()
        )

        if option_type not in {
            "CALL",
            "PUT",
        }:

            raise ValueError(
                "Option type must be CALL or PUT."
            )

        now = self._now()

        option_id = (
            "OPTION-"
            + uuid.uuid4().hex[:12].upper()
        )

        option = Option(
            option_id=option_id,
            underlying_asset_id=(
                underlying_asset_id
            ),
            option_type=option_type,
            strike_price=self._safe_float(
                strike_price
            ),
            premium=self._safe_float(
                premium
            ),
            quantity=self._safe_float(
                quantity
            ),
            expiry_tick=max(
                1,
                int(expiry_tick),
            ),
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.options[
            option_id
        ] = option

        self._refresh_aggregates()
        self._touch()
        self._save()

        return option

    # ========================================================
    # SEGUROS
    # ========================================================

    def create_insurance(
        self,
        owner_id: str,
        coverage: float,
        premium: float,
        risk_level: float,
    ) -> InsurancePolicy:

        self._require_state()

        now = self._now()

        policy_id = (
            "POLICY-"
            + uuid.uuid4().hex[:12].upper()
        )

        policy = InsurancePolicy(
            policy_id=policy_id,
            owner_id=owner_id,
            coverage=self._safe_float(
                coverage
            ),
            premium=self._safe_float(
                premium
            ),
            risk_level=max(
                0.0,
                min(1.0, float(risk_level)),
            ),
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.insurance_policies[
            policy_id
        ] = policy

        self._refresh_aggregates()
        self._touch()
        self._save()

        return policy

    # ========================================================
    # LIQUIDEZ BANCÁRIA
    # ========================================================

    def update_bank_liquidity(
        self,
        bank_id: str,
    ) -> Bank:

        bank = self.get_bank(
            bank_id
        )

        if bank.deposits > 0:

            ratio = (
                bank.reserves
                / bank.deposits
            )

            bank.liquidity = max(
                0.0,
                min(1.0, ratio),
            )

        else:

            bank.liquidity = 1.0

        if bank.loans > 0:

            bank.capital_ratio = max(
                0.0,
                min(
                    1.0,
                    bank.reserves
                    / bank.loans,
                ),
            )

        else:

            bank.capital_ratio = 1.0

        bank.updated_at = self._now()

        return bank

    # ========================================================
    # STRESS FINANCEIRO
    # ========================================================

    def calculate_financial_stress(
        self,
    ) -> float:

        self._require_state()

        banks = list(
            self.state.banks.values()
        )

        if not banks:
            self.state.financial_stress = 0.0
            return 0.0

        liquidity_values = []

        capital_values = []

        for bank in banks:

            self.update_bank_liquidity(
                bank.bank_id
            )

            liquidity_values.append(
                bank.liquidity
            )

            capital_values.append(
                bank.capital_ratio
            )

        average_liquidity = (
            sum(liquidity_values)
            / len(liquidity_values)
        )

        average_capital = (
            sum(capital_values)
            / len(capital_values)
        )

        stress = 1.0 - (
            (
                average_liquidity
                + average_capital
            )
            / 2.0
        )

        self.state.financial_stress = max(
            0.0,
            min(1.0, stress),
        )

        return self.state.financial_stress

    # ========================================================
    # TICK
    # ========================================================

    def process_tick(
        self,
        world_date: str,
    ) -> FinancialState:

        self._require_state()

        self.state.tick += 1
        self.state.total_ticks += 1
        self.state.world_date = world_date

        # ----------------------------------------------------
        # EMPRÉSTIMOS
        # ----------------------------------------------------

        for loan in (
            self.state.loans.values()
        ):

            if loan.status != "ACTIVE":
                continue

            interest = (
                loan.outstanding
                * loan.interest_rate
            )

            loan.outstanding += interest

            loan.remaining_ticks = max(
                0,
                loan.remaining_ticks - 1,
            )

            if loan.remaining_ticks <= 0:
                loan.status = "MATURED"

            loan.updated_at = self._now()

        # ----------------------------------------------------
        # OBRIGAÇÕES
        # ----------------------------------------------------

        for bond in (
            self.state.bonds.values()
        ):

            if not bond.active:
                continue

            bond.remaining_ticks = max(
                0,
                bond.remaining_ticks - 1,
            )

            if bond.remaining_ticks <= 0:
                bond.active = False

            bond.updated_at = self._now()

        # ----------------------------------------------------
        # OPÇÕES
        # ----------------------------------------------------

        for option in (
            self.state.options.values()
        ):

            if (
                option.active
                and self.state.tick
                >= option.expiry_tick
            ):

                option.active = False
                option.updated_at = (
                    self._now()
                )

        # ----------------------------------------------------
        # LIQUIDEZ / STRESS
        # ----------------------------------------------------

        for bank in (
            self.state.banks.values()
        ):

            self.update_bank_liquidity(
                bank.bank_id
            )

        self.calculate_financial_stress()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return self.state

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_bank(
        self,
        bank_id: str,
    ) -> Bank:

        self._require_state()

        try:
            return self.state.banks[
                bank_id
            ]
        except KeyError:
            raise KeyError(
                f"Bank not found: {bank_id}"
            )

    def get_account(
        self,
        account_id: str,
    ) -> Account:

        self._require_state()

        try:
            return self.state.accounts[
                account_id
            ]
        except KeyError:
            raise KeyError(
                f"Account not found: {account_id}"
            )

    def get_loan(
        self,
        loan_id: str,
    ) -> Loan:

        self._require_state()

        try:
            return self.state.loans[
                loan_id
            ]
        except KeyError:
            raise KeyError(
                f"Loan not found: {loan_id}"
            )

    # ========================================================
    # AGREGADOS
    # ========================================================

    def _refresh_aggregates(
        self,
    ) -> None:

        if self.state is None:
            return

        self.state.total_banks = len(
            self.state.banks
        )

        self.state.total_accounts = len(
            self.state.accounts
        )

        self.state.total_loans = len(
            self.state.loans
        )

        self.state.total_bonds = len(
            self.state.bonds
        )

        self.state.total_funds = len(
            self.state.funds
        )

        self.state.total_options = len(
            self.state.options
        )

        self.state.total_insurance_policies = (
            len(
                self.state.insurance_policies
            )
        )

        self.state.total_deposits = sum(
            bank.deposits
            for bank in self.state.banks.values()
        )

        self.state.total_credit = sum(
            loan.outstanding
            for loan in self.state.loans.values()
            if loan.status == "ACTIVE"
        )

        if self.state.banks:

            self.state.total_liquidity = (
                sum(
                    bank.liquidity
                    for bank in self.state.banks.values()
                )
                / len(self.state.banks)
            )

        else:

            self.state.total_liquidity = 0.0

    # ========================================================
    # ESTADO
    # ========================================================

    def _require_state(
        self,
    ) -> None:

        if self.state is None:
            raise RuntimeError(
                "FinancialEngine is not initialized."
            )

    def _touch(
        self,
    ) -> None:

        if self.state is not None:
            self.state.updated_at = (
                self._now()
            )

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    def save(self) -> None:
        self._save()

    def _save(self) -> None:

        if self.state is None:
            return

        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = asdict(
            self.state
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

    def load(
        self,
    ) -> FinancialState:

        if not self.state_file.exists():

            raise FileNotFoundError(
                "Financial state file not found: "
                f"{self.state_file}"
            )

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        banks = {}

        for bank_id, bank_data in (
            data.get(
                "banks",
                {},
            ).items()
        ):

            banks[bank_id] = Bank(
                **bank_data
            )

        accounts = {}

        for account_id, account_data in (
            data.get(
                "accounts",
                {},
            ).items()
        ):

            accounts[account_id] = Account(
                **account_data
            )

        loans = {}

        for loan_id, loan_data in (
            data.get(
                "loans",
                {},
            ).items()
        ):

            loans[loan_id] = Loan(
                **loan_data
            )

        bonds = {}

        for bond_id, bond_data in (
            data.get(
                "bonds",
                {},
            ).items()
        ):

            bonds[bond_id] = Bond(
                **bond_data
            )

        funds = {}

        for fund_id, fund_data in (
            data.get(
                "funds",
                {},
            ).items()
        ):

            funds[fund_id] = Fund(
                **fund_data
            )

        options = {}

        for option_id, option_data in (
            data.get(
                "options",
                {},
            ).items()
        ):

            options[option_id] = Option(
                **option_data
            )

        insurance_policies = {}

        for (
            policy_id,
            policy_data,
        ) in (
            data.get(
                "insurance_policies",
                {},
            ).items()
        ):

            insurance_policies[
                policy_id
            ] = InsurancePolicy(
                **policy_data
            )

        data["banks"] = banks
        data["accounts"] = accounts
        data["loans"] = loans
        data["bonds"] = bonds
        data["funds"] = funds
        data["options"] = options
        data["insurance_policies"] = (
            insurance_policies
        )

        self.state = FinancialState(
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

    engine = FinancialEngine()

    engine.initialize(
        world_date="2026-09-29"
    )

    # --------------------------------------------------------
    # BANCO
    # --------------------------------------------------------

    bank = engine.create_bank(
        bank_id="BANK-001",
        name="Banco Central",
        reserves=100_000.0,
        interest_rate=0.05,
    )

    # --------------------------------------------------------
    # CONTA
    # --------------------------------------------------------

    account = engine.create_account(
        account_id="ACCOUNT-001",
        owner_id="AGENT-001",
        bank_id="BANK-001",
        initial_balance=50_000.0,
    )

    # --------------------------------------------------------
    # EMPRÉSTIMO
    # --------------------------------------------------------

    loan = engine.create_loan(
        borrower_id="COMPANY-001",
        bank_id="BANK-001",
        principal=20_000.0,
        duration_ticks=12,
        interest_rate=0.05,
    )

    interest = (
        engine.calculate_loan_interest(
            loan.loan_id
        )
    )

    # --------------------------------------------------------
    # OBRIGAÇÃO
    # --------------------------------------------------------

    bond = engine.create_bond(
        bond_id="BOND-001",
        issuer_id="COMPANY-001",
        name="Atlas Bond",
        face_value=10_000.0,
        coupon_rate=0.04,
        maturity_ticks=24,
    )

    # --------------------------------------------------------
    # ETF
    # --------------------------------------------------------

    fund = engine.create_fund(
        fund_id="ETF-001",
        name="ATHENA World ETF",
        fund_type="ETF",
        assets=["ASSET-001"],
        total_value=100_000.0,
        units=1_000.0,
    )

    # --------------------------------------------------------
    # OPÇÃO
    # --------------------------------------------------------

    option = engine.create_option(
        underlying_asset_id="ASSET-001",
        option_type="CALL",
        strike_price=100.0,
        premium=5.0,
        quantity=100.0,
        expiry_tick=30,
    )

    # --------------------------------------------------------
    # SEGURO
    # --------------------------------------------------------

    policy = engine.create_insurance(
        owner_id="COMPANY-001",
        coverage=50_000.0,
        premium=500.0,
        risk_level=0.20,
    )

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    print()
    print("BANCO")
    print(
        "Nome          :",
        bank.name,
    )
    print(
        "Depósitos     :",
        f"{bank.deposits:,.2f}",
    )
    print(
        "Reservas      :",
        f"{bank.reserves:,.2f}",
    )

    print()
    print("CONTA")
    print(
        "Saldo         :",
        f"{account.balance:,.2f}",
    )

    print()
    print("EMPRÉSTIMO")
    print(
        "Capital       :",
        f"{loan.principal:,.2f}",
    )
    print(
        "Juro          :",
        f"{interest:,.2f}",
    )
    print(
        "Outstanding   :",
        f"{loan.outstanding:,.2f}",
    )

    print()
    print("OBRIGAÇÃO")
    print(
        "Valor nominal :",
        f"{bond.face_value:,.2f}",
    )
    print(
        "Cupão         :",
        f"{bond.coupon_rate:.2%}",
    )

    print()
    print("ETF")
    print(
        "Nome          :",
        fund.name,
    )
    print(
        "Preço unidade :",
        f"{fund.unit_price:,.2f}",
    )

    print()
    print("OPÇÃO")
    print(
        "Tipo          :",
        option.option_type,
    )
    print(
        "Strike        :",
        f"{option.strike_price:,.2f}",
    )
    print(
        "Prémio        :",
        f"{option.premium:,.2f}",
    )

    print()
    print("SEGURO")
    print(
        "Cobertura     :",
        f"{policy.coverage:,.2f}",
    )
    print(
        "Prémio        :",
        f"{policy.premium:,.2f}",
    )

    # --------------------------------------------------------
    # TICK
    # --------------------------------------------------------

    engine.process_tick(
        "2026-10-29"
    )

    print()
    print("APÓS 1 TICK")
    print(
        "Tick          :",
        engine.state.tick,
    )
    print(
        "Crédito total :",
        f"{engine.state.total_credit:,.2f}",
    )
    print(
        "Liquidez      :",
        f"{engine.state.total_liquidity:.2%}",
    )
    print(
        "Stress        :",
        f"{engine.state.financial_stress:.2%}",
    )

    print()
    print(
        "FINANCIAL ENGINE V01 "
        "TESTE CONCLUIDO"
    )

    print("=" * 60)