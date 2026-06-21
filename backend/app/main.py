import asyncio
from contextlib import asynccontextmanager

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, chat, platform, ws
from app.core.config import get_settings
from app.db.session import init_db
from app.services.metrics_simulator import kafka_sim

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # seed kafka sim
    await kafka_sim.publish("system.boot", {"service": "api-platform"})
    broadcaster = asyncio.create_task(ws.metrics_broadcaster())
    yield
    broadcaster.cancel()
    try:
        await broadcaster
    except Exception:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)
logger = logging.getLogger(__name__)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(platform.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ws.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
