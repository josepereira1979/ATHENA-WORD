from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD
# LEARNING ENGINE V01
# ============================================================
#
# Responsabilidade:
#   - experiências
#   - sucessos
#   - falhas
#   - aprendizagem individual
#   - aprendizagem empresarial
#   - aprendizagem familiar
#   - estratégias
#   - descobertas
#   - transferência de conhecimento
#   - evolução do conhecimento
#   - aprendizagem intergeracional
#
# O Learning Engine regista aquilo que o mundo aprende.
#
# NÃO controla diretamente:
#   - agentes
#   - famílias
#   - empresas
#   - economia
#   - mercados
#
# Os outros motores fornecem experiências e recebem
# conhecimento através das suas próprias interfaces.
#
# ============================================================


ENGINE_NAME = "ATHENA WORLD - LEARNING ENGINE"
ENGINE_VERSION = "V01"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "learning_state.json"


# ============================================================
# EXPERIÊNCIA
# ============================================================


@dataclass
class Experience:
    experience_id: str

    owner_id: str
    owner_type: str

    world_date: str

    event_type: str
    description: str

    outcome: str

    success: Optional[bool]

    impact: float = 0.0

    learning_value: float = 0.0

    knowledge_domain: str = "GENERAL"

    strategy: str = ""

    lesson: str = ""

    created_at: str = ""


# ============================================================
# CONHECIMENTO
# ============================================================


@dataclass
class KnowledgeRecord:
    knowledge_id: str

    owner_id: str
    owner_type: str

    domain: str

    level: float = 0.0

    experience_count: int = 0

    successful_experiences: int = 0
    failed_experiences: int = 0

    discoveries: int = 0

    inherited: int = 0
    transferred: int = 0

    last_learning_date: str = ""

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# ESTRATÉGIA
# ============================================================


@dataclass
class Strategy:
    strategy_id: str

    owner_id: str
    owner_type: str

    name: str
    description: str

    domain: str

    effectiveness: float = 0.5

    uses: int = 0
    successes: int = 0
    failures: int = 0

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# DESCOBERTA
# ============================================================


@dataclass
class Discovery:
    discovery_id: str

    owner_id: str
    owner_type: str

    world_date: str

    domain: str

    name: str
    description: str

    importance: float = 0.5

    adopted: bool = False

    created_at: str = ""


# ============================================================
# ESTADO
# ============================================================


@dataclass
class LearningState:
    world_date: str

    tick: int = 0
    total_ticks: int = 0

    experiences: Dict[str, Experience] = field(
        default_factory=dict
    )

    knowledge: Dict[str, KnowledgeRecord] = field(
        default_factory=dict
    )

    strategies: Dict[str, Strategy] = field(
        default_factory=dict
    )

    discoveries: Dict[str, Discovery] = field(
        default_factory=dict
    )

    total_experiences: int = 0
    total_knowledge_records: int = 0
    total_strategies: int = 0
    total_discoveries: int = 0

    total_successes: int = 0
    total_failures: int = 0

    total_knowledge_transfers: int = 0
    total_inherited_knowledge: int = 0

    created_at: str = ""
    updated_at: str = ""

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


# ============================================================
# LEARNING ENGINE
# ============================================================


