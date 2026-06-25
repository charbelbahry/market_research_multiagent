from fastapi import APIRouter, Depends, status

from app.config import Settings, get_settings
from app.core.orchestrator import Orchestrator
from app.schemas.report import AnalyzeRequest, AnalyzeResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", status_code=status.HTTP_200_OK)
def check_health():
    return {"status": "ok", "engine": "CrewAI" if settings.use_real_crew else "Mock"}


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
def analyze_idea(request: AnalyzeRequest, settings: Settings = Depends(get_settings)):
    orchestrator = Orchestrator(settings)
    return orchestrator.analyze(request.idea)
