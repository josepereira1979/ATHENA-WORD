from world.agents.agent_engine import AgentEngine
from world.families.family_engine import FamilyEngine
from world.survival.survival_engine import SurvivalEngine


def _make_world(tmp_path):
    families = FamilyEngine(state_file=tmp_path / "families.json", auto_load=False)
    agents = AgentEngine(state_file=tmp_path / "agents.json", auto_load=False)
    family = families.create_family("2026-10-09", family_name="Test Family")
    for role in ("ANALYST", "CONTRARIAN"):
        agent = agents.create_agent(
            world_date="2026-10-09",
            profession="Company researcher",
            family_id=family.family_id,
        )
        agent.research_role = role
        agent.research_focus = "REAL-001"
        families.add_member(family.family_id, agent.agent_id, "2026-10-09")
    family.real_company_id = "REAL-001"
    families.save()
    agents.save()
    return families, agents, family


def test_real_evidence_is_attributed_to_assigned_family_and_analyst(tmp_path):
    families, agents, family = _make_world(tmp_path)
    engine = SurvivalEngine(families, agents)

    result = engine.record_real_evidence(
        real_company_id="REAL-001",
        metric="REVENUE",
        source="TEST_FIXTURE",
        observation_id="OBS-001",
        world_date="2026-10-09",
    )

    assert result["families_updated"] == 1
    assert result["agents_updated"] == [family.member_ids[0]]
    assert family.real_evidence_count == 1
    assert agents.get_agent(family.member_ids[0]).evidence_collected == 1
    assert agents.get_agent(family.member_ids[1]).evidence_collected == 0


def test_only_evidence_backed_validated_research_unlocks_resources(tmp_path):
    families, agents, family = _make_world(tmp_path)
    engine = SurvivalEngine(families, agents)
    initial_food = family.food_reserve
    initial_tools = family.tools_level

    try:
        engine.assess_research(
            family_id=family.family_id,
            world_date="2026-10-09",
            evidence_count=0,
            validated_predictions=0,
            correct_predictions=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Research without evidence must not be rewarded.")

    result = engine.assess_research(
        family_id=family.family_id,
        world_date="2026-10-09",
        evidence_count=5,
        validated_predictions=5,
        correct_predictions=4,
        critical_challenges=3,
    )

    assert result["research_quality"] >= 0.70
    assert result["resources_awarded"] is True
    assert family.food_reserve > initial_food
    assert family.tools_level > initial_tools
    assert all(agents.get_agent(agent_id).validated_predictions == 5 for agent_id in family.member_ids)


def test_survival_tick_consumes_supplies_and_persists_status(tmp_path):
    families, agents, family = _make_world(tmp_path)
    engine = SurvivalEngine(families, agents)
    initial_food = family.food_reserve
    initial_water = family.water_reserve

    result = engine.process_tick("2026-10-10")

    assert result["families_alive_after"] == 1
    assert family.food_reserve < initial_food
    assert family.water_reserve < initial_water
    assert family.survival_days == 1
    assert family.survival_status == "STABLE"

    reloaded = FamilyEngine(state_file=tmp_path / "families.json", auto_load=True)
    saved_family = reloaded.get_family(family.family_id)
    assert saved_family is not None
    assert saved_family.survival_days == 1
    assert saved_family.food_reserve == family.food_reserve
