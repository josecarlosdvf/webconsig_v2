from fastapi import APIRouter

from app.api.v1.endpoints import audit, debug, financial, health, plugins, realtime

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(financial.router)
api_router.include_router(audit.router)
api_router.include_router(debug.router)
api_router.include_router(plugins.router)
api_router.include_router(realtime.router)
