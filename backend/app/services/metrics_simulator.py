import asyncio
import json
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MetricPoint:
    ts: float
    value: float


class MetricsSimulator:
    def __init__(self) -> None:
        self._cpu: deque[MetricPoint] = deque(maxlen=120)
        self._mem: deque[MetricPoint] = deque(maxlen=120)
        self._latency: deque[MetricPoint] = deque(maxlen=120)
        self._errors: deque[MetricPoint] = deque(maxlen=120)
        self._traffic: deque[MetricPoint] = deque(maxlen=120)
        self._seed = time.time()

    def _noise(self, phase: float, amp: float = 1.0) -> float:
        return amp * (0.5 + 0.5 * random.random()) * (0.85 + 0.15 * __import__("math").sin(phase))

    def snapshot(self) -> dict[str, Any]:
        t = time.time()
        phase = (t - self._seed) / 8.0
        cpu = min(99, 35 + 40 * random.random() + 10 * __import__("math").sin(phase))
        mem = min(95, 45 + 30 * random.random() + 8 * __import__("math").cos(phase * 0.7))
        latency = max(12, 80 + 60 * random.random() + 25 * __import__("math").sin(phase * 1.3))
        err = max(0.01, 0.2 + 1.2 * random.random() + 0.4 * abs(__import__("math").sin(phase * 2)))
        traffic = 800 + 400 * random.random() + 200 * __import__("math").sin(phase * 0.9)

        self._cpu.append(MetricPoint(t, cpu))
        self._mem.append(MetricPoint(t, mem))
        self._latency.append(MetricPoint(t, latency))
        self._errors.append(MetricPoint(t, err))
        self._traffic.append(MetricPoint(t, traffic))

        health = max(0, min(100, 100 - (cpu * 0.25 + mem * 0.2 + err * 5 + max(0, latency - 120) * 0.05)))
        failure_prob = min(0.99, max(0.01, (100 - health) / 130 + random.random() * 0.08))
        confidence = max(62, min(99.4, 88 + random.random() * 8 - failure_prob * 12))

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": round(cpu, 2),
            "memory_percent": round(mem, 2),
            "network_rps": round(traffic, 2),
            "error_rate_percent": round(err, 3),
            "latency_ms_p95": round(latency, 2),
            "api_health_score": round(health, 2),
            "failure_probability": round(failure_prob, 4),
            "ai_confidence_percent": round(confidence, 2),
            "active_alerts": random.randint(0, 4),
            "active_apis": 24 + random.randint(-2, 3),
        }

    def series(self, name: str, limit: int = 60) -> list[dict[str, Any]]:
        dq = {
            "cpu": self._cpu,
            "memory": self._mem,
            "latency": self._latency,
            "errors": self._errors,
            "traffic": self._traffic,
        }.get(name, self._cpu)
        pts = list(dq)[-limit:]
        return [{"t": p.ts, "v": round(p.value, 3)} for p in pts]


simulator = MetricsSimulator()


class KafkaSimulator:
    """In-process async queue simulating event streaming."""

    def __init__(self, max_size: int = 500) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_size)
        self._history: deque[dict[str, Any]] = deque(maxlen=max_size)

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        evt = {"topic": topic, "payload": payload, "ts": datetime.now(timezone.utc).isoformat()}
        self._history.append(evt)
        try:
            self._queue.put_nowait(evt)
        except asyncio.QueueFull:
            _ = self._queue.get_nowait()
            self._queue.put_nowait(evt)

    def recent(self, n: int = 50) -> list[dict[str, Any]]:
        return list(self._history)[-n:]


kafka_sim = KafkaSimulator()
