from mcp.server.fastmcp import FastMCP
from app.config import get_settings
from app.core.orchestrator import Orchestrator

# Create an MCP server
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
    
    # We use analyze_async to get the full report non-blocking
    response = await orchestrator.analyze_async(idea)
    
    return response.model_dump_json()

if __name__ == "__main__":
    # Start the server using stdio
    mcp.run(transport="stdio")
