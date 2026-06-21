import random
from datetime import datetime, timezone
from typing import Any

from app.services.metrics_simulator import simulator


def api_catalog() -> list[dict[str, Any]]:
    names = [
        ("auth-service", "Authentication"),
        ("payments-api", "Payments"),
        ("inventory-svc", "Inventory"),
        ("checkout-bff", "Checkout BFF"),
        ("recommendations", "Recommendations"),
        ("search-index", "Search"),
        ("notifications", "Notifications"),
        ("billing-webhook", "Billing Webhooks"),
    ]
    regions = ["us-east-1", "eu-west-1", "ap-south-1"]
    out: list[dict[str, Any]] = []
    for slug, title in names:
        healthy = random.random() > 0.12
        p95 = round(40 + random.random() * 220, 1)
        succ = round(94 + random.random() * 5.5, 2) if healthy else round(70 + random.random() * 20, 2)
        out.append(
            {
                "id": slug,
                "name": title,
                "region": random.choice(regions),
                "status": "healthy" if healthy else random.choice(["degraded", "failing"]),
                "p95_ms": p95,
                "success_rate": succ,
                "rps": round(50 + random.random() * 900, 1),
                "last_error": None
                if healthy
                else random.choice(["503 upstream", "timeout", "connection reset"]),
            }
        )
    return out


def api_logs(api_id: str, n: int = 40) -> list[dict[str, Any]]:
    levels = ["INFO", "WARN", "ERROR"]
    msgs = [
        "request completed",
        "retrying upstream",
        "circuit half-open",
        "cache miss",
        "db slow query",
        "rate limit near threshold",
    ]
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(n):
        lvl = random.choices(levels, weights=[0.78, 0.15, 0.07])[0]
        rows.append(
            {
                "ts": (now.timestamp() - i * 1.7),
                "level": lvl,
                "message": f"[{api_id}] {random.choice(msgs)}",
                "trace_id": f"tr_{random.randint(100000,999999)}",
            }
        )
    return rows


def traffic_spike_series() -> list[dict[str, Any]]:
    snap = simulator.snapshot()
    base = snap["network_rps"] * 0.01
    return [{"t": i, "rps": round(base * (1 + 0.35 * random.random()), 3)} for i in range(48)]
