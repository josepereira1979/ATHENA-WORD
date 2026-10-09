from world.learning.learning_engine import LearningEngine
from world.orchestration.world_runtime import WorldRuntime


def test_runtime_initializes_learning_engine(tmp_path):
    runtime = WorldRuntime(state_dir=tmp_path, auto_load=False)
    learning = runtime.engines["LEARNING"]
    assert learning.state is not None
    assert learning.state.world_date == runtime.world_core.state.world_date
    learning.process_tick(runtime.world_core.state["world_date"])
    assert learning.state.total_ticks == 1


def test_learning_state_survives_restart(tmp_path):
    state_file = tmp_path / "learning_state.json"
    first = LearningEngine(state_file=state_file)
    first.initialize("2026-10-01")
    first.record_experience(
        owner_id="FAMILY-1",
        owner_type="FAMILY",
        world_date="2026-10-01",
        event_type="VALIDATED_OUTCOME",
        description="A previsão falhou perante a observação real.",
        outcome="WRONG",
        success=False,
        impact=-0.5,
        learning_value=0.12,
        knowledge_domain="REVENUE",
        lesson="Reduzir confiança quando a evidência contradiz a hipótese.",
    )

    second = LearningEngine(state_file=state_file)
    loaded = second.load()
    assert loaded.total_experiences == 1
    assert loaded.total_failures == 1
    assert second.get_owner_experiences("FAMILY-1", "FAMILY")[0].outcome == "WRONG"


def test_real_observation_validates_prediction_and_teaches_failure(tmp_path):
    runtime = WorldRuntime(state_dir=tmp_path, auto_load=False)
    universe = runtime.engines["REALITY_BRIDGE"].universe
    real = universe.create_company(
        legal_name="Evidence Test Corporation",
        country="USA",
        sector="TECHNOLOGY",
        real_company_id="REAL-EVIDENCE-001",
        source_identity="test:issuer:001",
    )
    universe.add_listing(
        real_company_id=real.real_company_id,
        exchange="NASDAQ",
        ticker="EVT1",
        country="USA",
        currency="USD",
        primary=True,
    )

    result = runtime.finalize_global_world()
    assert result["closed"] is True
    assert runtime.world_integrity()["status"] == "HEALTHY"
    family = next(
        f for f in runtime.engines["FAMILY"].get_all_families()
        if f.real_company_id == real.real_company_id
    )
    prediction = runtime.prediction_engine.create_prediction(
        owner_id=family.family_id,
        owner_type="FAMILY",
        subject_id=family.virtual_company_id,
        subject_type="COMPANY",
        metric="REVENUE",
        statement="A receita será 100.",
        horizon_start="2026-10-02",
        horizon_end="2026-10-10",
        predicted_value=100.0,
        confidence=0.8,
    )

    runtime.ingest_real_observation(
        real_company_id=real.real_company_id,
        metric="REVENUE",
        value=130.0,
        observation_date="2026-10-03",
        source="TEST_FIXTURE",
        unit="USD",
    )
    validated = runtime.prediction_engine.get_prediction(prediction.prediction_id)
    assert validated.status == "VALIDATED"
    assert validated.outcome == "WRONG"

    learned = runtime.engines["LEARNING"].learn_from_validated_predictions(
        runtime.prediction_engine.get_all_predictions(),
        world_date="2026-10-03",
    )
    assert len(learned) == 1
    assert learned[0].success is False
    assert "PREDICTION_ID:" + prediction.prediction_id in learned[0].description

    again = runtime.engines["LEARNING"].learn_from_validated_predictions(
        runtime.prediction_engine.get_all_predictions(),
        world_date="2026-10-03",
    )
    assert again == []



def test_neutral_observation_does_not_count_as_success_or_failure(tmp_path):
    engine = LearningEngine(state_file=tmp_path / "learning_state.json")
    engine.initialize("2026-10-01")
    experience = engine.record_experience(
        owner_id="FAMILY-NEUTRAL",
        owner_type="FAMILY",
        world_date="2026-10-01",
        event_type="COMPANY_INTELLIGENCE",
        description="Metric observed without a validated forecast.",
        outcome="OBSERVED",
        success=None,
        learning_value=0.02,
        knowledge_domain="FINANCE",
    )
    assert experience.success is None
    assert engine.state.total_successes == 0
    assert engine.state.total_failures == 0
    knowledge = engine.get_knowledge("FAMILY-NEUTRAL", "FAMILY", "FINANCE")
    assert knowledge.experience_count == 1
    assert knowledge.successful_experiences == 0
    assert knowledge.failed_experiences == 0
