import sys
from pathlib import Path

# Ensure the project root is in sys.path so 'from app...' works when run as a script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os  # noqa: E402

os.environ["CREWAI_DISABLE_TELEMETRY"] = "1"
os.environ["OTEL_SDK_DISABLED"] = "true"

# Save original stdout before CrewAI has a chance to hijack it
original_stdout = sys.stdout

import rich.console  # noqa: E402

rich.console.Console.print = lambda *args, **kwargs: None  # type: ignore

try:
    import crewai.utilities.printer

    crewai.utilities.printer.Printer.print = lambda *args, **kwargs: None  # type: ignore
except ImportError:
    pass

from mcp.server.fastmcp import FastMCP  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.core.orchestrator import Orchestrator  # noqa: E402

# Restore original stdout. CrewAI's llm.py violently monkeypatches sys.stdout
# to filter LiteLLM logs, which completely corrupts MCP's stdio protocol.
sys.stdout = original_stdout

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

    import os
    import sys

    # Save original fd 1
    original_fd = os.dup(1)
    # Redirect fd 1 to fd 2 (stderr)
    os.dup2(2, 1)

    try:
        response = await orchestrator.analyze_async(idea)
    finally:
        sys.stdout.flush()
        # Restore fd 1
        os.dup2(original_fd, 1)
        os.close(original_fd)

    return response.model_dump_json()


if __name__ == "__main__":
    import logging

    # Strip any handlers that CrewAI/rich might have added to the root logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    mcp.run(transport="stdio")
