from __future__ import annotations

import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD - AGENT ENGINE V02
# ============================================================
#
# Responsabilidade:
# - Criar e gerir agentes
# - Personalidade
# - Profissão
# - Capital
# - Rendimento mensal
# - Despesas mensais
# - Conhecimento
# - Memória
# - Objectivos
# - Experiência
# - Decisões
# - Aprendizagem
# - Idade
# - Mortalidade básica
# - Persistência
#
# NOTA:
# Os valores de income e expenses são MENSALMENTE.
# O motor converte-os para um valor diário durante a simulação.
#
# A lógica económica actual é provisória.
# Mais tarde será substituída pelos COMPANY / ECONOMY ENGINES.
# ============================================================


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "agents_state.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PERSONALITY
# ============================================================

@dataclass
class Personality:
    curiosity: float = 0.5
    discipline: float = 0.5
    risk_tolerance: float = 0.5
    patience: float = 0.5
    ambition: float = 0.5
    sociability: float = 0.5
    adaptability: float = 0.5


# ============================================================
# MEMORY
# ============================================================

@dataclass
class MemoryEntry:
    memory_id: str
    world_date: str
    event_type: str
    description: str
    outcome: str
    importance: float


# ============================================================
# KNOWLEDGE
# ============================================================

@dataclass
class Knowledge:
    economics: float = 0.0
    finance: float = 0.0
    technology: float = 0.0
    management: float = 0.0
    production: float = 0.0
    social: float = 0.0
    general: float = 0.0


# ============================================================
# AGENT
# ============================================================

@dataclass
class Agent:
    agent_id: str
    first_name: str
    last_name: str

    age: int
    gender: str
    birth_date: str

    profession: str
    primary_company_id: Optional[str]

    capital: float
    income: float
    expenses: float
    debt: float

    goals: List[str]

    personality: Personality
    knowledge: Knowledge
    memories: List[MemoryEntry]

    decisions_made: int
    successful_decisions: int
    failed_decisions: int

    experience: float

    alive: bool
    generation: int
    family_id: Optional[str]

    created_world_date: str
    last_update_world_date: str

    total_ticks_processed: int

    # Estado de investigação; evidência só aumenta quando há dados verificáveis.
    research_role: str = "GENERALIST"
    research_focus: Optional[str] = None
    evidence_collected: int = 0
    hypotheses_proposed: int = 0
    hypotheses_challenged: int = 0
    validated_predictions: int = 0
    prediction_accuracy: float = 0.0


# ============================================================
# AGENT ENGINE
# ============================================================

