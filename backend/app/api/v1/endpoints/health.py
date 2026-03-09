from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Healthcheck")
def health() -> dict:
    return {"status": "ok"}
