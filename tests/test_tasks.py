from app.tasks.tasks import build_tasks
from app.agents.agents import build_agents
from app.schemas.report import FeasibilityReport
from app.config import Settings
from app.tools.search_tool import WebSearchTool


def test_build_tasks(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake_key")
    settings = Settings(
        cheap_model_name="openrouter/google/gemini-2.0-flash-exp:free",
        strong_model_name="openrouter/deepseek/deepseek-r1:free"
    )
    tools = {"web_search": WebSearchTool()}
    agents = build_agents(settings, tools)
    tasks = build_tasks(agents)
    
    assert len(tasks) == 4
    
    research_task, market_task, risk_task, decision_task = tasks
    
    # Assert context dependencies (the core of the sequential graph)
    assert market_task.context is not None
    assert len(market_task.context) == 1
    assert market_task.context[0] == research_task
    
    assert risk_task.context is not None
    assert len(risk_task.context) == 2
    assert risk_task.context[0] == research_task
    assert risk_task.context[1] == market_task
    
    assert decision_task.context is not None
    assert len(decision_task.context) == 3
    assert decision_task.context[0] == research_task
    assert decision_task.context[1] == market_task
    assert decision_task.context[2] == risk_task
    
    # Assert structured output is attached only to the final task
    assert decision_task.output_pydantic == FeasibilityReport
