from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.services.ai_engine import anomaly_report, failure_prediction_bundle, root_cause_bundle, security_bundle
from app.services.api_registry import api_catalog, api_logs, traffic_spike_series
from app.services.healing import healing_service
from app.services.metrics_simulator import kafka_sim, simulator
from app.services.redis_cache import cache_get_json, cache_set_json

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/metrics/live")
async def live_metrics(_: User = Depends(get_current_user)):
    return simulator.snapshot()


@router.get("/metrics/series/{name}")
async def metrics_series(name: str, _: User = Depends(get_current_user)):
    allowed = {"cpu", "memory", "latency", "errors", "traffic"}
    if name not in allowed:
        name = "cpu"
    return {"name": name, "points": simulator.series(name)}


@router.get("/apis")
async def list_apis(_: User = Depends(get_current_user)):
    cached = await cache_get_json("apis:catalog")
    if cached:
        return cached
    data = {"items": api_catalog(), "traffic_spike": traffic_spike_series()}
    await cache_set_json("apis:catalog", data, ttl=8)
    return data


@router.get("/apis/{api_id}/logs")
async def logs(api_id: str, _: User = Depends(get_current_user)):
    return {"api_id": api_id, "logs": api_logs(api_id)}


@router.get("/ai/predictions")
async def predictions(_: User = Depends(get_current_user)):
    return failure_prediction_bundle()


@router.get("/ai/anomalies")
async def anomalies(_: User = Depends(get_current_user)):
    return anomaly_report()


@router.get("/ai/root-cause")
async def root_cause(_: User = Depends(get_current_user)):
    return root_cause_bundle()


@router.get("/security/summary")
async def security(_: User = Depends(get_current_user)):
    return security_bundle()


@router.get("/events/recent")
async def recent_events(_: User = Depends(get_current_user)):
    return {"events": kafka_sim.recent(80)}


@router.get("/healing/logs")
async def healing_logs(_: User = Depends(get_current_user)):
    return {"logs": healing_service.logs()}


@router.post("/healing/actions/{action}")
async def healing_action(action: str, _: User = Depends(get_current_user)):
    normalized = action.strip().lower().replace("-", "_")
    aliases = {
        "rollback_deployment": "rollback",
        "scale": "scale_containers",
        "restart": "restart_service",
    }
    normalized = aliases.get(normalized, normalized)
    allowed = {"restart_service", "scale_containers", "restart_pods", "failover", "clear_cache", "rollback"}
    if normalized not in allowed:
        normalized = "restart_service"
    return await healing_service.run_action(normalized)
