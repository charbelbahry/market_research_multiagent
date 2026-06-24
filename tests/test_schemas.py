import pytest
from pydantic import ValidationError
from app.schemas.report import AnalyzeRequest, FeasibilityReport


def _valid_report() -> dict:
    """Helper that returns a valid FeasibilityReport dict."""
    return {
        "idea": "An AI-powered study assistant for university students",
        "market_overview": "Growing edtech market valued at $400B",
        "competitors": [
            {
                "name": "Quizlet",
                "description": "Flashcard and study tool platform",
                "differentiator": "Large existing user base",
            }
        ],
        "opportunities": ["Personalized learning paths"],
        "gaps": ["No AI-native study tools for STEM"],
        "technical_feasibility": "Moderate — requires NLP and content generation",
        "risks": ["High competition from incumbents"],
        "recommendation": "build_with_caveats",
        "confidence": 0.72,
        "reasoning": "Strong demand but crowded market",
        "mvp_suggestion": "Start with a single subject like biology",
        "engine": "mock",
    }


def test_valid_report_constructs():
    """A fully valid payload should construct without error."""
    report = FeasibilityReport(**_valid_report())
    assert report.recommendation == "build_with_caveats"


def test_idea_too_short():
    """AnalyzeRequest rejects ideas shorter than 10 chars."""
    with pytest.raises(ValidationError):
        AnalyzeRequest(idea="hi")


def test_bad_recommendation():
    """recommendation must be one of the three allowed literals."""
    data = _valid_report()
    data["recommendation"] = "maybe_build"
    with pytest.raises(ValidationError):
        FeasibilityReport(**data)


def test_confidence_out_of_range():
    """confidence must be between 0 and 1."""
    data = _valid_report()
    data["confidence"] = 1.5
    with pytest.raises(ValidationError):
        FeasibilityReport(**data)


def test_extra_fields_rejected():
    """extra='forbid' should reject unknown fields."""
    data = _valid_report()
    data["junk_field"] = "should fail"
    with pytest.raises(ValidationError):
        FeasibilityReport(**data)