class AgentEngine:

    ENGINE_NAME = "ATHENA WORLD - AGENT ENGINE"
    ENGINE_VERSION = "V02"

    # Aproximação provisória de um mês económico.
    DAYS_PER_MONTH = 30.0

    # Mortalidade extremamente simplificada nesta fase.
    # Será substituída / aprofundada posteriormente.
    MAX_AGE = 100

    def __init__(
        self,
        state_file: Path = STATE_FILE,
        auto_load: bool = True,
    ):
        self.state_file = Path(state_file)
        self.agents: Dict[str, Agent] = {}

        if auto_load:
            self.load()

    # ========================================================
    # UTILITÁRIOS
    # ========================================================

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        return max(minimum, min(maximum, float(value)))

    @staticmethod
    def _random_name() -> tuple[str, str]:
        first_names = [
            "Alex",
            "Maria",
            "João",
            "Ana",
            "Miguel",
            "Sofia",
            "Pedro",
            "Inês",
            "Daniel",
            "Laura",
        ]

        last_names = [
            "Pereira",
            "Silva",
            "Costa",
            "Santos",
            "Oliveira",
            "Ferreira",
            "Rodrigues",
            "Martins",
            "Sousa",
            "Gomes",
        ]

        return (
            random.choice(first_names),
            random.choice(last_names),
        )

    @staticmethod
    def _calculate_birth_date(
        world_date: date,
        age: int,
    ) -> date:
        birth_date = world_date.replace(
            year=world_date.year - age
        )

        # Pequena variação para evitar que todos os agentes
        # nasçam exactamente no mesmo dia.
        day_offset = random.randint(0, 364)

        try:
            birth_date = birth_date - timedelta(days=day_offset)
        except Exception:
            pass

        return birth_date

    # ========================================================
    # PERSONALIDADE
    # ========================================================

    def _generate_personality(self) -> Personality:
        return Personality(
            curiosity=self._clamp(random.uniform(0.2, 0.9)),
            discipline=self._clamp(random.uniform(0.2, 0.9)),
            risk_tolerance=self._clamp(random.uniform(0.1, 0.9)),
            patience=self._clamp(random.uniform(0.2, 0.9)),
            ambition=self._clamp(random.uniform(0.2, 0.9)),
            sociability=self._clamp(random.uniform(0.2, 0.9)),
            adaptability=self._clamp(random.uniform(0.2, 0.9)),
        )

    # ========================================================
    # CRIAR AGENTE
    # ========================================================

    def create_agent(
        self,
        world_date: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        profession: str = "Profissional",
        primary_company_id: Optional[str] = None,
        capital: float = 25000.0,
        income: Optional[float] = None,
        expenses: Optional[float] = None,
        debt: float = 0.0,
        goals: Optional[List[str]] = None,
        generation: int = 1,
        family_id: Optional[str] = None,
    ) -> Agent:

        world_day = date.fromisoformat(world_date)

        if first_name is None or last_name is None:
            generated_first, generated_last = self._random_name()

            if first_name is None:
                first_name = generated_first

            if last_name is None:
                last_name = generated_last

        if age is None:
            age = random.randint(20, 60)

        if gender is None:
            gender = random.choice(
                [
                    "M",
                    "F",
                ]
            )

        if income is None:
            # Rendimento MENSAL provisório.
            income = random.uniform(1500.0, 3500.0)

        if expenses is None:
            # Despesas MENSAIS provisórias.
            expenses = income * random.uniform(0.65, 0.85)

        if goals is None:
            goals = [
                "Aumentar capital",
                "Aprender",
                "Melhorar qualidade de vida",
            ]

        birth_date = self._calculate_birth_date(
            world_day,
            age,
        )

        agent = Agent(
            agent_id=self._new_id("AGENT"),
            first_name=first_name,
            last_name=last_name,
            age=int(age),
            gender=gender,
            birth_date=birth_date.isoformat(),
            profession=profession,
            primary_company_id=primary_company_id,
            capital=float(capital),
            income=float(income),
            expenses=float(expenses),
            debt=float(debt),
            goals=list(goals),
            personality=self._generate_personality(),
            knowledge=Knowledge(),
            memories=[],
            decisions_made=0,
            successful_decisions=0,
            failed_decisions=0,
            experience=0.0,
            alive=True,
            generation=int(generation),
            family_id=family_id,
            created_world_date=world_date,
            last_update_world_date=world_date,
            total_ticks_processed=0,
        )

        self.agents[agent.agent_id] = agent

        # Memória inicial de existência.
        self._add_memory(
            agent=agent,
            world_date=world_date,
            event_type="CREATION",
            description="Agente criado no ATHENA WORLD.",
            outcome="Agente iniciou a sua existência.",
            importance=0.5,
        )

        self.save()

        return agent

    # ========================================================
    # PROCESSAR TICK
    # ========================================================

    def process_tick(
        self,
        world_date: str,
    ) -> None:

        for agent in list(self.agents.values()):

            if not agent.alive:
                continue

            self._process_agent_tick(
                agent=agent,
                world_date=world_date,
            )

        self.save()

    # ========================================================
    # PROCESSAR AGENTE
    # ========================================================

    def _process_agent_tick(
        self,
        agent: Agent,
        world_date: str,
    ) -> None:

        world_day = date.fromisoformat(world_date)

        # ----------------------------------------------------
        # Contador do tick
        # ----------------------------------------------------

        next_tick = agent.total_ticks_processed + 1

        # ----------------------------------------------------
        # Idade
        # ----------------------------------------------------

        self._update_age(
            agent=agent,
            world_day=world_day,
        )

        # ----------------------------------------------------
        # Economia individual
        # ----------------------------------------------------

        self._update_economic_state(
            agent=agent,
        )

        # ----------------------------------------------------
        # Experiência
        # ----------------------------------------------------

        self._update_experience(
            agent=agent,
        )

        # ----------------------------------------------------
        # Aprendizagem
        # ----------------------------------------------------

        self._learn_from_life(
            agent=agent,
        )

        # ----------------------------------------------------
        # Memória periódica
        # ----------------------------------------------------

        if next_tick % 30 == 0:

            self._create_periodic_memory(
                agent=agent,
                world_date=world_date,
            )

        # ----------------------------------------------------
        # Mortalidade
        # ----------------------------------------------------

        self._process_mortality(
            agent=agent,
        )

        # ----------------------------------------------------
        # Estado final
        # ----------------------------------------------------

        agent.total_ticks_processed = next_tick
        agent.last_update_world_date = world_date

    # ========================================================
    # IDADE
    # ========================================================

    def _update_age(
        self,
        agent: Agent,
        world_day: date,
    ) -> None:

        birth_day = date.fromisoformat(
            agent.birth_date
        )

        age = (
            world_day.year
            - birth_day.year
            - (
                (
                    world_day.month,
                    world_day.day
                )
                <
                (
                    birth_day.month,
                    birth_day.day
                )
            )
        )

        agent.age = max(0, age)

    # ========================================================
    # ECONOMIA INDIVIDUAL
    # ========================================================

    def _update_economic_state(
        self,
        agent: Agent,
    ) -> None:

        # IMPORTANTÍSSIMO:
        #
        # income e expenses são valores MENSAIS.
        #
        # Como o WORLD CORE avança diariamente nesta fase,
        # convertemos o saldo mensal para saldo diário.

        monthly_income = max(
            0.0,
            float(agent.income),
        )

        monthly_expenses = max(
            0.0,
            float(agent.expenses),
        )

        daily_income = (
            monthly_income
            / self.DAYS_PER_MONTH
        )

        daily_expenses = (
            monthly_expenses
            / self.DAYS_PER_MONTH
        )

        daily_net = (
            daily_income
            - daily_expenses
        )

        agent.capital += daily_net

        # Juros muito simples sobre dívida nesta fase.
        if agent.debt > 0:

            daily_interest = (
                agent.debt
                * 0.0001
            )

            agent.debt += daily_interest

        # Capital não é permitido ficar infinitamente abaixo
        # de zero nesta fase.
        if agent.capital < 0:

            deficit = abs(agent.capital)

            agent.capital = 0.0
            agent.debt += deficit

    # ========================================================
    # EXPERIÊNCIA
    # ========================================================

    def _update_experience(
        self,
        agent: Agent,
    ) -> None:

        discipline = agent.personality.discipline
        curiosity = agent.personality.curiosity
        adaptability = agent.personality.adaptability

        gain = (
            0.00025
            + discipline * 0.00025
            + curiosity * 0.00025
            + adaptability * 0.00025
        )

        agent.experience = min(
            1.0,
            agent.experience + gain,
        )

    # ========================================================
    # APRENDIZAGEM
    # ========================================================

    def _learn_from_life(
        self,
        agent: Agent,
    ) -> None:

        curiosity = agent.personality.curiosity
        adaptability = agent.personality.adaptability
        discipline = agent.personality.discipline

        agent.knowledge.technology = min(
            1.0,
            agent.knowledge.technology
            + curiosity * 0.0002
            + adaptability * 0.00015,
        )

        agent.knowledge.general = min(
            1.0,
            agent.knowledge.general
            + curiosity * 0.00015,
        )

        agent.knowledge.economics = min(
            1.0,
            agent.knowledge.economics
            + discipline * 0.0001,
        )

        agent.knowledge.finance = min(
            1.0,
            agent.knowledge.finance
            + curiosity * 0.0001,
        )

        agent.knowledge.management = min(
            1.0,
            agent.knowledge.management
            + discipline * 0.0001,
        )

        agent.knowledge.production = min(
            1.0,
            agent.knowledge.production
            + discipline * 0.0001,
        )

        agent.knowledge.social = min(
            1.0,
            agent.knowledge.social
            + agent.personality.sociability * 0.0001,
        )

    # ========================================================
    # MEMÓRIA PERIÓDICA
    # ========================================================

    def _create_periodic_memory(
        self,
        agent: Agent,
        world_date: str,
    ) -> None:

        outcome = (
            f"Capital {agent.capital:.2f}; "
            f"experiência {agent.experience:.4f}; "
            f"conhecimento geral "
            f"{agent.knowledge.general:.4f}."
        )

        self._add_memory(
            agent=agent,
            world_date=world_date,
            event_type="LIFE_UPDATE",
            description=(
                "Avaliação periódica da vida "
                "e aprendizagem do agente."
            ),
            outcome=outcome,
            importance=0.3,
        )

    # ========================================================
    # MEMÓRIA
    # ========================================================

    def _add_memory(
        self,
        agent: Agent,
        world_date: str,
        event_type: str,
        description: str,
        outcome: str,
        importance: float,
    ) -> None:

        memory = MemoryEntry(
            memory_id=self._new_id("MEM"),
            world_date=world_date,
            event_type=event_type,
            description=description,
            outcome=outcome,
            importance=self._clamp(
                importance,
                0.0,
                1.0,
            ),
        )

        agent.memories.append(memory)

    def add_memory(
        self,
        agent_id: str,
        world_date: str,
        event_type: str,
        description: str,
        outcome: str,
        importance: float = 0.5,
    ) -> bool:

        agent = self.get_agent(agent_id)

        if agent is None:
            return False

        self._add_memory(
            agent=agent,
            world_date=world_date,
            event_type=event_type,
            description=description,
            outcome=outcome,
            importance=importance,
        )

        self.save()

        return True

    # ========================================================
    # MORTALIDADE
    # ========================================================

    def _process_mortality(
        self,
        agent: Agent,
    ) -> None:

        if agent.age >= self.MAX_AGE:

            agent.alive = False
            return

        # Probabilidade extremamente pequena antes
        # dos 80 anos.
        if agent.age < 80:
            return

        # Cresce progressivamente depois dos 80.
        excess_age = agent.age - 80

        probability = (
            0.001
            * (excess_age + 1)
        )

        if random.random() < probability:

            agent.alive = False

    # ========================================================
    # DECISÕES
    # ========================================================

    def register_decision(
        self,
        agent_id: str,
        success: bool,
    ) -> bool:

        agent = self.get_agent(agent_id)

        if agent is None:
            return False

        agent.decisions_made += 1

        if success:
            agent.successful_decisions += 1

            agent.experience = min(
                1.0,
                agent.experience + 0.005,
            )

        else:
            agent.failed_decisions += 1

            agent.experience = min(
                1.0,
                agent.experience + 0.002,
            )

        self.save()

        return True

    # ========================================================
    # CAPITAL
    # ========================================================

    def change_capital(
        self,
        agent_id: str,
        amount: float,
    ) -> bool:

        agent = self.get_agent(agent_id)

        if agent is None:
            return False

        agent.capital += float(amount)

        if agent.capital < 0:

            deficit = abs(agent.capital)

            agent.capital = 0.0
            agent.debt += deficit

        self.save()

        return True

    # ========================================================
    # INCOME
    # ========================================================

    def set_income(
        self,
        agent_id: str,
        monthly_income: float,
    ) -> bool:

        agent = self.get_agent(agent_id)

        if agent is None:
            return False

        agent.income = max(
            0.0,
            float(monthly_income),
        )

        self.save()

        return True

    # ========================================================
    # EXPENSES
    # ========================================================

    def set_expenses(
        self,
        agent_id: str,
        monthly_expenses: float,
    ) -> bool:

        agent = self.get_agent(agent_id)

        if agent is None:
            return False

        agent.expenses = max(
            0.0,
            float(monthly_expenses),
        )

        self.save()

        return True

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_agent(
        self,
        agent_id: str,
    ) -> Optional[Agent]:

        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[Agent]:

        return list(
            self.agents.values()
        )

    def get_alive_agents(self) -> List[Agent]:

        return [
            agent
            for agent in self.agents.values()
            if agent.alive
        ]

    def count(self) -> int:

        return len(
            self.agents
        )

    def alive_count(self) -> int:

        return len(
            self.get_alive_agents()
        )

    # ========================================================
    # VIDA
    # ========================================================

    def kill_agent(
        self,
        agent_id: str,
    ) -> bool:

        agent = self.get_agent(agent_id)

        if agent is None:
            return False

        agent.alive = False

        self.save()

        return True

    def revive_agent(
        self,
        agent_id: str,
    ) -> bool:

        agent = self.get_agent(agent_id)

        if agent is None:
            return False

        agent.alive = True

        self.save()

        return True

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    @staticmethod
    def _serialize_agent(
        agent: Agent,
    ) -> dict:

        data = asdict(agent)

        return data

    @staticmethod
    def _deserialize_agent(
        data: dict,
    ) -> Agent:

        personality_data = data.get(
            "personality",
            {},
        )

        knowledge_data = data.get(
            "knowledge",
            {},
        )

        memories_data = data.get(
            "memories",
            [],
        )

        personality = Personality(
            **personality_data
        )

        knowledge = Knowledge(
            **knowledge_data
        )

        memories = [
            MemoryEntry(
                **memory
            )
            for memory in memories_data
        ]

        return Agent(
            agent_id=data["agent_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            age=int(data["age"]),
            gender=data["gender"],
            birth_date=data["birth_date"],
            profession=data["profession"],
            primary_company_id=data.get(
                "primary_company_id"
            ),
            capital=float(
                data.get("capital", 0.0)
            ),
            income=float(
                data.get("income", 0.0)
            ),
            expenses=float(
                data.get("expenses", 0.0)
            ),
            debt=float(
                data.get("debt", 0.0)
            ),
            goals=list(
                data.get("goals", [])
            ),
            personality=personality,
            knowledge=knowledge,
            memories=memories,
            decisions_made=int(
                data.get("decisions_made", 0)
            ),
            successful_decisions=int(
                data.get("successful_decisions", 0)
            ),
            failed_decisions=int(
                data.get("failed_decisions", 0)
            ),
            experience=float(
                data.get("experience", 0.0)
            ),
            alive=bool(
                data.get("alive", True)
            ),
            generation=int(
                data.get("generation", 1)
            ),
            family_id=data.get(
                "family_id"
            ),
            created_world_date=data[
                "created_world_date"
            ],
            last_update_world_date=data[
                "last_update_world_date"
            ],
            total_ticks_processed=int(
                data.get(
                    "total_ticks_processed",
                    0,
                )
            ),
            research_role=data.get("research_role", "GENERALIST"),
            research_focus=data.get("research_focus"),
            evidence_collected=int(data.get("evidence_collected", 0)),
            hypotheses_proposed=int(data.get("hypotheses_proposed", 0)),
            hypotheses_challenged=int(data.get("hypotheses_challenged", 0)),
            validated_predictions=int(data.get("validated_predictions", 0)),
            prediction_accuracy=float(data.get("prediction_accuracy", 0.0)),
        )

    def save(self) -> None:

        payload = {
            "engine_name": self.ENGINE_NAME,
            "engine_version": self.ENGINE_VERSION,
            "updated_at": datetime.now().isoformat(),
            "agents": [
                self._serialize_agent(agent)
                for agent in self.agents.values()
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

            self.agents = {}

            for data in payload.get(
                "agents",
                [],
            ):

                agent = self._deserialize_agent(
                    data
                )

                self.agents[
                    agent.agent_id
                ] = agent

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):

            self.agents = {}

    def reset(self) -> None:

        self.agents = {}

        if self.state_file.exists():
            self.state_file.unlink()


# ============================================================
# TESTE DIRECTO
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("ATHENA WORLD - AGENT ENGINE")
    print("=" * 70)

    engine = AgentEngine()

    # Para o teste ficar limpo e repetível.
    engine.reset()

    agent = engine.create_agent(
        world_date="2026-10-04",
        first_name="Alex",
        last_name="Pereira",
        age=32,
        gender="M",
        profession="Engenheiro",
        primary_company_id="COMPANY-TEST",
        capital=25000.0,
        income=2083.20,
        expenses=1551.98,
    )

    print(
        f"Agent ID       : {agent.agent_id}"
    )

    print(
        f"Name           : "
        f"{agent.first_name} "
        f"{agent.last_name}"
    )

    print(
        f"Birth Date     : "
        f"{agent.birth_date}"
    )

    print(
        f"Age            : "
        f"{agent.age}"
    )

    print(
        f"Profession     : "
        f"{agent.profession}"
    )

    print(
        f"Capital        : "
        f"{agent.capital:.2f}"
    )

    print(
        f"Income mensal  : "
        f"{agent.income:.2f}"
    )

    print(
        f"Expenses mensal: "
        f"{agent.expenses:.2f}"
    )

    print(
        f"Experience     : "
        f"{agent.experience:.4f}"
    )

    print(
        f"Knowledge Tech : "
        f"{agent.knowledge.technology:.4f}"
    )

    print(
        f"Memories       : "
        f"{len(agent.memories)}"
    )

    print(
        f"Ticks          : "
        f"{agent.total_ticks_processed}"
    )

    print()
    print("A PROCESSAR 30 TICKS...")
    print()

    current_date = date.fromisoformat(
        "2026-10-04"
    )

    for _ in range(30):

        current_date += timedelta(days=1)

        engine.process_tick(
            world_date=current_date.isoformat()
        )

    agent = engine.get_agent(
        agent.agent_id
    )

    print("=" * 70)
    print("APÓS 30 TICKS")
    print("-" * 70)

    print(
        f"Data           : "
        f"{agent.last_update_world_date}"
    )

    print(
        f"Age            : "
        f"{agent.age}"
    )

    print(
        f"Capital        : "
        f"{agent.capital:.2f}"
    )

    print(
        f"Income mensal  : "
        f"{agent.income:.2f}"
    )

    print(
        f"Expenses mensal: "
        f"{agent.expenses:.2f}"
    )

    print(
        f"Experiência    : "
        f"{agent.experience:.4f}"
    )

    print(
        f"Technology     : "
        f"{agent.knowledge.technology:.4f}"
    )

    print(
        f"Economics      : "
        f"{agent.knowledge.economics:.4f}"
    )

    print(
        f"Finance        : "
        f"{agent.knowledge.finance:.4f}"
    )

    print(
        f"General        : "
        f"{agent.knowledge.general:.4f}"
    )

    print(
        f"Memories       : "
        f"{len(agent.memories)}"
    )

    print(
        f"Ticks          : "
        f"{agent.total_ticks_processed}"
    )

    print(
        f"Alive          : "
        f"{agent.alive}"
    )

    print("=" * 70)

    print()
    print(
        "ATHENA WORLD - AGENT ENGINE V02 "
        "carregado com sucesso."
    )
    print("=" * 70)