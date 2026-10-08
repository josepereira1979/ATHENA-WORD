from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class CorporateRelationship:
    relationship_id: str
    source_real_company_id: str
    target_real_company_id: str
    relationship_type: str
    status: str
    confidence: float
    source_document: str
    source_url: str
    evidence: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    active: bool = True
    created_at: str = ""
    updated_at: str = ""

class CorporateNetworkEngine:
    ENGINE_NAME = "ATHENA WORLD - CORPORATE NETWORK ENGINE"
    ENGINE_VERSION = "V01"

    def __init__(self, state_file=None, universe=None):
        self.state_file = Path(state_file) if state_file else Path(__file__).resolve().parents[2] / "data" / "corporate_network_state.json"
        self.universe = universe
        self.relationships: Dict[str, CorporateRelationship] = {}
        self.load()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _validate_company(self, company_id: str) -> bool:
        if self.universe is None:
            return bool(company_id)
        company = self.universe.get_company(company_id)
        return company is not None and bool(company.active)

    def _make_id(self, source: str, target: str, relation_type: str) -> str:
        base = f"{source}|{target}|{relation_type.upper()}"
        return "REL-" + hashlib.sha256(base.encode("utf-8")).hexdigest()[:12].upper()

    def add_relationship(self, source_real_company_id: str, target_real_company_id: str, relationship_type: str,
                         status: str = "CONFIRMED", confidence: float = 1.0,
                         source_document: str = "", source_url: str = "", evidence: str = "",
                         valid_from: Optional[str] = None, valid_to: Optional[str] = None) -> CorporateRelationship:
        source, target = str(source_real_company_id).strip(), str(target_real_company_id).strip()
        relation_type, status = str(relationship_type).strip().upper(), str(status).strip().upper()
        confidence = float(confidence)
        if not self._validate_company(source) or not self._validate_company(target):
            raise ValueError("Both companies must exist and be active in the real-company universe.")
        if source == target or not relation_type:
            raise ValueError("Invalid company relationship endpoints.")
        if status not in {"CONFIRMED", "PROBABLE", "INFERRED"}:
            raise ValueError("Invalid relationship status.")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")
        relationship_id = self._make_id(source, target, relation_type)
        now = self._now()
        existing = self.relationships.get(relationship_id)
        row = CorporateRelationship(relationship_id, source, target, relation_type, status, confidence,
                                    source_document, source_url, evidence, valid_from, valid_to, True,
                                    existing.created_at if existing else now, now)
        self.relationships[relationship_id] = row
        self.save()
        return row

    def get_relationships(self, company_id=None, relationship_type=None, status=None) -> List[CorporateRelationship]:
        relation_type = relationship_type.upper() if relation_type else None
        wanted_status = status.upper() if status else None
        return [row for row in self.relationships.values()
                if row.active
                and (not company_id or row.source_real_company_id == company_id or row.target_real_company_id == company_id)
                and (not relation_type or row.relationship_type == relation_type)
                and (not wanted_status or row.status == wanted_status)]

    def get_neighbors(self, company_id: str) -> List[str]:
        neighbors = set()
        for row in self.get_relationships(company_id):
            neighbors.add(row.target_real_company_id if row.source_real_company_id == company_id else row.source_real_company_id)
        return sorted(neighbors)

    def counts(self) -> Dict[str, int]:
        active = self.get_relationships()
        by_type = {}
        for row in active:
            by_type[row.relationship_type] = by_type.get(row.relationship_type, 0) + 1
        return {"relationships": len(active), "confirmed": sum(x.status == "CONFIRMED" for x in active),
                "probable": sum(x.status == "PROBABLE" for x in active),
                "inferred": sum(x.status == "INFERRED" for x in active), "by_type": by_type}

    def export_graph(self):
        return {"nodes": sorted({x for row in self.get_relationships() for x in (row.source_real_company_id, row.target_real_company_id)}),
                "edges": [asdict(row) for row in self.get_relationships()]}

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({"engine_name": self.ENGINE_NAME, "engine_version": self.ENGINE_VERSION,
                                               "relationships": [asdict(x) for x in self.relationships.values()]},
                                              indent=2, ensure_ascii=False), encoding="utf-8")

    def _bootstrap_documented_relationships(self):
        if self.relationships:
            return
        seed = [
            ("REAL-000021", "REAL-000001", "SUPPLIES", 0.99, "NVIDIA FY2025 Annual Report",
             "NVIDIA states that it utilizes TSMC to produce semiconductor wafers."),
            ("REAL-000022", "REAL-000001", "SUPPLIES", 0.99, "NVIDIA FY2025 Annual Report",
             "NVIDIA states that it utilizes Samsung to produce semiconductor wafers."),
            ("REAL-000006", "REAL-000001", "COMPETES_WITH", 0.97, "NVIDIA FY2025 Annual Report",
             "NVIDIA identifies Broadcom among competitors in SoC and networking products."),
            ("REAL-000021", "REAL-000002", "SUPPLIES", 0.92, "TSMC 2025 Annual Report",
             "TSMC identifies Apple among its customers.")
        ]
        for source, target, relation_type, confidence, document, evidence in seed:
            if self._validate_company(source) and self._validate_company(target):
                relationship_id = self._make_id(source, target, relation_type)
                now = self._now()
                self.relationships[relationship_id] = CorporateRelationship(
                    relationship_id, source, target, relation_type, "CONFIRMED", confidence,
                    document, "", evidence, "2025-01-01", None, True, now, now
                )

    def load(self):
        if not self.state_file.exists():
            self._bootstrap_documented_relationships()
            self.save()
            return
        data = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.relationships = {x["relationship_id"]: CorporateRelationship(**x) for x in data.get("relationships", [])}
