from __future__ import annotations

from typing import Any, Dict, List


class WorldControlCenter:
    """Painel estrutural da ATHENA WORLD: saúde, população, inteligência e prontidão."""

    ENGINE_NAME = "ATHENA WORLD - CONTROL CENTER"
    ENGINE_VERSION = "V01"

    def __init__(self, runtime):
        self.runtime = runtime

    def snapshot(self) -> Dict[str, Any]:
        engines = self.runtime.engines
        family_engine = engines.get("FAMILY")
        agent_engine = engines.get("AGENT")
        prediction_engine = getattr(self.runtime, "prediction_engine", None)
        learning_engine = engines.get("LEARNING")
        network = getattr(self.runtime, "corporate_network_engine", None)
        census = self.runtime.global_market_census()
        readiness = self.runtime.global_market_readiness()
        allocation = self.runtime.preview_global_family_market_allocation(limit=10)
        families = list(family_engine.families.values()) if family_engine else []
        agents = getattr(agent_engine, "agents", {}) if agent_engine else {}
        predictions = prediction_engine.get_all_predictions() if prediction_engine else []
        validated = [p for p in predictions if p.status == "VALIDATED"]
        network_counts = network.counts() if network else {}
        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "world": {
                "date": self.runtime.world_core.state["world_date"],
                "tick": self.runtime.world_core.state["tick"],
                "paused": self.runtime.world_core.state["paused"],
            },
            "population": {
                "families": len(families),
                "families_assigned": sum(1 for f in families if f.real_company_id),
                "families_unassigned": sum(1 for f in families if f.alive and not f.real_company_id),
                "agents": len(agents),
                "real_companies": census.get("active_real_companies", 0),
                "primary_listings": census.get("companies_with_primary_listing", 0),
            },
            "markets": {
                "regions": census.get("regions", {}),
                "countries": census.get("countries", {}),
                "exchanges": census.get("exchanges", {}),
                "sectors": census.get("sectors", {}),
                "readiness": readiness,
            },
            "network": network_counts,
            "real_world_sources": self.runtime.real_world_sources.list_sources(),
            "intelligence": {
                "predictions": len(predictions),
                "open_predictions": sum(1 for p in predictions if p.status == "OPEN"),
                "validated_predictions": len(validated),
                "accuracy": prediction_engine.accuracy() if prediction_engine else {},
                "learning_experiences": getattr(getattr(learning_engine, "state", None), "total_experiences", 0),
                "learning_knowledge": getattr(getattr(learning_engine, "state", None), "total_knowledge_records", 0),
            },
            "allocation_preview": allocation,
        }

    def integrity(self) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        engines = self.runtime.engines
        family_engine = engines.get("FAMILY")
        agent_engine = engines.get("AGENT")
        company_engine = engines.get("COMPANY")
        bridge = engines.get("REALITY_BRIDGE")
        universe = getattr(bridge, "universe", None)
        assigned_real = {}
        for family in (family_engine.families.values() if family_engine else []):
            if not family.alive:
                continue

            for agent_id in family.member_ids:
                if agent_engine is None or agent_id not in agent_engine.agents:
                    errors.append(f"UNKNOWN_FAMILY_MEMBER:{family.family_id}:{agent_id}")

            if family.virtual_company_id and not family.real_company_id:
                errors.append(f"VIRTUAL_COMPANY_WITHOUT_REAL_IDENTITY:{family.family_id}")
            if family.real_company_id and not family.virtual_company_id:
                errors.append(f"REAL_COMPANY_WITHOUT_VIRTUAL_COMPANY:{family.family_id}")

            if not family.real_company_id:
                continue
            if family.real_company_id in assigned_real:
                errors.append(f"DUPLICATE_REAL_COMPANY_ASSIGNMENT:{family.real_company_id}")
            assigned_real[family.real_company_id] = family.family_id
            if universe is not None and universe.get_company(family.real_company_id) is None:
                errors.append(f"UNKNOWN_REAL_COMPANY:{family.family_id}:{family.real_company_id}")
            if not family.market_exchange or not family.market_listing_id:
                warnings.append(f"FAMILY_MARKET_IDENTITY_INCOMPLETE:{family.family_id}")

            virtual = company_engine.get_company(family.virtual_company_id) if company_engine and family.virtual_company_id else None
            if virtual is None:
                errors.append(f"UNKNOWN_VIRTUAL_COMPANY:{family.family_id}:{family.virtual_company_id}")
            elif getattr(virtual, "real_company_id", None) != family.real_company_id:
                errors.append(f"VIRTUAL_REAL_COMPANY_MISMATCH:{family.family_id}:{family.real_company_id}")

            mapping = bridge.get_mapping_by_virtual_company(family.virtual_company_id) if bridge and family.virtual_company_id else None
            if mapping is None:
                errors.append(f"MISSING_REALITY_MAPPING:{family.family_id}:{family.virtual_company_id}")
            elif mapping.real_company_id != family.real_company_id:
                errors.append(f"REALITY_MAPPING_MISMATCH:{family.family_id}:{family.real_company_id}")
        prediction_engine = getattr(self.runtime, "prediction_engine", None)
        if prediction_engine:
            for prediction in prediction_engine.get_all_predictions():
                if prediction.horizon_end < prediction.horizon_start:
                    errors.append(f"INVALID_PREDICTION_HORIZON:{prediction.prediction_id}")
                if prediction.status == "OPEN" and prediction.actual_date is not None:
                    errors.append(f"OPEN_PREDICTION_HAS_RESULT:{prediction.prediction_id}")
        return {
            "status": "HEALTHY" if not errors else "ATTENTION_REQUIRED",
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
        }

    def full_report(self) -> Dict[str, Any]:
        return {"snapshot": self.snapshot(), "integrity": self.integrity()}