class LearningEngine:

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

        self.state: Optional[LearningState] = None

    # ========================================================
    # UTILIDADES
    # ========================================================

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat()

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:

        return max(
            minimum,
            min(maximum, float(value)),
        )

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def initialize(
        self,
        world_date: str,
    ) -> LearningState:

        now = self._now()

        self.state = LearningState(
            world_date=world_date,
            created_at=now,
            updated_at=now,
        )

        self._save()

        return self.state

    # ========================================================
    # EXPERIÊNCIA
    # ========================================================

    def record_experience(
        self,
        owner_id: str,
        owner_type: str,
        world_date: str,
        event_type: str,
        description: str,
        outcome: str,
        success: Optional[bool],
        impact: float = 0.0,
        learning_value: float = 0.1,
        knowledge_domain: str = "GENERAL",
        strategy: str = "",
        lesson: str = "",
    ) -> Experience:

        self._require_state()

        experience_id = (
            "EXP-"
            + uuid.uuid4().hex[:12].upper()
        )

        experience = Experience(
            experience_id=experience_id,
            owner_id=owner_id,
            owner_type=owner_type.upper(),
            world_date=world_date,
            event_type=event_type,
            description=description,
            outcome=outcome,
            success=(None if success is None else bool(success)),
            impact=self._clamp(
                impact,
                -1.0,
                1.0,
            ),
            learning_value=self._clamp(
                learning_value
            ),
            knowledge_domain=(
                knowledge_domain.upper()
            ),
            strategy=strategy,
            lesson=lesson,
            created_at=self._now(),
        )

        self.state.experiences[
            experience_id
        ] = experience

        if experience.success is True:
            self.state.total_successes += 1
        elif experience.success is False:
            self.state.total_failures += 1

        self._learn_from_experience(
            experience
        )

        self._refresh_aggregates()
        self._touch()
        self._save()

        return experience

    # ========================================================
    # APRENDER COM EXPERIÊNCIA
    # ========================================================

    def _learn_from_experience(
        self,
        experience: Experience,
    ) -> None:

        knowledge_id = self._knowledge_key(
            experience.owner_id,
            experience.owner_type,
            experience.knowledge_domain,
        )

        record = self.state.knowledge.get(
            knowledge_id
        )

        if record is None:

            now = self._now()

            record = KnowledgeRecord(
                knowledge_id=knowledge_id,
                owner_id=experience.owner_id,
                owner_type=experience.owner_type,
                domain=experience.knowledge_domain,
                level=0.0,
                experience_count=0,
                successful_experiences=0,
                failed_experiences=0,
                discoveries=0,
                inherited=0,
                transferred=0,
                last_learning_date=(
                    experience.world_date
                ),
                created_at=now,
                updated_at=now,
            )

            self.state.knowledge[
                knowledge_id
            ] = record

        record.experience_count += 1

        if experience.success is True:
            record.successful_experiences += 1
        elif experience.success is False:
            record.failed_experiences += 1

        gain = (
            experience.learning_value
            * (
                1.0
                + abs(experience.impact)
            )
        )

        # Falhas também ensinam.
        # Uma falha não significa ausência de aprendizagem.
        if experience.success is False:
            gain *= 1.15

        record.level = self._clamp(
            record.level + gain
        )

        record.last_learning_date = (
            experience.world_date
        )

        record.updated_at = self._now()

        # Se uma estratégia foi indicada,
        # atualiza a sua eficácia.
        if experience.strategy:

            self._update_strategy_from_experience(
                owner_id=experience.owner_id,
                owner_type=experience.owner_type,
                strategy_name=experience.strategy,
                domain=experience.knowledge_domain,
                success=experience.success,
            )

    def learn_from_prediction(
        self,
        prediction,
        world_date: Optional[str] = None,
    ) -> Optional[Experience]:
        """Converte uma previsão validada numa experiência de aprendizagem."""
        self._require_state()
        if prediction is None or prediction.status != "VALIDATED":
            return None
        if prediction.outcome not in {"CORRECT", "WRONG", "PARTIAL"}:
            return None

        learning_value = {
            "CORRECT": 0.10,
            "PARTIAL": 0.08,
            "WRONG": 0.12,
        }[prediction.outcome]

        impact = {
            "CORRECT": 0.50,
            "PARTIAL": 0.20,
            "WRONG": -0.50,
        }[prediction.outcome]

        success = prediction.outcome == "CORRECT"
        date_value = world_date or prediction.actual_date or prediction.horizon_end
        lesson = {
            "CORRECT": "A hipótese e a previsão mostraram capacidade preditiva.",
            "PARTIAL": "A direção ou magnitude aproximou-se da realidade, mas a previsão precisa de calibração.",
            "WRONG": "A previsão falhou; o erro deve alimentar a aprendizagem e revisão da hipótese.",
        }[prediction.outcome]

        return self.record_experience(
            owner_id=prediction.owner_id,
            owner_type=prediction.owner_type,
            world_date=date_value,
            event_type="PREDICTION_VALIDATION",
            description=prediction.statement,
            outcome=prediction.outcome,
            success=success,
            impact=impact,
            learning_value=learning_value,
            knowledge_domain=prediction.metric,
            strategy="",
            lesson=lesson,
        )

    # ========================================================
    # ESTRATÉGIAS
    # ========================================================

    def create_strategy(
        self,
        owner_id: str,
        owner_type: str,
        name: str,
        description: str,
        domain: str = "GENERAL",
        effectiveness: float = 0.5,
    ) -> Strategy:

        self._require_state()

        strategy_id = (
            "STRAT-"
            + uuid.uuid4().hex[:12].upper()
        )

        now = self._now()

        strategy = Strategy(
            strategy_id=strategy_id,
            owner_id=owner_id,
            owner_type=owner_type.upper(),
            name=name,
            description=description,
            domain=domain.upper(),
            effectiveness=self._clamp(
                effectiveness
            ),
            created_at=now,
            updated_at=now,
        )

        self.state.strategies[
            strategy_id
        ] = strategy

        self._refresh_aggregates()
        self._touch()
        self._save()

        return strategy

    def _find_strategy(
        self,
        owner_id: str,
        owner_type: str,
        name: str,
    ) -> Optional[Strategy]:

        for strategy in (
            self.state.strategies.values()
        ):

            if (
                strategy.owner_id == owner_id
                and strategy.owner_type
                == owner_type.upper()
                and strategy.name == name
                and strategy.active
            ):
                return strategy

        return None

    def _update_strategy_from_experience(
        self,
        owner_id: str,
        owner_type: str,
        strategy_name: str,
        domain: str,
        success: bool,
    ) -> Strategy:

        strategy = self._find_strategy(
            owner_id,
            owner_type,
            strategy_name,
        )

        if strategy is None:

            strategy = self.create_strategy(
                owner_id=owner_id,
                owner_type=owner_type,
                name=strategy_name,
                description=(
                    "Estratégia criada "
                    "a partir da experiência."
                ),
                domain=domain,
            )

        strategy.uses += 1

        if success:

            strategy.successes += 1

        else:

            strategy.failures += 1

        # A eficácia é baseada no histórico observado.
        strategy.effectiveness = (
            strategy.successes
            / strategy.uses
        )

        strategy.updated_at = self._now()

        return strategy

    # ========================================================
    # DESCOBERTAS
    # ========================================================

    def create_discovery(
        self,
        owner_id: str,
        owner_type: str,
        world_date: str,
        domain: str,
        name: str,
        description: str,
        importance: float = 0.5,
    ) -> Discovery:

        self._require_state()

        discovery_id = (
            "DISC-"
            + uuid.uuid4().hex[:12].upper()
        )

        discovery = Discovery(
            discovery_id=discovery_id,
            owner_id=owner_id,
            owner_type=owner_type.upper(),
            world_date=world_date,
            domain=domain.upper(),
            name=name,
            description=description,
            importance=self._clamp(
                importance
            ),
            adopted=False,
            created_at=self._now(),
        )

        self.state.discoveries[
            discovery_id
        ] = discovery

        knowledge_id = self._knowledge_key(
            owner_id,
            owner_type.upper(),
            domain.upper(),
        )

        record = self.state.knowledge.get(
            knowledge_id
        )

        if record is None:

            now = self._now()

            record = KnowledgeRecord(
                knowledge_id=knowledge_id,
                owner_id=owner_id,
                owner_type=owner_type.upper(),
                domain=domain.upper(),
                created_at=now,
                updated_at=now,
            )

            self.state.knowledge[
                knowledge_id
            ] = record

        record.discoveries += 1

        discovery_gain = (
            0.05
            * importance
        )

        record.level = self._clamp(
            record.level + discovery_gain
        )

        record.updated_at = self._now()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return discovery

    # ========================================================
    # TRANSFERÊNCIA DE CONHECIMENTO
    # ========================================================

    def transfer_knowledge(
        self,
        source_id: str,
        source_type: str,
        target_id: str,
        target_type: str,
        domain: str,
        amount: float = 0.10,
        inherited: bool = False,
    ) -> bool:

        self._require_state()

        amount = self._clamp(
            amount
        )

        source_key = self._knowledge_key(
            source_id,
            source_type.upper(),
            domain.upper(),
        )

        target_key = self._knowledge_key(
            target_id,
            target_type.upper(),
            domain.upper(),
        )

        source = self.state.knowledge.get(
            source_key
        )

        if source is None:
            return False

        if source.level <= 0:
            return False

        target = self.state.knowledge.get(
            target_key
        )

        if target is None:

            now = self._now()

            target = KnowledgeRecord(
                knowledge_id=target_key,
                owner_id=target_id,
                owner_type=target_type.upper(),
                domain=domain.upper(),
                created_at=now,
                updated_at=now,
            )

            self.state.knowledge[
                target_key
            ] = target

        transfer_amount = min(
            amount,
            source.level,
        )

        target.level = self._clamp(
            target.level + transfer_amount
        )

        target.transferred += 1

        if inherited:
            target.inherited += 1
            self.state.total_inherited_knowledge += 1
        else:
            self.state.total_knowledge_transfers += 1

        target.updated_at = self._now()

        self._refresh_aggregates()
        self._touch()
        self._save()

        return True

    # ========================================================
    # ADOTAR DESCOBERTA
    # ========================================================

    def adopt_discovery(
        self,
        discovery_id: str,
    ) -> bool:

        self._require_state()

        discovery = self.state.discoveries.get(
            discovery_id
        )

        if discovery is None:
            return False

        discovery.adopted = True

        knowledge_id = self._knowledge_key(
            discovery.owner_id,
            discovery.owner_type,
            discovery.domain,
        )

        record = self.state.knowledge.get(
            knowledge_id
        )

        if record is not None:

            record.level = self._clamp(
                record.level
                + (
                    0.05
                    * discovery.importance
                )
            )

            record.updated_at = self._now()

        self._touch()
        self._save()

        return True

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_knowledge(
        self,
        owner_id: str,
        owner_type: str,
        domain: str,
    ) -> Optional[KnowledgeRecord]:

        self._require_state()

        return self.state.knowledge.get(
            self._knowledge_key(
                owner_id,
                owner_type.upper(),
                domain.upper(),
            )
        )

    def get_owner_knowledge(
        self,
        owner_id: str,
        owner_type: str,
    ) -> List[KnowledgeRecord]:

        self._require_state()

        return [
            record
            for record
            in self.state.knowledge.values()
            if (
                record.owner_id == owner_id
                and record.owner_type
                == owner_type.upper()
            )
        ]

    def get_owner_experiences(
        self,
        owner_id: str,
        owner_type: str,
    ) -> List[Experience]:

        self._require_state()

        return [
            experience
            for experience
            in self.state.experiences.values()
            if (
                experience.owner_id == owner_id
                and experience.owner_type
                == owner_type.upper()
            )
        ]

    # ========================================================
    # TICK
    # ========================================================

    def learn_from_validated_predictions(self, predictions, world_date: Optional[str] = None) -> List[Experience]:
        self._require_state()
        existing = {e.description.split("PREDICTION_ID:", 1)[1].split("|", 1)[0] for e in self.state.experiences.values() if "PREDICTION_ID:" in e.description}
        learned = []
        for prediction in predictions or []:
            pid = getattr(prediction, "prediction_id", "")
            if not pid or pid in existing:
                continue
            exp = self.learn_from_prediction(prediction, world_date=world_date)
            if exp is not None:
                exp.description = f"PREDICTION_ID:{pid}|HYPOTHESIS_ID:{getattr(prediction, 'source_hypothesis_id', None)}|{exp.description}"
                self.state.experiences[exp.experience_id] = exp
                self._save()
                learned.append(exp)
                existing.add(pid)
        return learned

    def process_tick(
        self,
        world_date: str,
    ) -> LearningState:

        self._require_state()

        self.state.tick += 1
        self.state.total_ticks += 1
        self.state.world_date = world_date

        self._touch()
        self._save()

        return self.state

    # ========================================================
    # CHAVE DE CONHECIMENTO
    # ========================================================

    @staticmethod
    def _knowledge_key(
        owner_id: str,
        owner_type: str,
        domain: str,
    ) -> str:

        return (
            f"{owner_type.upper()}:"
            f"{owner_id}:"
            f"{domain.upper()}"
        )

    # ========================================================
    # AGREGADOS
    # ========================================================

    def _refresh_aggregates(
        self,
    ) -> None:

        if self.state is None:
            return

        self.state.total_experiences = len(
            self.state.experiences
        )

        self.state.total_knowledge_records = len(
            self.state.knowledge
        )

        self.state.total_strategies = len(
            self.state.strategies
        )

        self.state.total_discoveries = len(
            self.state.discoveries
        )

    # ========================================================
    # ESTADO
    # ========================================================

    def _require_state(
        self,
    ) -> None:

        if self.state is None:
            raise RuntimeError(
                "LearningEngine is not initialized."
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

        with self.state_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                asdict(self.state),
                file,
                ensure_ascii=False,
                indent=4,
            )

    def load(
        self,
    ) -> LearningState:

        if not self.state_file.exists():

            raise FileNotFoundError(
                "Learning state file not found: "
                f"{self.state_file}"
            )

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        data["experiences"] = {
            key: Experience(**value)
            for key, value
            in data.get(
                "experiences",
                {},
            ).items()
        }

        data["knowledge"] = {
            key: KnowledgeRecord(**value)
            for key, value
            in data.get(
                "knowledge",
                {},
            ).items()
        }

        data["strategies"] = {
            key: Strategy(**value)
            for key, value
            in data.get(
                "strategies",
                {},
            ).items()
        }

        data["discoveries"] = {
            key: Discovery(**value)
            for key, value
            in data.get(
                "discoveries",
                {},
            ).items()
        }

        self.state = LearningState(
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

    engine = LearningEngine()

    engine.initialize(
        world_date="2026-09-29"
    )

    # --------------------------------------------------------
    # ESTRATÉGIA
    # --------------------------------------------------------

    strategy = engine.create_strategy(
        owner_id="AGENT-001",
        owner_type="AGENT",
        name="Poupar antes de investir",
        description=(
            "Acumular capital antes de assumir "
            "novos investimentos."
        ),
        domain="FINANCE",
    )

    # --------------------------------------------------------
    # EXPERIÊNCIA DE SUCESSO
    # --------------------------------------------------------

    success = engine.record_experience(
        owner_id="AGENT-001",
        owner_type="AGENT",
        world_date="2026-10-01",
        event_type="INVESTMENT",
        description=(
            "O agente realizou um investimento "
            "após acumular capital."
        ),
        outcome="Retorno positivo.",
        success=True,
        impact=0.40,
        learning_value=0.10,
        knowledge_domain="FINANCE",
        strategy="Poupar antes de investir",
        lesson=(
            "Manter liquidez antes de investir "
            "reduziu o risco."
        ),
    )

    # --------------------------------------------------------
    # EXPERIÊNCIA DE FALHA
    # --------------------------------------------------------

    failure = engine.record_experience(
        owner_id="AGENT-001",
        owner_type="AGENT",
        world_date="2026-10-15",
        event_type="INVESTMENT",
        description=(
            "O agente realizou uma segunda "
            "operação sem analisar suficientemente "
            "o risco."
        ),
        outcome="Perda financeira.",
        success=False,
        impact=-0.50,
        learning_value=0.12,
        knowledge_domain="FINANCE",
        lesson=(
            "Decisões com pouca análise "
            "aumentaram o risco."
        ),
    )

    # --------------------------------------------------------
    # DESCOBERTA
    # --------------------------------------------------------

    discovery = engine.create_discovery(
        owner_id="AGENT-001",
        owner_type="AGENT",
        world_date="2026-10-20",
        domain="FINANCE",
        name="Importância da Liquidez",
        description=(
            "O agente descobre que manter liquidez "
            "permite aproveitar oportunidades."
        ),
        importance=0.80,
    )

    # --------------------------------------------------------
    # TRANSFERÊNCIA
    # --------------------------------------------------------

    transferred = engine.transfer_knowledge(
        source_id="AGENT-001",
        source_type="AGENT",
        target_id="AGENT-002",
        target_type="AGENT",
        domain="FINANCE",
        amount=0.10,
    )

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    knowledge = engine.get_knowledge(
        "AGENT-001",
        "AGENT",
        "FINANCE",
    )

    strategy_after = engine._find_strategy(
        "AGENT-001",
        "AGENT",
        "Poupar antes de investir",
    )

    print()
    print("RESULTADOS")
    print(
        "Experiências :",
        engine.state.total_experiences,
    )

    print(
        "Sucessos     :",
        engine.state.total_successes,
    )

    print(
        "Falhas       :",
        engine.state.total_failures,
    )

    print(
        "Conhecimento :",
        engine.state.total_knowledge_records,
    )

    print(
        "Estratégias  :",
        engine.state.total_strategies,
    )

    print(
        "Descobertas  :",
        engine.state.total_discoveries,
    )

    print()

    print("CONHECIMENTO AGENTE")

    if knowledge:

        print(
            "Domínio      :",
            knowledge.domain,
        )

        print(
            "Nível        :",
            f"{knowledge.level:.4f}",
        )

        print(
            "Experiências :",
            knowledge.experience_count,
        )

        print(
            "Sucessos     :",
            knowledge.successful_experiences,
        )

        print(
            "Falhas       :",
            knowledge.failed_experiences,
        )

        print(
            "Descobertas  :",
            knowledge.discoveries,
        )

    print()

    print("ESTRATÉGIA")

    if strategy_after:

        print(
            "Nome         :",
            strategy_after.name,
        )

        print(
            "Usos         :",
            strategy_after.uses,
        )

        print(
            "Sucessos     :",
            strategy_after.successes,
        )

        print(
            "Eficácia     :",
            f"{strategy_after.effectiveness:.2%}",
        )

    print()

    print(
        "Transferência:",
        transferred,
    )

    print(
        "Conhecimento transferido:",
        engine.state.total_knowledge_transfers,
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
        "Data          :",
        engine.state.world_date,
    )

    print()

    print(
        "LEARNING ENGINE V01 "
        "TESTE CONCLUIDO"
    )

    print("=" * 60)