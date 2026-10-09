from __future__ import annotations

from typing import Dict, Optional

from .network_propagation_engine import NetworkPropagationEngine


class NetworkShockProcessor:
    """Turns a real-company shock into propagation signals and family intelligence."""

    ENGINE_NAME = "ATHENA WORLD - NETWORK SHOCK PROCESSOR"
    ENGINE_VERSION = "V01"

    def __init__(self, propagation_engine, family_engine=None, learning_engine=None):
        self.propagation = propagation_engine
        self.family_engine = family_engine
        self.learning_engine = learning_engine

    def process_shock(
        self,
        origin_company_id: str,
        direction: str,
        strength: float = 1.0,
        world_date: str = "",
        max_depth: int = 3,
        min_strength: float = 0.10,
        source_event_id: Optional[str] = None,
        source_observation_id: Optional[str] = None,
    ) -> Dict:
        signals = self.propagation.propagate(
            origin_company_id=origin_company_id,
            initial_direction=direction,
            initial_strength=strength,
            max_depth=max_depth,
            min_strength=min_strength,
            world_date=world_date,
            source_event_id=source_event_id,
            source_observation_id=source_observation_id,
        )

        family_signals = 0
        if self.family_engine is not None and self.learning_engine is not None:
            family_by_real = {
                getattr(family, "real_company_id", None): family
                for family in getattr(self.family_engine, "families", {}).values()
                if getattr(family, "alive", False) and getattr(family, "real_company_id", None)
            }
            for signal in signals:
                family = family_by_real.get(signal.affected_company_id)
                if family is None:
                    continue
                self.learning_engine.record_experience(
                    owner_id=family.family_id,
                    owner_type="FAMILY",
                    world_date=world_date,
                    event_type="NETWORK_SHOCK",
                    description=(
                        f"{signal.direction}: {signal.origin_company_id} -> "
                        f"{signal.affected_company_id} via {' > '.join(signal.relation_types)}"
                    ),
                    outcome="OBSERVED",
                    success=True,
                    impact=signal.strength * signal.confidence,
                    learning_value=0.10,
                    knowledge_domain="NETWORK_RISK",
                    lesson=(
                        "Choques empresariais podem propagar-se por relações reais; "
                        "a intensidade diminui com a distância e a confiança da evidência."
                    ),
                )
                family_signals += 1
            refresh = getattr(self.learning_engine, "_refresh_aggregates", None)
            if callable(refresh):
                refresh()
            save = getattr(self.learning_engine, "save", None)
            if callable(save):
                save()

        return {
            "origin_company_id": origin_company_id,
            "direction": direction.upper(),
            "world_date": world_date,
            "signals": len(signals),
            "family_signals": family_signals,
            "summary": self.propagation.summarize(signals),
            "signal_ids": [signal.signal_id for signal in signals],
        }
