from __future__ import annotations

from typing import Any, Dict


class WorldLaunchController:
    """Prepara a primeira WORLD operacional sem criar dados fictícios."""

    ENGINE_NAME = "ATHENA WORLD - LAUNCH CONTROLLER"
    ENGINE_VERSION = "V01"

    def __init__(self, runtime):
        self.runtime = runtime

    def readiness(self) -> Dict[str, Any]:
        census = self.runtime.global_market_census()
        integrity = self.runtime.world_integrity()
        capacity = census["unassigned_company_capacity"]
        families = census["unassigned_families"]
        return {
            "ready": capacity >= families and integrity["status"] == "HEALTHY",
            "capacity": capacity,
            "families_to_assign": families,
            "integrity": integrity,
            "census": census,
        }

    def prepare(self, allocate: bool = False, cycles: int = 0) -> Dict[str, Any]:
        before = self.readiness()
        result: Dict[str, Any] = {"before": before, "allocation": None, "cycles": None}

        if allocate:
            if not before["ready"]:
                result["status"] = "WAITING_FOR_REAL_COMPANIES"
                result["reason"] = "Não existem empresas reais suficientes para atribuir todas as famílias 1:1."
                return result
            result["allocation"] = self.runtime.allocate_global_family_market()
            result["status"] = "POPULATED"

        if cycles:
            if cycles < 1:
                raise ValueError("cycles must be >= 1")
            result["cycles"] = self.runtime.run_cycles(cycles)

        result["after"] = self.readiness()
        result["status"] = result.get("status", "READY")
        return result
