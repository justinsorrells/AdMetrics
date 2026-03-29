"""Health-check route."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple liveness payload."""

    return {"status": "ok"}
