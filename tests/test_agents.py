from app.agents.agents import build_agents
from app.config import Settings
from app.tools.search_tool import WebSearchTool


def test_build_agents(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake_key")
    settings = Settings(
        cheap_model_name="openrouter/openai/gpt-4o-mini",
        strong_model_name="openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
    )

    tools = {"web_search": WebSearchTool()}

    agents = build_agents(settings, tools)

    assert len(agents) == 4
    assert "research" in agents
    assert "market" in agents
    assert "risk" in agents
    assert "strategy" in agents

    assert agents["research"].role == "Senior Product Researcher"
    assert agents["market"].role == "Market Analyst"
    assert agents["risk"].role == "Risk & Feasibility Analyst"
    assert agents["strategy"].role == "Head of Strategy"

    assert len(agents["research"].tools) == 1
    assert agents["research"].tools[0].name == "web_search"

    assert len(agents["market"].tools) == 0
    assert len(agents["risk"].tools) == 0
    assert len(agents["strategy"].tools) == 0

    assert agents["research"].llm.model == "openrouter/openai/gpt-4o-mini"
    assert agents["market"].llm.model == "openrouter/openai/gpt-4o-mini"
    assert agents["risk"].llm.model == "openrouter/openai/gpt-4o-mini"
    assert (
        agents["strategy"].llm.model
        == "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"
    )

    assert not agents["research"].allow_delegation
    assert not agents["market"].allow_delegation
    assert not agents["risk"].allow_delegation
    assert not agents["strategy"].allow_delegation
