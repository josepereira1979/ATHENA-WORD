from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class RealWorldConnection:
    """Único ponto de entrada para ligar fontes reais à ATHENA WORLD."""

    ENGINE_NAME = "ATHENA WORLD - REAL WORLD CONNECTION"
    ENGINE_VERSION = "V01"

    def __init__(self, runtime):
        self.runtime = runtime

    def ingest_and_finalize(
        self,
        records: Iterable[Dict[str, Any]],
        allocate: bool = True,
    ) -> Dict[str, Any]:
        ingestion = self.runtime.ingest_global_companies(records, allocate=False)
        finalization = None
        if allocate:
            finalization = self.runtime.finalize_global_world()
        return {
            "engine": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "ingestion": ingestion,
            "finalization": finalization,
        }

    def status(self) -> Dict[str, Any]:
        """Distinguish adapter readiness from a verified live external session."""
        bridge = self.runtime.engines.get("REALITY_BRIDGE")
        aggregates = bridge.aggregates() if bridge is not None else {}
        return {
            "connected": False,
            "live_connection_verified": False,
            "adapter_ready": True,
            "mode": "ADAPTER_READY",
            "source_of_truth": "EXTERNAL_REAL_WORLD_SOURCES",
            "ingested_evidence": {
                "real_observations": int(aggregates.get("real_observations", 0)),
                "real_events": int(aggregates.get("real_events", 0)),
                "company_mappings": int(aggregates.get("mappings", 0)),
            },
            "note": "Registo de fontes e adaptador prontos não comprovam ligação live.",
            "world": self.runtime.world_snapshot(),
        }
