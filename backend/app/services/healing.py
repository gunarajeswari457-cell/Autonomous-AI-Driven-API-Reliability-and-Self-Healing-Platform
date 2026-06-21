import asyncio
import random
import uuid
from datetime import datetime, timezone
from typing import Any

from app.services.metrics_simulator import kafka_sim
from app.services.mongo_log import log_event


class HealingService:
    def __init__(self) -> None:
        self._logs: list[dict[str, Any]] = []

    def _push(self, entry: dict[str, Any]) -> None:
        self._logs.append(entry)
        self._logs = self._logs[-200:]

    async def run_action(self, action: str) -> dict[str, Any]:
        rid = str(uuid.uuid4())
        self._push(
            {
                "id": rid,
                "action": action,
                "status": "started",
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )
        await asyncio.sleep(0.6 + random.random() * 0.9)
        ok = random.random() > 0.06
        result = {
            "id": rid,
            "action": action,
            "status": "success" if ok else "failed",
            "message": (
                f"{action} completed successfully"
                if ok
                else f"{action} blocked by safety policy (simulated)"
            ),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._push(result)
        await kafka_sim.publish(
            "healing.actions",
            {"action": action, "status": result["status"], "id": rid},
        )
        await log_event(
            "healing_logs",
            {"action": action, "status": result["status"], "correlation_id": rid},
        )
        return result

    def logs(self) -> list[dict[str, Any]]:
        return list(reversed(self._logs[-80:]))


healing_service = HealingService()
