from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "prediction_state.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


@dataclass
class Prediction:
    prediction_id: str
    owner_id: str
    owner_type: str
    subject_id: str
    subject_type: str
    metric: str
    statement: str
    predicted_value: Optional[float]
    predicted_direction: Optional[str]
    confidence: float
    horizon_start: str
    horizon_end: str
    invalidation_condition: Optional[str] = None
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    status: str = "OPEN"
    outcome: Optional[str] = None
    actual_value: Optional[float] = None
    actual_date: Optional[str] = None
    error: Optional[float] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


class PredictionEngine:
    """Regista previsões antes do resultado e valida-as contra a realidade.

    O motor não decide investimentos. Preserva a integridade temporal:
    uma previsão nasce OPEN e só recebe resultado quando existe observação
    posterior suficiente para a validar.
    """

    ENGINE_NAME = "ATHENA WORLD - PREDICTION ENGINE"
    ENGINE_VERSION = "V01"

    def __init__(self, state_file: Path = STATE_FILE, auto_load: bool = True):
        self.state_file = Path(state_file)
        self.predictions: Dict[str, Prediction] = {}
        if auto_load:
            self.load()

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def create_prediction(
        self,
        owner_id: str,
        owner_type: str,
        subject_id: str,
        subject_type: str,
        metric: str,
        statement: str,
        horizon_start: str,
        horizon_end: str,
        confidence: float = 0.50,
        predicted_value: Optional[float] = None,
        predicted_direction: Optional[str] = None,
        invalidation_condition: Optional[str] = None,
        supporting_evidence: Optional[List[str]] = None,
        contradicting_evidence: Optional[List[str]] = None,
    ) -> Prediction:
        if not owner_id or not subject_id or not metric or not statement:
            raise ValueError("owner_id, subject_id, metric e statement são obrigatórios.")
        if horizon_end < horizon_start:
            raise ValueError("horizon_end não pode ser anterior a horizon_start.")

        prediction = Prediction(
            prediction_id=new_id("PRED"),
            owner_id=owner_id,
            owner_type=owner_type.upper(),
            subject_id=subject_id,
            subject_type=subject_type.upper(),
            metric=metric,
            statement=statement,
            predicted_value=(
                float(predicted_value)
                if predicted_value is not None
                else None
            ),
            predicted_direction=(
                predicted_direction.upper()
                if predicted_direction
                else None
            ),
            confidence=self._clamp(confidence),
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            invalidation_condition=invalidation_condition,
            supporting_evidence=list(supporting_evidence or []),
            contradicting_evidence=list(contradicting_evidence or []),
        )
        self.predictions[prediction.prediction_id] = prediction
        self.save()
        return prediction

    def add_evidence(
        self,
        prediction_id: str,
        evidence_id: str,
        supporting: bool = True,
    ) -> bool:
        prediction = self.get_prediction(prediction_id)
        if prediction is None or not evidence_id:
            return False
        target = (
            prediction.supporting_evidence
            if supporting
            else prediction.contradicting_evidence
        )
        if evidence_id not in target:
            target.append(evidence_id)
        prediction.updated_at = now_iso()
        self.save()
        return True

    def validate_prediction(
        self,
        prediction_id: str,
        actual_value: float,
        actual_date: str,
        outcome: str,
    ) -> Optional[Prediction]:
        prediction = self.get_prediction(prediction_id)
        if prediction is None:
            return None
        if prediction.status != "OPEN":
            raise ValueError("A previsão já foi validada.")
        if actual_date < prediction.horizon_start:
            raise ValueError("A realidade usada para validação é anterior ao horizonte.")

        prediction.actual_value = float(actual_value)
        prediction.actual_date = actual_date
        prediction.outcome = outcome.upper()
        prediction.status = "VALIDATED"
        if prediction.predicted_value is not None:
            prediction.error = (
                prediction.actual_value - prediction.predicted_value
            )
        prediction.updated_at = now_iso()
        self.save()
        return prediction

    def close_expired(
        self,
        current_date: str,
        unresolved_outcome: str = "UNRESOLVED",
    ) -> int:
        changed = 0
        for prediction in self.predictions.values():
            if (
                prediction.status == "OPEN"
                and current_date > prediction.horizon_end
            ):
                prediction.status = "VALIDATED"
                prediction.outcome = unresolved_outcome.upper()
                prediction.updated_at = now_iso()
                changed += 1
        if changed:
            self.save()
        return changed

    def get_prediction(self, prediction_id: str) -> Optional[Prediction]:
        return self.predictions.get(prediction_id)

    def get_all_predictions(self) -> List[Prediction]:
        return list(self.predictions.values())

    def get_open_predictions(self) -> List[Prediction]:
        return [x for x in self.predictions.values() if x.status == "OPEN"]

    def get_predictions_by_owner(
        self,
        owner_id: str,
        owner_type: Optional[str] = None,
    ) -> List[Prediction]:
        owner_type_norm = owner_type.upper() if owner_type else None
        return [
            x for x in self.predictions.values()
            if x.owner_id == owner_id
            and (owner_type_norm is None or x.owner_type == owner_type_norm)
        ]

    def accuracy(self, owner_id: Optional[str] = None) -> Dict[str, float]:
        rows = self.get_all_predictions()
        if owner_id is not None:
            rows = [x for x in rows if x.owner_id == owner_id]
        validated = [
            x for x in rows
            if x.status == "VALIDATED" and x.outcome in {"CORRECT", "WRONG", "PARTIAL"}
        ]
        correct = sum(1 for x in validated if x.outcome == "CORRECT")
        wrong = sum(1 for x in validated if x.outcome == "WRONG")
        partial = sum(1 for x in validated if x.outcome == "PARTIAL")
        denominator = len(validated)
        return {
            "total": float(len(rows)),
            "validated": float(denominator),
            "correct": float(correct),
            "wrong": float(wrong),
            "partial": float(partial),
            "accuracy": (correct / denominator) if denominator else 0.0,
        }

    def save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "engine_name": self.ENGINE_NAME,
            "engine_version": self.ENGINE_VERSION,
            "predictions": [asdict(x) for x in self.predictions.values()],
            "updated_at": now_iso(),
        }
        with self.state_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=4)

    def load(self) -> None:
        if not self.state_file.exists():
            return
        with self.state_file.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        self.predictions = {
            item["prediction_id"]: Prediction(**item)
            for item in payload.get("predictions", [])
        }

    def reset(self) -> None:
        self.predictions = {}
        if self.state_file.exists():
            self.state_file.unlink()
