from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from world.intelligence.prediction_engine import PredictionEngine


def test_prediction_engine_round_trip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = PredictionEngine(
            state_file=Path(tmp) / "predictions.json",
            auto_load=False,
        )

        prediction = engine.create_prediction(
            owner_id="FAMILY-001",
            owner_type="FAMILY",
            subject_id="REAL-001",
            subject_type="COMPANY",
            metric="REVENUE",
            statement="A receita deverá crescer.",
            predicted_value=120.0,
            confidence=0.75,
            horizon_start="2027-01-01",
            horizon_end="2027-03-31",
            invalidation_condition="Queda estrutural da procura.",
        )

        assert prediction.status == "OPEN"
        assert engine.add_evidence(prediction.prediction_id, "OBS-001", True)
        assert engine.add_evidence(prediction.prediction_id, "OBS-002", False)

        engine.validate_prediction(
            prediction.prediction_id,
            actual_value=118.0,
            actual_date="2027-03-31",
            outcome="CORRECT",
        )

        stats = engine.accuracy("FAMILY-001")
        assert stats["validated"] == 1.0
        assert stats["correct"] == 1.0
        assert stats["accuracy"] == 1.0

        print("PREDICTION ENGINE TEST: OK")


if __name__ == "__main__":
    test_prediction_engine_round_trip()
