from crewai import Agent, LLM
from crewai.tools import BaseTool

from app.config import Settings
from app.tools.search_tool import WebSearchTool


def build_llm(model_name: str, temperature: float = 0.3) -> LLM:
    return LLM(model=model_name, temperature=temperature)


def build_agents(
    settings: Settings, tools: dict[str, BaseTool] | None = None
) -> dict[str, Agent]:
    """Build and return the 4 core agents for the feasibility pipeline."""

    if tools is None:
        tools = {"web_search": WebSearchTool()}

    cheap_llm = build_llm(settings.cheap_model_name)
    strong_llm = build_llm(settings.strong_model_name)

    researcher = Agent(
        role="Senior Product Researcher",
        goal="Gather concrete demand signals, competitor data, and market context for: {idea}",
        backstory="You are a meticulous researcher who only trusts evidence that can be cited. You excel at extracting factual signals from noise.",
        tools=[tools["web_search"]],
        llm=cheap_llm,
        allow_delegation=False,
        verbose=True,
    )

    market_analyst = Agent(
        role="Market Analyst",
        goal="Assess target audience, demand viability, and competitive landscape for: {idea}",
        backstory="You are an expert at finding market gaps and understanding consumer behavior. You analyze raw research and turn it into market insights.",
        tools=[],
        llm=cheap_llm,
        allow_delegation=False,
        verbose=True,
    )

    risk_analyst = Agent(
        role="Risk & Feasibility Analyst",
        goal="Evaluate technical, market, cost, and feasibility risks for: {idea}",
        backstory="You are a pragmatic skeptic. You easily identify why a product might fail, highlighting technical barriers, market saturation, and hidden costs.",
        tools=[],
        llm=cheap_llm,
        allow_delegation=False,
        verbose=True,
    )

    strategy_head = Agent(
        role="Head of Strategy",
        goal="Synthesize all findings into a final build / don't-build recommendation with an MVP strategy for: {idea}",
        backstory="You are an elite product strategist. You weigh risks against market opportunities to make decisive, actionable recommendations.",
        tools=[],
        llm=strong_llm,
        allow_delegation=False,
        verbose=True,
    )

    return {
        "research": researcher,
        "market": market_analyst,
        "risk": risk_analyst,
        "strategy": strategy_head,
    }
