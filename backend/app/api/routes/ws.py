import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.services.metrics_simulator import kafka_sim, simulator

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def metrics_broadcaster() -> None:
    try:
        while True:
            snap = simulator.snapshot()
            snap["type"] = "metrics"
            await manager.broadcast(snap)
            await kafka_sim.publish("metrics.stream", {"health": snap["api_health_score"]})
            await asyncio.sleep(2.0)
    except asyncio.CancelledError:
        return


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=4401)
        return
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "type": "hello",
                "message": "stream connected",
                "user": payload["sub"],
                "server_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        while True:
            # keepalive / allow client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "ts": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
