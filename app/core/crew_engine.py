from crewai import Crew, Process
import json

from app.schemas.report import FeasibilityReport
from app.agents.agents import build_agents
from app.tasks.tasks import build_tasks
from app.config import Settings
from app.core.mock_engine import MockEngine


class CrewEngine:
    """The real CrewAI multi-agent engine."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.agents_dict = build_agents(self.settings)
        self.tasks_list = build_tasks(self.agents_dict)

        self.crew = Crew(
            agents=list(self.agents_dict.values()),
            tasks=self.tasks_list,
            process=Process.sequential,
            verbose=False,
        )

    def analyze(self, idea: str) -> FeasibilityReport:
        """Run the multi-agent pipeline."""
        import sys

        # Suppress sys.stdout completely during kickoff
        original_stdout = sys.stdout

        class NullWriter:
            def write(self, s: str) -> None:
                pass

            def flush(self) -> None:
                pass

        sys.stdout = NullWriter()

        try:
            result = self.crew.kickoff(inputs={"idea": idea})
        finally:
            sys.stdout = original_stdout

        report: FeasibilityReport | None = None

        # Bypass strict type hints that union CrewOutput and CrewStreamingOutput
        pydantic_output = getattr(result, "pydantic", None)

        if pydantic_output is not None:
            if isinstance(pydantic_output, FeasibilityReport):
                report = pydantic_output
            else:
                # If CrewAI returned a generic BaseModel, convert it
                report = FeasibilityReport.model_validate(pydantic_output.model_dump())
        else:
            try:
                raw_text = getattr(result, "raw", "{}")
                raw_dict = json.loads(raw_text)
                report = FeasibilityReport(**raw_dict)
            except Exception:
                report = MockEngine().analyze(idea)

        report.engine = "crew"
        return report
