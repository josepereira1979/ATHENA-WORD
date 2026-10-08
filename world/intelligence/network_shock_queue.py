from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class QueuedNetworkShock:
    shock_id: str
    origin_company_id: str
    direction: str
    strength: float
    world_date: str
    max_depth: int
    min_strength: float
    source_event_id: Optional[str]
    source_observation_id: Optional[str]
    status: str = "PENDING"
    created_at: str = ""


class NetworkShockQueue:
    ENGINE_NAME = "ATHENA WORLD - NETWORK SHOCK QUEUE"
    ENGINE_VERSION = "V01"

    def __init__(self, state_file=None):
        self.state_file = Path(state_file) if state_file else Path(__file__).resolve().parents[2] / "data" / "network_shock_queue_state.json"
        self.shocks: List[QueuedNetworkShock] = []
        self.load()

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def enqueue(
        self,
        origin_company_id: str,
        direction: str,
        strength: float = 1.0,
        world_date: str = "",
        max_depth: int = 3,
        min_strength: float = 0.10,
        source_event_id: Optional[str] = None,
        source_observation_id: Optional[str] = None,
    ) -> QueuedNetworkShock:
        direction = direction.upper().strip()
        if direction not in {"RISK", "OPPORTUNITY"}:
            raise ValueError("direction must be RISK or OPPORTUNITY")
        strength = float(strength)
        if not 0.0 <= strength <= 1.0:
            raise ValueError("strength must be between 0 and 1")
        row = QueuedNetworkShock(
            shock_id="NSH-" + uuid.uuid4().hex[:12].upper(),
            origin_company_id=str(origin_company_id),
            direction=direction,
            strength=strength,
            world_date=str(world_date),
            max_depth=max(1, int(max_depth)),
            min_strength=max(0.0, float(min_strength)),
            source_event_id=source_event_id,
            source_observation_id=source_observation_id,
            created_at=self._now(),
        )
        self.shocks.append(row)
        self.save()
        return row

    def get_pending(self) -> List[QueuedNetworkShock]:
        return [x for x in self.shocks if x.status == "PENDING"]

    def mark_processed(self, shock_id: str) -> None:
        for row in self.shocks:
            if row.shock_id == shock_id:
                row.status = "PROCESSED"
                self.save()
                return
        raise KeyError(f"Network shock not found: {shock_id}")

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(
                {
                    "engine_name": self.ENGINE_NAME,
                    "engine_version": self.ENGINE_VERSION,
                    "shocks": [asdict(x) for x in self.shocks],
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
        self.shocks = [QueuedNetworkShock(**x) for x in data.get("shocks", [])]
