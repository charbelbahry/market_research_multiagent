import sys
from pathlib import Path

# Ensure the project root is in sys.path so 'from app...' works when run as a script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP
from app.config import get_settings
from app.core.orchestrator import Orchestrator

mcp = FastMCP("MarketResearchAnalyzer")


@mcp.tool()
async def analyze_idea(idea: str) -> str:
    """
    Analyze a product idea's feasibility using a multi-agent AI pipeline.

    Args:
        idea: A detailed string describing the product idea.

    Returns:
        A JSON string containing the feasibility report (market overview, competitors, risks, recommendation, etc.)
    """
    settings = get_settings()
    orchestrator = Orchestrator(settings)

    response = await orchestrator.analyze_async(idea)

    return response.model_dump_json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
