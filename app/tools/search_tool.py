import os
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.config import get_settings
from app.tools.mock_search import get_mock_search_results


class SearchInput(BaseModel):
    query: str = Field(..., description="Search query for market/competitor research")
    max_results: int = Field(
        default=5, ge=1, le=10, description="Max number of results to return."
    )


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for market data, competitors, and demand signals."
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        settings = get_settings()

        try:
            if settings.serper_api_key:
                from crewai_tools import SerperDevTool

                os.environ["SERPER_API_KEY"] = settings.serper_api_key
                tool = SerperDevTool(n_results=max_results)
                return str(tool._run(search_query=query))

            elif settings.tavily_api_key:
                from crewai_tools import TavilySearchTool

                os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
                tavily_tool = TavilySearchTool()
                return str(tavily_tool._run(query=query))

            else:
                return get_mock_search_results(query)

        except Exception as e:
            return f"Error executing search for '{query}': {str(e)}"
