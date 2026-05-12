from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def readiness_probe() -> dict[str, str]:
    return {"status": "ok"}
