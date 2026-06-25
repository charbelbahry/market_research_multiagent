from crewai import Task, Agent
from app.schemas.report import FeasibilityReport


def build_tasks(agents: dict[str, Agent]) -> list[Task]:
    """Build and return the 4 tasks for the feasibility pipeline.
    
    The tasks are chained via `context` to form a dependency graph.
    """
    
    research_task = Task(
        description=(
            "Research the product idea: {idea}. Use your web_search tool to find "
            "concrete demand signals, competitor products, and market context. "
            "Ensure you extract factual data rather than generic statements."
        ),
        expected_output="A bulleted list of demand signals, named competitors, and cited sources.",
        agent=agents["research"],
    )

    market_task = Task(
        description=(
            "Based on the research provided, analyze the target audience, demand viability, "
            "and competitive landscape for the idea: {idea}."
        ),
        expected_output="A comprehensive market overview, a list of competitors with differentiators, and identified market opportunities/gaps.",
        agent=agents["market"],
        context=[research_task],  # Depends on research
    )

    risk_task = Task(
        description=(
            "Using the research and market analysis, rigorously evaluate the technical, "
            "market, cost, and feasibility risks for the idea: {idea}."
        ),
        expected_output="A categorized list of severe to moderate risks.",
        agent=agents["risk"],
        context=[research_task, market_task],  # Depends on both
    )

    decision_task = Task(
        description=(
            "Synthesize all the research, market analysis, and risk evaluations for the idea: {idea}. "
            "Make a definitive, final recommendation on whether to build this product or not. "
            "Provide clear reasoning, confidence score, and a potential MVP suggestion if applicable."
        ),
        expected_output="A fully populated FeasibilityReport JSON.",
        agent=agents["strategy"],
        context=[research_task, market_task, risk_task],  # Depends on all prior steps
        output_pydantic=FeasibilityReport,  # Structured output
    )

    return [research_task, market_task, risk_task, decision_task]
