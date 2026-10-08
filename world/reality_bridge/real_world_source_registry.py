from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional


@dataclass(frozen=True)
class WorldSource:
    name: str
    region: str
    source_type: str
    enabled: bool = True
    notes: str = ""


class RealWorldSourceRegistry:
    """Registo de fontes reais sem acoplar a WORLD a um fornecedor único."""

    def __init__(self):
        self.sources: Dict[str, WorldSource] = {}
        self.register(WorldSource(
            "SEC_EDGAR",
            "AMERICAS",
            "REGULATORY",
            True,
            "US public-company reference data",
        ))
        self.register(WorldSource(
            "EXCHANGE_FEEDS",
            "GLOBAL",
            "EXCHANGE",
            True,
            "Official exchange/listing feeds supplied externally",
        ))
        self.register(WorldSource(
            "REGULATORS",
            "GLOBAL",
            "REGULATORY",
            True,
            "Local securities regulators supplied externally",
        ))
        self.register(WorldSource(
            "CORPORATE_FILINGS",
            "GLOBAL",
            "FILINGS",
            True,
            "Annual reports, regulatory filings and issuer disclosures",
        ))

    def register(self, source: WorldSource) -> None:
        if not source.name:
            raise ValueError("source name is required")
        self.sources[source.name] = source

    def list_sources(self) -> list[Dict[str, Any]]:
        return [
            {
                "name": source.name,
                "region": source.region,
                "source_type": source.source_type,
                "enabled": source.enabled,
                "notes": source.notes,
            }
            for source in self.sources.values()
        ]

    def ingest(
        self,
        source_name: str,
        runtime,
        records: Iterable[Dict[str, Any]],
        allocate: bool = True,
    ) -> Dict[str, Any]:
        source = self.sources.get(source_name)
        if source is None or not source.enabled:
            raise ValueError(f"Unknown or disabled source: {source_name}")
        return runtime.connect_real_world(records, allocate=allocate)
