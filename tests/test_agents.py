from app.agents.agents import build_agents
from app.config import Settings
from app.tools.search_tool import WebSearchTool


def test_build_agents(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")
    settings = Settings(
        cheap_model_name="gpt-4o-mini",
        strong_model_name="gpt-4o"
    )
    
    # We pass tools explicitly so we don't accidentally initialize a real tool if we don't want to
    tools = {"web_search": WebSearchTool()}
    
    agents = build_agents(settings, tools)
    
    assert len(agents) == 4
    assert "research" in agents
    assert "market" in agents
    assert "risk" in agents
    assert "strategy" in agents
    
    # Check roles
    assert agents["research"].role == "Senior Product Researcher"
    assert agents["market"].role == "Market Analyst"
    assert agents["risk"].role == "Risk & Feasibility Analyst"
    assert agents["strategy"].role == "Head of Strategy"
    
    # Check tools (only researcher has the search tool)
    assert len(agents["research"].tools) == 1
    assert agents["research"].tools[0].name == "web_search"
    
    assert len(agents["market"].tools) == 0
    assert len(agents["risk"].tools) == 0
    assert len(agents["strategy"].tools) == 0
    
    # Check multi-model routing
    assert agents["research"].llm.model == "gpt-4o-mini"
    assert agents["market"].llm.model == "gpt-4o-mini"
    assert agents["risk"].llm.model == "gpt-4o-mini"
    assert agents["strategy"].llm.model == "gpt-4o"
    
    # Check delegation is off
    assert not agents["research"].allow_delegation
    assert not agents["market"].allow_delegation
    assert not agents["risk"].allow_delegation
    assert not agents["strategy"].allow_delegation
