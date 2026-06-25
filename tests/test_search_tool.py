import pytest
from pydantic import ValidationError

from app.config import Settings
from app.tools.search_tool import SearchInput, WebSearchTool


def test_search_input_validation():
    SearchInput(query="test", max_results=5)

    with pytest.raises(ValidationError):
        SearchInput(query="test", max_results=99)

    with pytest.raises(ValidationError):
        SearchInput(query="test", max_results=0)


def test_web_search_tool_mock_fallback(monkeypatch):
    monkeypatch.setattr(
        "app.tools.search_tool.get_settings",
        lambda: Settings(serper_api_key=None, tavily_api_key=None),
    )

    tool = WebSearchTool()
    result = tool._run(query="competitor analysis")

    assert "Market Leader Corp" in result
    assert "Agile Startup Inc" in result


def test_web_search_tool_serper(monkeypatch):
    monkeypatch.setattr(
        "app.tools.search_tool.get_settings",
        lambda: Settings(serper_api_key="fake_key", tavily_api_key=None),
    )

    class FakeSerper:
        def __init__(self, **kwargs):
            pass

        def _run(self, search_query: str):
            return "Fake Serper Result"

    monkeypatch.setattr("crewai_tools.SerperDevTool", FakeSerper)

    tool = WebSearchTool()
    result = tool._run(query="AI trends")

    assert result == "Fake Serper Result"


def test_web_search_tool_tavily(monkeypatch):
    monkeypatch.setattr(
        "app.tools.search_tool.get_settings",
        lambda: Settings(tavily_api_key="fake_key", serper_api_key=None),
    )

    class FakeTavily:
        def __init__(self, **kwargs):
            pass

        def _run(self, query: str):
            return "Fake Tavily Result"

    monkeypatch.setattr("crewai_tools.TavilySearchTool", FakeTavily)

    tool = WebSearchTool()
    result = tool._run(query="AI trends")

    assert result == "Fake Tavily Result"


def test_web_search_tool_handles_exceptions(monkeypatch):
    monkeypatch.setattr(
        "app.tools.search_tool.get_settings",
        lambda: Settings(serper_api_key="fake_key", tavily_api_key=None),
    )

    class FailingSerper:
        def __init__(self, **kwargs):
            pass

        def _run(self, search_query: str):
            raise ValueError("API quota exceeded")

    monkeypatch.setattr("crewai_tools.SerperDevTool", FailingSerper)

    tool = WebSearchTool()
    result = tool._run(query="AI trends")

    assert "Error executing search" in result
    assert "API quota exceeded" in result
