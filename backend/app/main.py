import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from sqlalchemy.exc import OperationalError

from app.adapters.gateways.audit_gateway import AuditGateway
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.debug_store import push_debug_event
from app.core.logging import setup_logging
from app.core.realtime_hub import publish_event
from app.domain.models import audit, financial, idempotency, plugin  # noqa: F401

setup_logging()
logger = logging.getLogger("backend")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    logger.info("startup_complete", extra={"area": "backend"})
    publish_event(event_type="system.startup", payload={"message": "backend_ready"})


@app.exception_handler(OperationalError)
async def handle_db_operational_error(request: Request, exc: OperationalError):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    actor = request.headers.get("X-Actor", "anonymous")
    push_debug_event(
        source="backend",
        level="ERROR",
        message="database_unavailable",
        context={"error": str(exc)[:2000]},
        request_id=request_id,
        actor=actor,
        path=request.url.path,
    )

    db = SessionLocal()
    try:
        AuditGateway(db).append(
            area="backend",
            action="http.error.database_unavailable",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="http",
            http_method=request.method,
            http_path=request.url.path,
            status_code=503,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            severity="ERROR",
            detail={"error": str(exc)[:2000]},
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    logger.exception(
        "database_unavailable",
        extra={"area": "backend", "path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Banco de dados indisponível ou credenciais inválidas"},
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    actor = request.headers.get("X-Actor", "anonymous")
    push_debug_event(
        source="backend",
        level="ERROR",
        message="unhandled_exception",
        context={"error": str(exc)[:2000]},
        request_id=request_id,
        actor=actor,
        path=request.url.path,
    )

    db = SessionLocal()
    try:
        AuditGateway(db).append(
            area="backend",
            action="http.error.unhandled",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="http",
            http_method=request.method,
            http_path=request.url.path,
            status_code=500,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            severity="ERROR",
            detail={"error": str(exc)[:2000]},
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    logger.exception("unhandled_exception", extra={"area": "backend", "path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})


@app.middleware("http")
async def audit_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()

    should_skip_audit = (not settings.enable_request_audit) or (request.url.path in settings.excluded_paths)
    should_read_body = request.method in {"POST", "PUT", "PATCH", "DELETE"}

    body_preview = ""
    if should_read_body:
        raw_body = await request.body()
        body_preview = raw_body.decode("utf-8", errors="ignore")[: settings.request_log_body_limit]

    actor = request.headers.get("X-Actor", "anonymous")

    push_debug_event(
        source="backend",
        level="DEBUG",
        message="request_received",
        context={
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "body_preview": body_preview,
        },
        request_id=request_id,
        actor=actor,
        path=request.url.path,
    )

    logger.debug(
        "request_received",
        extra={
            "area": "backend",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "body_preview": body_preview,
            "user_id": actor,
        },
    )
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    push_debug_event(
        source="backend",
        level="DEBUG",
        message="request_completed",
        context={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
        request_id=request_id,
        actor=actor,
        path=request.url.path,
    )

    if not should_skip_audit:
        db = SessionLocal()
        try:
            AuditGateway(db).append(
                area="backend",
                action="http.request.completed",
                actor=actor,
                request_id=request_id,
                source="backend",
                resource="http",
                http_method=request.method,
                http_path=request.url.path,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                severity="INFO",
                detail={
                    "query": str(request.query_params),
                    "elapsed_ms": elapsed_ms,
                    "body_preview": body_preview,
                },
            )
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    logger.debug(
        "request_completed",
        extra={
            "area": "backend",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "user_id": actor,
        },
    )
    response.headers["X-Request-Id"] = request_id
    return response


app.include_router(api_router, prefix=settings.api_prefix)
