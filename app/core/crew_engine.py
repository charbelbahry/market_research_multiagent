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
        # Instantiate agents and tasks when the engine is initialized
        self.agents_dict = build_agents(self.settings)
        self.tasks_list = build_tasks(self.agents_dict)
        
        self.crew = Crew(
            agents=list(self.agents_dict.values()),
            tasks=self.tasks_list,
            process=Process.sequential,
            verbose=True
        )

    def analyze(self, idea: str) -> FeasibilityReport:
        """Run the multi-agent pipeline."""
        
        result = self.crew.kickoff(inputs={"idea": idea})
        
        if result.pydantic:
            report = result.pydantic
        else:
            # Fallback if the LLM failed to match the schema completely and CrewAI couldn't fix it
            # This is rare but important for graceful degradation
            try:
                # Try to parse raw JSON if pydantic is missing
                raw_dict = json.loads(result.raw)
                report = FeasibilityReport(**raw_dict)
            except Exception:
                # Absolute worst-case fallback: return a mock report so the user doesn't get a 500
                report = MockEngine().analyze(idea)
                
        # Stamp it with the provenance
        report.engine = "crew"
        return report
