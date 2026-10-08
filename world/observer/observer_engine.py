from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "observer_state.json"

ENGINE_NAME = "ATHENA WORLD - WORLD OBSERVER ENGINE"
ENGINE_VERSION = "V01"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


@dataclass
class Observation:
    observation_id: str
    world_date: str
    tick: int
    source_engine: str
    subject_id: str
    subject_type: str
    metric: str
    value: float
    previous_value: Optional[float] = None
    change: float = 0.0
    change_rate: float = 0.0
    created_at: str = field(default_factory=now_iso)


@dataclass
class Anomaly:
    anomaly_id: str
    world_date: str
    tick: int
    source_engine: str
    subject_id: str
    metric: str
    observed_value: float
    expected_value: float
    deviation: float
    threshold: float
    severity: float
    description: str
    active: bool = True
    created_at: str = field(default_factory=now_iso)


@dataclass
class Pattern:
    pattern_id: str
    world_date: str
    tick: int
    name: str
    description: str
    source_engines: List[str]
    subjects: List[str]
    observations: List[str]
    confidence: float
    strength: float
    status: str = "OPEN"
    created_at: str = field(default_factory=now_iso)


@dataclass
class Relationship:
    relationship_id: str
    world_date: str
    tick: int
    source_subject: str
    source_metric: str
    target_subject: str
    target_metric: str
    relationship_type: str
    strength: float
    confidence: float
    observations: List[str]
    description: str
    created_at: str = field(default_factory=now_iso)


@dataclass
class Signal:
    signal_id: str
    world_date: str
    tick: int
    signal_type: str
    source_engine: str
    subject_id: str
    metric: str
    strength: float
    confidence: float
    description: str
    followed_by_event: bool = False
    created_at: str = field(default_factory=now_iso)


@dataclass
class Hypothesis:
    hypothesis_id: str
    world_date: str
    tick: int
    statement: str
    supporting_observations: List[str]
    contradicting_observations: List[str]
    confidence: float
    status: str
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class ObserverState:
    world_date: str
    tick: int = 0
    total_ticks: int = 0

    observations: Dict[str, Observation] = field(default_factory=dict)
    anomalies: Dict[str, Anomaly] = field(default_factory=dict)
    patterns: Dict[str, Pattern] = field(default_factory=dict)
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    signals: Dict[str, Signal] = field(default_factory=dict)
    hypotheses: Dict[str, Hypothesis] = field(default_factory=dict)

    total_observations: int = 0
    total_anomalies: int = 0
    total_patterns: int = 0
    total_relationships: int = 0
    total_signals: int = 0
    total_hypotheses: int = 0

    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


