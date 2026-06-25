import time

from app.config import Settings
from app.core.mock_engine import MockEngine
from app.schemas.report import AnalyzeMeta, AnalyzeResponse, FeasibilityReport
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CrewEngine:
    """Stub for the real LLM engine, to be implemented in M6."""

    def analyze(self, idea: str) -> FeasibilityReport:
        # For now, it just delegates to the mock engine
        # In M6 this will be replaced with actual CrewAI logic
        return MockEngine().analyze(idea)


class Orchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mock_engine = MockEngine()
        self.crew_engine = CrewEngine()

    def analyze(self, idea: str) -> AnalyzeResponse:
        start_time = time.time()

        use_real = self.settings.use_real_crew

        if use_real:
            logger.info(f"Using CrewEngine for idea length {len(idea)}")
            engine_to_use = self.crew_engine  # type: ignore
        else:
            logger.info(f"Using MockEngine for idea length {len(idea)}")
            engine_to_use = self.mock_engine  # type: ignore

        report = engine_to_use.analyze(idea)

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Analysis complete. Engine: {report.engine}, Duration: {duration_ms}ms"
        )

        meta = AnalyzeMeta(
            duration_ms=duration_ms,
            model=None,  # Will be populated by CrewEngine in M6
        )

        return AnalyzeResponse(report=report, meta=meta)
