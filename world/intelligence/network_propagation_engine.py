from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .corporate_network_engine import CorporateNetworkEngine


@dataclass
class PropagationSignal:
    signal_id: str
    origin_company_id: str
    affected_company_id: str
    path: List[str]
    relation_types: List[str]
    direction: str
    strength: float
    confidence: float
    depth: int
    source_event_id: Optional[str]
    source_observation_id: Optional[str]
    world_date: str
    evidence: List[str]
    created_at: str


class NetworkPropagationEngine:
    """Propagates documented corporate shocks through the real-company graph.

    This engine does not invent relationships. It only traverses relationships
    already present in CorporateNetworkEngine and attenuates the signal by
    relation type, evidence confidence, and network depth.
    """

    ENGINE_NAME = "ATHENA WORLD - NETWORK PROPAGATION ENGINE"
    ENGINE_VERSION = "V01"

    DEFAULT_RELATION_WEIGHTS = {
        "SUPPLIES": 0.90,
        "CUSTOMER_OF": 0.85,
        "MANUFACTURES_FOR": 0.90,
        "DEPENDS_ON": 0.90,
        "DISTRIBUTES": 0.80,
        "USES_TECHNOLOGY_FROM": 0.80,
        "PARTNER_OF": 0.60,
        "INVESTOR_IN": 0.45,
        "ACQUIRES": 0.55,
        "SAME_SUPPLY_CHAIN": 0.55,
        "SAME_SECTOR": 0.30,
        "COMPETES_WITH": 0.60,
    }

    # Direction describes the effect on the relation target when the shock
    # starts at the relation source. The reverse traversal uses the inverse
    # semantic rule so supplier/customer edges work in both directions.
    _DIRECT_EFFECTS = {
        "SUPPLIES": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "CUSTOMER_OF": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "MANUFACTURES_FOR": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "DEPENDS_ON": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "DISTRIBUTES": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "USES_TECHNOLOGY_FROM": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "PARTNER_OF": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "INVESTOR_IN": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "ACQUIRES": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "SAME_SUPPLY_CHAIN": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "SAME_SECTOR": {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"},
        "COMPETES_WITH": {"RISK": "OPPORTUNITY", "OPPORTUNITY": "RISK"},
    }

    def __init__(self, network_engine: CorporateNetworkEngine, state_file=None):
        self.network = network_engine
        self.state_file = Path(state_file) if state_file else Path(__file__).resolve().parents[2] / "data" / "network_propagation_state.json"
        self.signals: Dict[str, PropagationSignal] = {}
        self.load()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _make_id(self, origin: str, affected: str, path: List[str], direction: str) -> str:
        base = "|".join([origin, affected, direction, *path])
        return "PSIG-" + hashlib.sha256(base.encode("utf-8")).hexdigest()[:14].upper()

    def _effect(self, relation_type: str, direction: str, traversed_forward: bool) -> str:
        relation_type = relation_type.upper()
        direction = direction.upper()
        direct = self._DIRECT_EFFECTS.get(relation_type, {"RISK": "RISK", "OPPORTUNITY": "OPPORTUNITY"})
        if traversed_forward:
            return direct.get(direction, direction)
        # For symmetric relations this is unchanged. For directional supply
        # relations, reversing the edge keeps the shock semantics but swaps
        # upstream/downstream exposure; the same effect is conservative.
        return direct.get(direction, direction)

    def _edge_options(self, company_id: str):
        for row in self.network.get_relationships(company_id=company_id):
            if row.source_real_company_id == company_id:
                yield row, row.target_real_company_id, True
            else:
                yield row, row.source_real_company_id, False

    def propagate(
        self,
        origin_company_id: str,
        initial_direction: str,
        initial_strength: float = 1.0,
        max_depth: int = 3,
        min_strength: float = 0.10,
        world_date: str = "",
        source_event_id: Optional[str] = None,
        source_observation_id: Optional[str] = None,
        relationship_weights: Optional[Dict[str, float]] = None,
    ) -> List[PropagationSignal]:
        direction = str(initial_direction).strip().upper()
        if direction not in {"RISK", "OPPORTUNITY"}:
            raise ValueError("initial_direction must be RISK or OPPORTUNITY.")
        if not 0.0 <= float(initial_strength) <= 1.0:
            raise ValueError("initial_strength must be between 0 and 1.")
        if int(max_depth) < 1:
            raise ValueError("max_depth must be >= 1.")
        if not self.network._validate_company(origin_company_id):
            raise ValueError("Origin company must exist and be active.")

        weights = dict(self.DEFAULT_RELATION_WEIGHTS)
        if relationship_weights:
            weights.update({str(k).upper(): float(v) for k, v in relationship_weights.items()})

        results: Dict[str, PropagationSignal] = {}
        frontier: List[Tuple[str, List[str], List[str], str, float, float, List[str]]] = [
            (origin_company_id, [origin_company_id], [], direction, float(initial_strength), 1.0, [])
        ]

        for _ in range(int(max_depth)):
            next_frontier = []
            for current_id, path, relation_types, current_direction, strength, confidence, evidence in frontier:
                for relation, neighbor, forward in self._edge_options(current_id):
                    if neighbor in path:
                        continue
                    weight = weights.get(relation.relationship_type, 0.40)
                    if weight <= 0.0:
                        continue
                    next_strength = strength * weight
                    if next_strength < min_strength:
                        continue

                    next_direction = self._effect(relation.relationship_type, current_direction, forward)
                    next_confidence = confidence * relation.confidence
                    next_path = path + [neighbor]
                    next_relation_types = relation_types + [relation.relationship_type]
                    next_evidence = evidence + [relation.evidence or relation.source_document or relation.source_url]
                    signal = PropagationSignal(
                        signal_id=self._make_id(origin_company_id, neighbor, next_path, next_direction),
                        origin_company_id=origin_company_id,
                        affected_company_id=neighbor,
                        path=next_path,
                        relation_types=next_relation_types,
                        direction=next_direction,
                        strength=round(next_strength, 8),
                        confidence=round(next_confidence, 8),
                        depth=len(next_path) - 1,
                        source_event_id=source_event_id,
                        source_observation_id=source_observation_id,
                        world_date=world_date,
                        evidence=[x for x in next_evidence if x],
                        created_at=self._now(),
                    )
                    previous = results.get(neighbor)
                    if previous is None or (signal.strength * signal.confidence) > (previous.strength * previous.confidence):
                        results[neighbor] = signal
                    next_frontier.append(
                        (neighbor, next_path, next_relation_types, next_direction,
                         next_strength, next_confidence, next_evidence)
                    )
            frontier = next_frontier
            if not frontier:
                break

        for signal in results.values():
            self.signals[signal.signal_id] = signal
        if results:
            self.save()
        return sorted(results.values(), key=lambda x: (-(x.strength * x.confidence), x.depth, x.affected_company_id))

    def get_signals(self, affected_company_id=None, direction=None, min_strength=0.0) -> List[PropagationSignal]:
        direction = direction.upper() if direction else None
        return [
            signal for signal in self.signals.values()
            if (not affected_company_id or signal.affected_company_id == affected_company_id)
            and (not direction or signal.direction == direction)
            and signal.strength >= float(min_strength)
        ]

    def summarize(self, signals: Optional[List[PropagationSignal]] = None) -> dict:
        rows = signals if signals is not None else list(self.signals.values())
        return {
            "signals": len(rows),
            "risk": sum(x.direction == "RISK" for x in rows),
            "opportunity": sum(x.direction == "OPPORTUNITY" for x in rows),
            "max_depth": max((x.depth for x in rows), default=0),
            "top_affected_companies": [
                {
                    "company_id": x.affected_company_id,
                    "direction": x.direction,
                    "strength": x.strength,
                    "confidence": x.confidence,
                    "depth": x.depth,
                    "path": x.path,
                }
                for x in sorted(rows, key=lambda y: -(y.strength * y.confidence))[:10]
            ],
        }

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(
                {
                    "engine_name": self.ENGINE_NAME,
                    "engine_version": self.ENGINE_VERSION,
                    "signals": [asdict(x) for x in self.signals.values()],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def load(self):
        if not self.state_file.exists():
            return
        data = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.signals = {
            x["signal_id"]: PropagationSignal(**x)
            for x in data.get("signals", [])
        }