class ObserverEngine:

    def __init__(
        self,
        world_date: Optional[str] = None,
        tick: int = 0,
        state_file: Optional[Path] = None,
    ):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.state_file = state_file or STATE_FILE

        if world_date is None:
            world_date = date.today().isoformat()

        self.state = ObserverState(
            world_date=world_date,
            tick=tick,
        )

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def initialize(
        self,
        world_date: Optional[str] = None,
        tick: int = 0,
    ) -> None:
        if world_date is None:
            world_date = date.today().isoformat()

        self.state = ObserverState(
            world_date=world_date,
            tick=tick,
        )

        self.save()

    # ==========================================================
    # OBSERVATIONS
    # ==========================================================

    def observe(
        self,
        source_engine: str,
        subject_id: str,
        subject_type: str,
        metric: str,
        value: float,
        previous_value: Optional[float] = None,
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> Observation:

        if world_date is None:
            world_date = self.state.world_date

        if tick is None:
            tick = self.state.tick

        value = float(value)

        change = 0.0
        change_rate = 0.0

        if previous_value is not None:
            previous_value = float(previous_value)
            change = value - previous_value

            if previous_value != 0:
                change_rate = change / abs(previous_value)

        observation = Observation(
            observation_id=new_id("OBS"),
            world_date=world_date,
            tick=tick,
            source_engine=source_engine,
            subject_id=subject_id,
            subject_type=subject_type,
            metric=metric,
            value=value,
            previous_value=previous_value,
            change=change,
            change_rate=change_rate,
        )

        self.state.observations[observation.observation_id] = observation
        self.state.total_observations = len(self.state.observations)

        self._touch()
        self.save()

        return observation

    # ==========================================================
    # ==========================================================
    # INGESTÃO NORMALIZADA
    # ==========================================================

    def ingest(
        self,
        source_engine: str,
        subject_id: str,
        subject_type: str,
        metric: str,
        value: float,
        previous_value: Optional[float] = None,
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> Observation:
        """Entrada única para dados normalizados vindos de outros engines."""
        return self.observe(
            source_engine=source_engine,
            subject_id=subject_id,
            subject_type=subject_type,
            metric=metric,
            value=value,
            previous_value=previous_value,
            world_date=world_date,
            tick=tick,
        )

    def ingest_batch(
        self,
        observations: List[Dict],
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> List[Observation]:
        """Ingere várias observações normalizadas."""
        return [
            self.ingest(
                source_engine=item["source_engine"],
                subject_id=item["subject_id"],
                subject_type=item["subject_type"],
                metric=item["metric"],
                value=item["value"],
                previous_value=item.get("previous_value"),
                world_date=world_date,
                tick=tick,
            )
            for item in observations
        ]

    # ANOMALIES
    # ==========================================================

    def detect_anomaly(
        self,
        observation: Observation,
        expected_value: float,
        threshold: float = 0.20,
        description: Optional[str] = None,
    ) -> Optional[Anomaly]:

        expected_value = float(expected_value)
        observed_value = float(observation.value)
        threshold = abs(float(threshold))

        if expected_value == 0:
            deviation = abs(observed_value)
        else:
            deviation = abs(
                observed_value - expected_value
            ) / abs(expected_value)

        if deviation < threshold:
            return None

        severity = min(1.0, deviation)

        if description is None:
            description = (
                f"{observation.metric} desviou "
                f"{deviation:.2%} do valor esperado."
            )

        anomaly = Anomaly(
            anomaly_id=new_id("ANOM"),
            world_date=observation.world_date,
            tick=observation.tick,
            source_engine=observation.source_engine,
            subject_id=observation.subject_id,
            metric=observation.metric,
            observed_value=observed_value,
            expected_value=expected_value,
            deviation=deviation,
            threshold=threshold,
            severity=severity,
            description=description,
        )

        self.state.anomalies[anomaly.anomaly_id] = anomaly
        self.state.total_anomalies = len(self.state.anomalies)

        self._touch()
        self.save()

        return anomaly

    # ==========================================================
    # PATTERNS
    # ==========================================================

    def record_pattern(
        self,
        name: str,
        description: str,
        source_engines: List[str],
        subjects: List[str],
        observations: List[str],
        confidence: float,
        strength: float,
        status: str = "OPEN",
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> Pattern:

        if world_date is None:
            world_date = self.state.world_date

        if tick is None:
            tick = self.state.tick

        pattern = Pattern(
            pattern_id=new_id("PAT"),
            world_date=world_date,
            tick=tick,
            name=name,
            description=description,
            source_engines=list(source_engines),
            subjects=list(subjects),
            observations=list(observations),
            confidence=max(0.0, min(1.0, float(confidence))),
            strength=max(0.0, min(1.0, float(strength))),
            status=status,
        )

        self.state.patterns[pattern.pattern_id] = pattern
        self.state.total_patterns = len(self.state.patterns)

        self._touch()
        self.save()

        return pattern

    # ==========================================================
    # RELATIONSHIPS
    # ==========================================================

    def record_relationship(
        self,
        source_subject: str,
        source_metric: str,
        target_subject: str,
        target_metric: str,
        relationship_type: str,
        strength: float,
        confidence: float,
        observations: List[str],
        description: str,
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> Relationship:

        if world_date is None:
            world_date = self.state.world_date

        if tick is None:
            tick = self.state.tick

        relationship = Relationship(
            relationship_id=new_id("REL"),
            world_date=world_date,
            tick=tick,
            source_subject=source_subject,
            source_metric=source_metric,
            target_subject=target_subject,
            target_metric=target_metric,
            relationship_type=relationship_type,
            strength=max(0.0, min(1.0, float(strength))),
            confidence=max(0.0, min(1.0, float(confidence))),
            observations=list(observations),
            description=description,
        )

        self.state.relationships[relationship.relationship_id] = relationship
        self.state.total_relationships = len(self.state.relationships)

        self._touch()
        self.save()

        return relationship

    # ==========================================================
    # SIGNALS
    # ==========================================================

    def record_signal(
        self,
        signal_type: str,
        source_engine: str,
        subject_id: str,
        metric: str,
        strength: float,
        confidence: float,
        description: str,
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> Signal:

        if world_date is None:
            world_date = self.state.world_date

        if tick is None:
            tick = self.state.tick

        signal = Signal(
            signal_id=new_id("SIG"),
            world_date=world_date,
            tick=tick,
            signal_type=signal_type,
            source_engine=source_engine,
            subject_id=subject_id,
            metric=metric,
            strength=max(0.0, min(1.0, float(strength))),
            confidence=max(0.0, min(1.0, float(confidence))),
            description=description,
        )

        self.state.signals[signal.signal_id] = signal
        self.state.total_signals = len(self.state.signals)

        self._touch()
        self.save()

        return signal

    def mark_signal_followed_by_event(
        self,
        signal_id: str,
    ) -> Optional[Signal]:

        signal = self.state.signals.get(signal_id)

        if signal is None:
            return None

        signal.followed_by_event = True

        self._touch()
        self.save()

        return signal

    # ==========================================================
    # HYPOTHESES
    # ==========================================================

    def create_hypothesis(
        self,
        statement: str,
        confidence: float = 0.50,
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> Hypothesis:

        if world_date is None:
            world_date = self.state.world_date

        if tick is None:
            tick = self.state.tick

        hypothesis = Hypothesis(
            hypothesis_id=new_id("HYP"),
            world_date=world_date,
            tick=tick,
            statement=statement,
            supporting_observations=[],
            contradicting_observations=[],
            confidence=max(0.0, min(1.0, float(confidence))),
            status="OPEN",
        )

        self.state.hypotheses[hypothesis.hypothesis_id] = hypothesis
        self.state.total_hypotheses = len(self.state.hypotheses)

        self._touch()
        self.save()

        return hypothesis

    def update_hypothesis(
        self,
        hypothesis_id: str,
        supporting_observation: Optional[str] = None,
        contradicting_observation: Optional[str] = None,
    ) -> Optional[Hypothesis]:

        hypothesis = self.state.hypotheses.get(hypothesis_id)

        if hypothesis is None:
            return None

        if (
            supporting_observation
            and supporting_observation
            not in hypothesis.supporting_observations
        ):
            hypothesis.supporting_observations.append(
                supporting_observation
            )

        if (
            contradicting_observation
            and contradicting_observation
            not in hypothesis.contradicting_observations
        ):
            hypothesis.contradicting_observations.append(
                contradicting_observation
            )

        supports = len(hypothesis.supporting_observations)
        contradictions = len(
            hypothesis.contradicting_observations
        )

        total_evidence = supports + contradictions

        # ------------------------------------------------------
        # A hipótese só pode ser SUPPORTED com pelo menos
        # 3 evidências favoráveis.
        #
        # Antes disso, a confiança fica limitada para evitar
        # uma falsa aparência de certeza.
        # ------------------------------------------------------

        if supports >= 3 and contradictions == 0:
            hypothesis.status = "SUPPORTED"

        elif contradictions >= 3 and supports == 0:
            hypothesis.status = "CONTRADICTED"

        elif contradictions > supports and contradictions >= 2:
            hypothesis.status = "WEAKENED"

        else:
            hypothesis.status = "OPEN"

        if total_evidence == 0:
            hypothesis.confidence = 0.50

        else:
            evidence_ratio = supports / total_evidence

            if hypothesis.status == "SUPPORTED":
                hypothesis.confidence = min(
                    0.95,
                    0.50 + (0.15 * supports),
                )

            elif hypothesis.status == "CONTRADICTED":
                hypothesis.confidence = max(
                    0.05,
                    0.50 - (0.15 * contradictions),
                )

            else:
                # Hipótese ainda aberta:
                # máximo de 80% mesmo que todas as evidências
                # disponíveis sejam favoráveis.
                hypothesis.confidence = min(
                    0.80,
                    0.50 + (0.15 * evidence_ratio),
                )

        hypothesis.updated_at = now_iso()

        self._touch()
        self.save()

        return hypothesis

    # ==========================================================
    # TICK
    # ==========================================================

    def process_tick(
        self,
        world_date: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> ObserverState:

        if world_date is None:
            try:
                current_date = date.fromisoformat(
                    self.state.world_date
                )
                world_date = (
                    current_date + timedelta(days=1)
                ).isoformat()
            except ValueError:
                world_date = self.state.world_date

        if tick is None:
            tick = self.state.tick + 1

        self.state.world_date = world_date
        self.state.tick = tick
        self.state.total_ticks += 1

        self._touch()
        self.save()

        return self.state

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_observation(
        self,
        observation_id: str,
    ) -> Optional[Observation]:
        return self.state.observations.get(observation_id)

    def get_anomaly(
        self,
        anomaly_id: str,
    ) -> Optional[Anomaly]:
        return self.state.anomalies.get(anomaly_id)

    def get_pattern(
        self,
        pattern_id: str,
    ) -> Optional[Pattern]:
        return self.state.patterns.get(pattern_id)

    def get_relationship(
        self,
        relationship_id: str,
    ) -> Optional[Relationship]:
        return self.state.relationships.get(relationship_id)

    def get_signal(
        self,
        signal_id: str,
    ) -> Optional[Signal]:
        return self.state.signals.get(signal_id)

    def get_hypothesis(
        self,
        hypothesis_id: str,
    ) -> Optional[Hypothesis]:
        return self.state.hypotheses.get(hypothesis_id)

    def get_all_observations(self) -> List[Observation]:
        return list(self.state.observations.values())

    def get_all_anomalies(self) -> List[Anomaly]:
        return list(self.state.anomalies.values())

    def get_all_patterns(self) -> List[Pattern]:
        return list(self.state.patterns.values())

    def get_all_relationships(self) -> List[Relationship]:
        return list(self.state.relationships.values())

    def get_all_signals(self) -> List[Signal]:
        return list(self.state.signals.values())

    def get_all_hypotheses(self) -> List[Hypothesis]:
        return list(self.state.hypotheses.values())

    # ==========================================================
    # AGGREGATES
    # ==========================================================

    def aggregates(self) -> Dict[str, int]:
        return {
            "observations": len(self.state.observations),
            "anomalies": len(self.state.anomalies),
            "patterns": len(self.state.patterns),
            "relationships": len(self.state.relationships),
            "signals": len(self.state.signals),
            "hypotheses": len(self.state.hypotheses),
        }

    # ==========================================================
    # PERSISTENCE
    # ==========================================================

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.state.updated_at = now_iso()

        payload = asdict(self.state)

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

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        self.state = ObserverState(
            world_date=data["world_date"],
            tick=data.get("tick", 0),
            total_ticks=data.get("total_ticks", 0),

            observations={
                key: Observation(**value)
                for key, value
                in data.get("observations", {}).items()
            },

            anomalies={
                key: Anomaly(**value)
                for key, value
                in data.get("anomalies", {}).items()
            },

            patterns={
                key: Pattern(**value)
                for key, value
                in data.get("patterns", {}).items()
            },

            relationships={
                key: Relationship(**value)
                for key, value
                in data.get("relationships", {}).items()
            },

            signals={
                key: Signal(**value)
                for key, value
                in data.get("signals", {}).items()
            },

            hypotheses={
                key: Hypothesis(**value)
                for key, value
                in data.get("hypotheses", {}).items()
            },

            total_observations=data.get(
                "total_observations",
                len(data.get("observations", {})),
            ),

            total_anomalies=data.get(
                "total_anomalies",
                len(data.get("anomalies", {})),
            ),

            total_patterns=data.get(
                "total_patterns",
                len(data.get("patterns", {})),
            ),

            total_relationships=data.get(
                "total_relationships",
                len(data.get("relationships", {})),
            ),

            total_signals=data.get(
                "total_signals",
                len(data.get("signals", {})),
            ),

            total_hypotheses=data.get(
                "total_hypotheses",
                len(data.get("hypotheses", {})),
            ),

            created_at=data.get(
                "created_at",
                now_iso(),
            ),

            updated_at=data.get(
                "updated_at",
                now_iso(),
            ),

            engine_name=data.get(
                "engine_name",
                ENGINE_NAME,
            ),

            engine_version=data.get(
                "engine_version",
                ENGINE_VERSION,
            ),
        )

    def reset(self) -> None:
        self.state = ObserverState(
            world_date=date.today().isoformat(),
            tick=0,
        )

        self.save()

    # ==========================================================
    # INTERNAL
    # ==========================================================

    def _touch(self) -> None:
        self.state.updated_at = now_iso()


# ==============================================================
# TESTE DO ENGINE
# ==============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(ENGINE_NAME)
    print(ENGINE_VERSION)
    print("=" * 60)

    observer = ObserverEngine(
        world_date="2026-10-28",
        tick=0,
    )

    observer.reset()

    # ----------------------------------------------------------
    # OBSERVAÇÕES
    # ----------------------------------------------------------

    economy_observation = observer.observe(
        source_engine="ECONOMY",
        subject_id="WORLD",
        subject_type="WORLD",
        metric="GDP",
        value=120.0,
        previous_value=100.0,
    )

    market_observation = observer.observe(
        source_engine="MARKET",
        subject_id="ASSET-001",
        subject_type="ASSET",
        metric="PRICE",
        value=150.0,
        previous_value=100.0,
    )

    # ----------------------------------------------------------
    # ANOMALIA
    # ----------------------------------------------------------

    anomaly = observer.detect_anomaly(
        observation=market_observation,
        expected_value=100.0,
        threshold=0.20,
        description="Preço do ativo muito acima do valor esperado.",
    )

    # ----------------------------------------------------------
    # PADRÃO
    # ----------------------------------------------------------

    pattern = observer.record_pattern(
        name="Aceleração Económica",
        description=(
            "A aceleração do PIB coincide com aumento "
            "significativo do preço do ativo."
        ),
        source_engines=["ECONOMY", "MARKET"],
        subjects=["WORLD", "ASSET-001"],
        observations=[
            economy_observation.observation_id,
            market_observation.observation_id,
        ],
        confidence=0.75,
        strength=0.80,
    )

    # ----------------------------------------------------------
    # RELAÇÃO
    # ----------------------------------------------------------

    relationship = observer.record_relationship(
        source_subject="WORLD",
        source_metric="GDP",
        target_subject="ASSET-001",
        target_metric="PRICE",
        relationship_type="POSITIVE",
        strength=0.70,
        confidence=0.65,
        observations=[
            economy_observation.observation_id,
            market_observation.observation_id,
        ],
        description=(
            "Aumento do PIB associado a aumento "
            "do preço do ativo."
        ),
    )

    # ----------------------------------------------------------
    # SINAL
    # ----------------------------------------------------------

    signal = observer.record_signal(
        signal_type="PRE_EVENT",
        source_engine="OBSERVER",
        subject_id="ASSET-001",
        metric="PRICE",
        strength=0.80,
        confidence=0.70,
        description=(
            "Movimento anormal do ativo associado "
            "a aceleração económica."
        ),
    )

    # ----------------------------------------------------------
    # HIPÓTESE
    # ----------------------------------------------------------

    hypothesis = observer.create_hypothesis(
        statement=(
            "A aceleração económica pode preceder "
            "um aumento sustentado de determinados ativos."
        ),
        confidence=0.50,
    )

    observer.update_hypothesis(
        hypothesis.hypothesis_id,
        supporting_observation=economy_observation.observation_id,
    )

    observer.update_hypothesis(
        hypothesis.hypothesis_id,
        supporting_observation=market_observation.observation_id,
    )

    # ----------------------------------------------------------
    # RESULTADOS
    # ----------------------------------------------------------

    print()
    print("OBSERVAÇÕES")
    print(f"Total         : {len(observer.state.observations)}")
    print(f"Anomalias     : {len(observer.state.anomalies)}")
    print(f"Padrões       : {len(observer.state.patterns)}")
    print(f"Relações      : {len(observer.state.relationships)}")
    print(f"Sinais        : {len(observer.state.signals)}")
    print(f"Hipóteses     : {len(observer.state.hypotheses)}")

    if anomaly:
        print()
        print("ANOMALIA")
        print(f"Métrica       : {anomaly.metric}")
        print(f"Observado     : {anomaly.observed_value:.2f}")
        print(f"Esperado      : {anomaly.expected_value:.2f}")
        print(f"Desvio        : {anomaly.deviation:.2%}")
        print(f"Severidade    : {anomaly.severity:.2%}")

    print()
    print("PADRÃO")
    print(f"Nome          : {pattern.name}")
    print(f"Confiança     : {pattern.confidence:.2%}")
    print(f"Força         : {pattern.strength:.2%}")

    print()
    print("RELAÇÃO")
    print(f"Tipo          : {relationship.relationship_type}")
    print(f"Força         : {relationship.strength:.2%}")
    print(f"Confiança     : {relationship.confidence:.2%}")

    print()
    print("SINAL")
    print(f"Tipo          : {signal.signal_type}")
    print(f"Força         : {signal.strength:.2%}")
    print(f"Confiança     : {signal.confidence:.2%}")

    print()
    print("HIPÓTESE")
    print(f"Estado        : {hypothesis.status}")
    print(f"Confiança     : {hypothesis.confidence:.2%}")
    print(
        f"Evidências    : "
        f"{len(hypothesis.supporting_observations)} favoráveis / "
        f"{len(hypothesis.contradicting_observations)} contraditórias"
    )

    # ----------------------------------------------------------
    # TICK
    # ----------------------------------------------------------

    observer.process_tick()

    print()
    print("APÓS 1 TICK")
    print(f"Tick          : {observer.state.tick}")
    print(f"Data          : {observer.state.world_date}")

    print()
    print("WORLD OBSERVER ENGINE V01 TESTE CONCLUIDO")
    print("=" * 60)