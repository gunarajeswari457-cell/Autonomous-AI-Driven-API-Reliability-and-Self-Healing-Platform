import random
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.metrics_simulator import kafka_sim, simulator


def _now() -> datetime:
    return datetime.now(timezone.utc)


def failure_prediction_bundle() -> dict[str, Any]:
    snap = simulator.snapshot()
    risk = round(min(100, max(5, (1 - snap["api_health_score"] / 100) * 100 + random.random() * 12)), 2)
    downtime = _now() + timedelta(minutes=int(5 + random.random() * 90))
    return {
        "failure_probability": snap["failure_probability"],
        "risk_score": risk,
        "ai_confidence_percent": snap["ai_confidence_percent"],
        "predicted_downtime_at": downtime.isoformat(),
        "signals": {
            "overload": round(random.uniform(0.1, 0.95), 3),
            "latency_spike": round(random.uniform(0.05, 0.88), 3),
            "memory_pressure": round(random.uniform(0.1, 0.9), 3),
            "downtime_window_minutes": int(10 + random.random() * 80),
        },
        "forecast": [
            {
                "t": (_now() + timedelta(minutes=i * 5)).isoformat(),
                "p_fail": round(min(0.99, snap["failure_probability"] * (1 + (i - 6) * 0.02)), 4),
            }
            for i in range(18)
        ],
        "explanations": [
            "Elevated p95 latency correlates with GC pressure on primary API nodes.",
            "Traffic skew toward checkout shard increases saturation risk during peak.",
            "Error budget burn is accelerating vs. trailing 24h baseline.",
        ],
    }


def anomaly_report() -> dict[str, Any]:
    return {
        "unusual_traffic": round(random.uniform(0.2, 0.95), 3),
        "suspicious_patterns": round(random.uniform(0.05, 0.6), 3),
        "error_spike": round(random.uniform(0.1, 0.9), 3),
        "notes": [
            "Burst RPS +2.4σ vs seasonal baseline in us-east-1.",
            "5xx ratio diverged from dependency latency (upstream not culprit).",
        ],
    }


def root_cause_bundle() -> dict[str, Any]:
    return {
        "primary_hypothesis": "Memory pressure on payments-api causing thread pool starvation.",
        "severity": random.choice(["SEV-3", "SEV-2", "SEV-3"]),
        "impact": {
            "users_affected_estimate": int(1200 + random.random() * 9000),
            "revenue_at_risk_usd": int(5000 + random.random() * 45000),
            "blast_radius": "payments + checkout read path",
        },
        "ai_root_causes": [
            {
                "title": "GC thrash on JVM heap boundary",
                "confidence": round(72 + random.random() * 18, 1),
                "evidence": ["heap usage 91%", "p99 GC pause +340%", "allocation rate spike"],
            },
            {
                "title": "Downstream DB connection pool exhaustion",
                "confidence": round(55 + random.random() * 15, 1),
                "evidence": ["wait time on pool.acquire()", "idle connections ~0"],
            },
        ],
        "topology": {
            "nodes": [
                {"id": "gw", "label": "Edge Gateway", "health": 0.96},
                {"id": "api", "label": "Core API", "health": 0.78},
                {"id": "pay", "label": "Payments API", "health": 0.62},
                {"id": "db", "label": "Primary DB", "health": 0.88},
                {"id": "cache", "label": "Redis", "health": 0.93},
                {"id": "queue", "label": "Kafka", "health": 0.9},
            ],
            "edges": [
                {"from": "gw", "to": "api", "load": 0.74},
                {"from": "api", "to": "pay", "load": 0.81},
                {"from": "api", "to": "cache", "load": 0.45},
                {"from": "pay", "to": "db", "load": 0.69},
                {"from": "pay", "to": "queue", "load": 0.52},
            ],
        },
    }


def security_bundle() -> dict[str, Any]:
    return {
        "suspicious_traffic_score": round(random.uniform(0.08, 0.55), 3),
        "ddos_likelihood": round(random.uniform(0.02, 0.35), 3),
        "blocked_requests_1h": int(120 + random.random() * 4000),
        "threat_analytics": {
            "waf_rules_triggered": int(3 + random.random() * 40),
            "geo_anomalies": int(0 + random.random() * 8),
            "credential_stuffing": round(random.uniform(0.01, 0.22), 3),
        },
        "recent_blocks": [
            {"ip": "198.51.100.12", "reason": "rate limit", "ts": _now().isoformat()},
            {"ip": "203.0.113.44", "reason": "bot signature", "ts": (_now() - timedelta(minutes=3)).isoformat()},
        ],
    }


async def chat_reply(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    m = message.lower()
    snap = simulator.snapshot()
    pred = failure_prediction_bundle()
    rc = root_cause_bundle()
    if "fail" in m or "why" in m:
        answer = (
            f"Likely driver: {rc['primary_hypothesis']} Current health score {snap['api_health_score']:.1f} "
            f"with failure probability {snap['failure_probability']*100:.2f}%."
        )
    elif "health" in m or "status" in m:
        answer = (
            f"System health score {snap['api_health_score']:.1f}. Active alerts {snap['active_alerts']}. "
            f"p95 latency {snap['latency_ms_p95']:.0f}ms."
        )
    elif "recover" in m or "heal" in m or "fix" in m:
        answer = (
            "Suggested sequence: drain traffic → restart payments-api pods → clear hot cache keys for checkout, "
            "then validate DB pool sizing. I can run simulated healing actions from the Self-Healing page."
        )
    elif "predict" in m or "confidence" in m:
        answer = (
            f"Model confidence {pred['ai_confidence_percent']:.1f}% with risk score {pred['risk_score']:.1f}. "
            f"Predicted incident window near {pred['predicted_downtime_at']}."
        )
    else:
        answer = (
            "I correlate live metrics, traces, and dependency health. Ask about failures, health, recovery, "
            "or prediction confidence for a tailored briefing."
        )
    await kafka_sim.publish(
        "ai.chat",
        {"message": message[:500], "answer_preview": answer[:180]},
    )
    return {"answer": answer, "context_used": bool(context)}
