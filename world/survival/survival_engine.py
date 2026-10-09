from __future__ import annotations

from typing import Any, Dict


class SurvivalEngine:
    """Economia de sobrevivência das famílias, separada da ligação externa.

    As métricas são normalizadas. Só uma avaliação explícita, sustentada por
    evidência e previsões validadas, pode desbloquear recursos por investigação.
    """

    ENGINE_NAME = "ATHENA WORLD - SURVIVAL ENGINE"
    ENGINE_VERSION = "V01"

    FOOD_PER_TICK = 0.10
    WATER_PER_TICK = 0.12
    HEALTH_LOSS_WITHOUT_FOOD = 0.025
    HEALTH_LOSS_WITHOUT_WATER = 0.035
    ENERGY_RECOVERY = 0.04
    ENERGY_LOSS_WITHOUT_SUPPLIES = 0.08

    def __init__(self, family_engine, agent_engine) -> None:
        self.family_engine = family_engine
        self.agent_engine = agent_engine

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        return max(minimum, min(maximum, float(value)))

    def process_tick(self, world_date: str) -> Dict[str, Any]:
        """Consome recursos, atualiza saúde/energia e aplica consequências."""
        families = self.family_engine.get_all_families()
        alive_before = sum(1 for family in families if family.alive)
        deaths = 0

        for family in families:
            if not family.alive:
                continue

            family.survival_days += 1
            family.food_reserve = max(0.0, family.food_reserve - self.FOOD_PER_TICK)
            family.water_reserve = max(0.0, family.water_reserve - self.WATER_PER_TICK)

            if family.food_reserve <= 0.0:
                family.health = self._clamp(family.health - self.HEALTH_LOSS_WITHOUT_FOOD)
            if family.water_reserve <= 0.0:
                family.health = self._clamp(family.health - self.HEALTH_LOSS_WITHOUT_WATER)

            if family.food_reserve > 0.0 and family.water_reserve > 0.0:
                family.energy = self._clamp(family.energy + self.ENERGY_RECOVERY)
                family.survival_status = "STABLE"
            else:
                family.energy = self._clamp(family.energy - self.ENERGY_LOSS_WITHOUT_SUPPLIES)
                family.survival_status = "FOOD_CRITICAL" if family.food_reserve <= 0.0 else "WATER_CRITICAL"

            family.last_update_world_date = world_date
            if family.health <= 0.0:
                family.alive = False
                family.survival_status = "DECEASED"
                deaths += 1
                for agent_id in family.member_ids:
                    self.agent_engine.kill_agent(agent_id)

        self.family_engine.save()
        self.agent_engine.save()
        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "world_date": world_date,
            "families_total": len(families),
            "families_alive_before": alive_before,
            "families_alive_after": sum(1 for family in families if family.alive),
            "families_deceased_this_tick": deaths,
        }

    def record_real_evidence(
        self,
        real_company_id: str,
        metric: str,
        source: str,
        observation_id: str,
        world_date: str,
    ) -> Dict[str, Any]:
        """Regista evidência recebida pelo Reality Bridge sem presumir que seja boa."""
        if not real_company_id or not metric or not source or not observation_id:
            raise ValueError("Empresa, métrica, fonte e ID da observação são obrigatórios.")

        matches = [
            family for family in self.family_engine.get_all_families()
            if family.alive and family.real_company_id == real_company_id
        ]
        updated_agents = []
        for family in matches:
            family.real_evidence_count += 1
            family.last_update_world_date = world_date
            members = [
                self.agent_engine.get_agent(agent_id)
                for agent_id in family.member_ids
            ]
            members = [agent for agent in members if agent is not None and agent.alive]
            analysts = [agent for agent in members if agent.research_role == "ANALYST"]
            targets = analysts or members[:1]
            for agent in targets:
                agent.evidence_collected += 1
                agent.research_focus = real_company_id
                agent.last_update_world_date = world_date
                updated_agents.append(agent.agent_id)

        if matches:
            self.family_engine.save()
            self.agent_engine.save()
        return {
            "observation_id": observation_id,
            "real_company_id": real_company_id,
            "metric": metric.upper(),
            "source": source,
            "families_updated": len(matches),
            "agents_updated": updated_agents,
        }

    def assess_research(
        self,
        family_id: str,
        world_date: str,
        evidence_count: int,
        validated_predictions: int,
        correct_predictions: int,
        critical_challenges: int = 0,
    ) -> Dict[str, Any]:
        """Converte trabalho comprovado em progresso; nunca recompensa dados sem validação."""
        family = self.family_engine.get_family(family_id)
        if family is None or not family.alive:
            raise ValueError("Família inexistente ou inativa.")
        if evidence_count < 1 or validated_predictions < 1:
            raise ValueError("É necessária evidência e pelo menos uma previsão validada.")
        if evidence_count > int(family.real_evidence_count):
            raise ValueError("A avaliação excede a evidência externa registada para esta família.")
        if correct_predictions < 0 or correct_predictions > validated_predictions:
            raise ValueError("Número de previsões corretas inválido.")
        if critical_challenges < 0:
            raise ValueError("O número de desafios críticos não pode ser negativo.")

        evidence_score = min(1.0, evidence_count / 5.0)
        accuracy_score = correct_predictions / validated_predictions
        challenge_score = min(1.0, critical_challenges / max(1, validated_predictions))
        quality = round(0.35 * evidence_score + 0.45 * accuracy_score + 0.20 * challenge_score, 4)

        family.research_quality = quality
        family.research_assessments += 1
        family.predictions_count = max(family.predictions_count, validated_predictions)
        family.predictions_correct = max(family.predictions_correct, correct_predictions)

        rewarded = False
        if quality >= 0.70 and family.last_research_reward_date != world_date:
            family.food_reserve += 1.5 * quality
            family.water_reserve += 1.5 * quality
            family.tools_level = min(1.0, family.tools_level + 0.05 * quality)
            family.shelter_quality = min(1.0, family.shelter_quality + 0.02 * quality)
            family.last_research_reward_date = world_date
            if quality >= 0.85 and family.tools_level >= 0.20:
                family.evolution_level += 1
            rewarded = True

        family.last_update_world_date = world_date
        for agent_id in family.member_ids:
            agent = self.agent_engine.get_agent(agent_id)
            if agent is None or not agent.alive:
                continue
            agent.validated_predictions = max(agent.validated_predictions, validated_predictions)
            agent.prediction_accuracy = round(accuracy_score, 4)
            agent.hypotheses_challenged = max(agent.hypotheses_challenged, critical_challenges)
            agent.last_update_world_date = world_date

        self.family_engine.save()
        self.agent_engine.save()
        return {
            "family_id": family_id,
            "world_date": world_date,
            "research_quality": quality,
            "evidence_score": round(evidence_score, 4),
            "prediction_accuracy": round(accuracy_score, 4),
            "critical_challenge_score": round(challenge_score, 4),
            "resources_awarded": rewarded,
            "food_reserve": family.food_reserve,
            "water_reserve": family.water_reserve,
            "tools_level": family.tools_level,
            "evolution_level": family.evolution_level,
        }
