from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymilvus import connections, utility
from pymongo import MongoClient

from app.api import chat_api, memory_api, pattern_api, task_api
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import configure_logging, get_logger

logger = get_logger(__name__)


def check_mongodb(settings: Settings) -> dict[str, str]:
    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1000)
    client.admin.command("ping")
    client.close()
    return {"status": "ok"}


def check_milvus(settings: Settings) -> dict[str, str]:
    alias = "startup_check"
    connections.connect(alias=alias, host=settings.milvus_host, port=settings.milvus_port)
    try:
        has_collection = utility.has_collection(settings.milvus_collection, using=alias)
        return {"status": "ok", "collection_exists": str(has_collection).lower()}
    finally:
        connections.disconnect(alias)


def check_startup_dependencies(settings: Settings) -> dict[str, dict[str, str]]:
    """Probe MongoDB and Milvus reachability on startup.

    This runs in *health-check mode*: failures are recorded but do not block
    the application from starting.  The authoritative dependency status is
    exposed via ``GET /health/dependencies`` so downstream operators or
    orchestrators can decide whether to route traffic, retry, or alert.
    """
    results: dict[str, dict[str, str]] = {}
    for name, check in (("mongodb", check_mongodb), ("milvus", check_milvus)):
        try:
            results[name] = check(settings)
            logger.info("%s startup check passed", name, extra={"dependency": name})
        except Exception as exc:
            results[name] = {"status": "error", "message": str(exc)}
            logger.warning(
                "%s startup check failed: %s",
                name,
                exc,
                extra={"dependency": name},
            )
    return results


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.settings = settings
    app.state.dependencies = check_startup_dependencies(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Memory-Driven Growth Agent", lifespan=lifespan)
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat_api.router)
    app.include_router(memory_api.router)
    app.include_router(pattern_api.router)
    app.include_router(task_api.router)
    return app


app = create_app()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/dependencies")
async def dependency_health() -> dict[str, Any]:
    return getattr(app.state, "dependencies", {})
