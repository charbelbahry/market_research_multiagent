import pytest
import json
from app.mcp.server import analyze_idea
from app.config import get_settings


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("USE_REAL_CREW", "false")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_mcp_tool_analyze_idea():
    idea = "Should I build an AI study assistant?"

    result_str = await analyze_idea(idea)

    # Must return a valid JSON string
    assert isinstance(result_str, str)

    data = json.loads(result_str)

    # Must contain the response wrapper
    assert "report" in data
    assert "meta" in data

    # Meta should indicate degraded/mock if USE_REAL_CREW is false
    assert data["report"]["engine"] == "mock"
