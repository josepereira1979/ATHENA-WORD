from __future__ import annotations

from typing import Any, Dict


class CorporateNetworkIntelligence:
    """Adapta a rede empresarial real para consumo seguro pela inteligência coletiva."""

    ENGINE_NAME = "ATHENA WORLD - CORPORATE NETWORK INTELLIGENCE"
    ENGINE_VERSION = "V01"

    def __init__(self, network_engine, family_engine, learning_engine):
        self.network = network_engine
        self.family_engine = family_engine
        self.learning = learning_engine

    def process(self, world_date: str) -> Dict[str, Any]:
        processed = 0
        signals = 0
        for family in self.family_engine.get_all_families():
            if not family.alive or not family.real_company_id:
                continue
            view = self.network.intelligence_for_company(family.real_company_id)
            processed += 1
            for relationship in view["relationships"]:
                self.learning.record_experience(
                    owner_id=family.family_id,
                    owner_type="FAMILY",
                    world_date=world_date,
                    event_type="REAL_CORPORATE_NETWORK",
                    description=(
                        f'{relationship["relationship_type"]}: '
                        f'{relationship["source_real_company_id"]} -> '
                        f'{relationship["target_real_company_id"]}; '
                        f'confidence={relationship["confidence"]:.2f}; '
                        f'status={relationship["status"]}; '
                        f'evidence={relationship["evidence"]}'
                    ),
                    outcome="OBSERVED",
                    success=True,
                    impact=relationship["confidence"],
                    learning_value=0.08,
                    knowledge_domain="REAL_NETWORK",
                    lesson=(
                        "Relações empresariais documentadas podem transmitir "
                        "risco, procura, dependência ou vantagem competitiva."
                    ),
                )
                signals += 1
        self.learning._refresh_aggregates()
        self.learning.save()
        return {"families_processed": processed, "signals_recorded": signals}
