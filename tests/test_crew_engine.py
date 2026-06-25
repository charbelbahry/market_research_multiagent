from unittest.mock import MagicMock
import pytest

from app.core.crew_engine import CrewEngine
from app.config import Settings
from app.schemas.report import FeasibilityReport


def test_crew_engine_kickoff(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake_key")
    settings = Settings(
        cheap_model_name="openrouter/google/gemini-2.0-flash-exp:free",
        strong_model_name="openrouter/deepseek/deepseek-r1:free"
    )
    
    engine = CrewEngine(settings)
    
    # Create a mock return value that simulates CrewAI's CrewOutput
    mock_report = FeasibilityReport(
        idea="A test idea",
        market_overview="Good market",
        competitors=[],
        opportunities=["gap 1"],
        gaps=["feature 1"],
        technical_feasibility="hard",
        risks=["risk 1"],
        recommendation="build",
        confidence=0.9,
        reasoning="Because I said so",
        mvp_suggestion="A CLI app",
        engine="mock"  # We'll assert that the engine overrides this to 'crew'
    )
    
    mock_output = MagicMock()
    mock_output.pydantic = mock_report
    mock_output.raw = "This is raw text."
    
    # Monkeypatch the kickoff method on the Crew class so we don't actually call an LLM
    monkeypatch.setattr("crewai.Crew.kickoff", lambda self, inputs: mock_output)
    
    report = engine.analyze("A test idea")
    
    # Ensure it returns the structured Pydantic object
    assert isinstance(report, FeasibilityReport)
    
    # Ensure the engine stamped it with "crew"
    assert report.engine == "crew"
    assert report.idea == "A test idea"
