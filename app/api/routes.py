from fastapi import APIRouter, status
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", status_code=status.HTTP_200_OK)
def check_health():
    return {"status": "ok", "engine": "CrewAI" if settings.use_real_crew else "Mock"}
