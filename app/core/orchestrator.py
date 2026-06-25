import time

from app.config import Settings
from app.core.mock_engine import MockEngine
from app.schemas.report import AnalyzeMeta, AnalyzeResponse, FeasibilityReport
from app.utils.logging import get_logger

logger = get_logger(__name__)


from app.core.crew_engine import CrewEngine

class Orchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mock_engine = MockEngine()
        self.crew_engine = CrewEngine(settings)

    def analyze(self, idea: str) -> AnalyzeResponse:
        start_time = time.time()

        use_real = self.settings.use_real_crew

        if use_real:
            logger.info("Using CrewEngine", extra={"idea_length": len(idea), "engine_used": "crew"})
            engine_to_use = self.crew_engine  # type: ignore
        else:
            logger.info("Using MockEngine", extra={"idea_length": len(idea), "engine_used": "mock"})
            engine_to_use = self.mock_engine  # type: ignore

        report = engine_to_use.analyze(idea)

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Analysis complete",
            extra={
                "engine_used": report.engine,
                "duration_ms": duration_ms,
                "idea_length": len(idea),
            }
        )

        meta = AnalyzeMeta(
            duration_ms=duration_ms,
            model=None,
        )

        return AnalyzeResponse(report=report, meta=meta)
