from app.core.crew_engine import CrewEngine

import time

from app.config import Settings
from app.core.mock_engine import MockEngine
from app.schemas.report import AnalyzeMeta, AnalyzeResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)


class Orchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mock_engine = MockEngine()
        self.crew_engine = CrewEngine(settings)

    async def analyze_async(self, idea: str) -> AnalyzeResponse:
        import asyncio

        start_time = time.time()

        use_real = self.settings.use_real_crew
        degraded = False
        report = None

        if use_real:
            logger.info(
                "Starting CrewEngine in background thread",
                extra={"idea_length": len(idea)},
            )
            try:
                # Offload blocking CrewAI execution to a worker thread so we don't block the FastAPI event loop
                report = await asyncio.wait_for(
                    asyncio.to_thread(self.crew_engine.analyze, idea),
                    timeout=self.settings.request_timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "CrewEngine timed out, gracefully degrading to mock",
                    extra={"timeout": self.settings.request_timeout_seconds},
                )
                degraded = True
                report = self.mock_engine.analyze(idea)
            except Exception as e:
                logger.error(f"CrewEngine failed unexpectedly: {e}", exc_info=True)
                degraded = True
                report = self.mock_engine.analyze(idea)
        else:
            logger.info(
                "Using MockEngine",
                extra={"idea_length": len(idea), "engine_used": "mock"},
            )
            # Mock engine is instant, no need to thread it
            report = self.mock_engine.analyze(idea)

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Analysis complete",
            extra={
                "engine_used": report.engine,
                "duration_ms": duration_ms,
                "idea_length": len(idea),
                "degraded": degraded,
            },
        )

        meta = AnalyzeMeta(duration_ms=duration_ms, model=None, degraded=degraded)

        return AnalyzeResponse(report=report, meta=meta)
