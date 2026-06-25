from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class AnalyzeRequest(BaseModel):
    """The incoming request body for POST /analyze."""

    model_config = ConfigDict(extra="forbid")

    idea: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The product idea to analyze for feasibility.",
    )


class Competitor(BaseModel):
    """A competing product identified during analysis."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Name of the competing product or company.",
    )
    description: str = Field(
        ...,
        description="Brief description of what the competitor offers.",
    )
    differentiator: str | None = Field(
        default=None,
        description="What makes this competitor unique or different, if known.",
    )


class FeasibilityReport(BaseModel):
    """The complete feasibility analysis report."""

    model_config = ConfigDict(extra="forbid")

    idea: str = Field(
        ...,
        description="The original product idea that was analyzed.",
    )
    market_overview: str = Field(
        ...,
        description="High-level summary of the market landscape and demand signals.",
    )
    competitors: list[Competitor] = Field(
        ...,
        description="List of identified competing products or services.",
    )
    opportunities: list[str] = Field(
        ...,
        description="Market opportunities and gaps the idea could exploit.",
    )
    gaps: list[str] = Field(
        ...,
        description="Unmet needs or underserved segments in the market.",
    )
    technical_feasibility: str = Field(
        ...,
        description="Assessment of technical complexity, required stack, and build effort.",
    )
    risks: list[str] = Field(
        ...,
        description="Key risks including technical, market, regulatory, and competitive.",
    )
    recommendation: Literal["build", "dont_build", "build_with_caveats"] = Field(
        ...,
        description="Final recommendation: build, dont_build, or build_with_caveats.",
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence score for the recommendation, from 0.0 to 1.0.",
    )
    reasoning: str = Field(
        ...,
        description="Detailed explanation of the reasoning behind the recommendation.",
    )
    mvp_suggestion: str | None = Field(
        default=None,
        description="Suggested minimum viable product scope, if recommendation is to build.",
    )
    engine: Literal["mock", "crew"] = Field(
        ...,
        description="Which engine produced this report: mock (deterministic fallback) or crew (real LLM agents).",
    )


class AnalyzeMeta(BaseModel):
    """Metadata about the analysis run."""

    duration_ms: int = Field(
        ...,
        description="Time taken to generate the report, in milliseconds.",
    )
    model: str | None = Field(
        default=None,
        description="The LLM model used, if applicable.",
    )
    degraded: bool = Field(
        default=False,
        description="True if the real crew failed or timed out and fell back to the mock engine.",
    )


class AnalyzeResponse(BaseModel):
    """The full API response for POST /analyze."""

    report: FeasibilityReport = Field(
        ...,
        description="The feasibility analysis report.",
    )
    meta: AnalyzeMeta = Field(
        ...,
        description="Metadata about the analysis run.",
    )
