import hashlib
import random

from typing import Literal, cast

from app.schemas.report import Competitor, FeasibilityReport


class MockEngine:
    def analyze(self, idea: str) -> FeasibilityReport:
        idea_hash = int(hashlib.sha256(idea.encode("utf-8")).hexdigest(), 16)

        rng = random.Random(idea_hash)

        short_idea = idea[:50] + ("..." if len(idea) > 50 else "")

        market_overview = (
            f"The market for '{short_idea}' shows moderate but growing interest."
        )

        competitors = [
            Competitor(
                name=f"{short_idea.split()[0].capitalize()}Corp",
                description="A legacy player in this space.",
                differentiator="Large existing user base but slow to innovate.",
            ),
            Competitor(
                name="AgileTech AI",
                description="A new startup addressing similar needs.",
                differentiator="Modern tech stack but lacks enterprise features.",
            ),
        ]

        opportunities = [
            "Underserved enterprise segment.",
            "Potential for AI-driven automation.",
        ]

        gaps = [
            "Lack of integrations with legacy systems.",
            "High learning curve in existing solutions.",
        ]

        technical_feasibility = "Moderate complexity. Requires standard web stack and some API integrations."

        risks = [
            "High customer acquisition cost.",
            "Incumbents could easily replicate the feature set.",
            "Technical debt if scaled too quickly.",
        ]

        recommendation = cast(
            Literal["build", "dont_build", "build_with_caveats"],
            rng.choice(["build", "dont_build", "build_with_caveats"]),
        )

        mvp_suggestion = (
            "A simple web app focusing on the core value proposition for a single niche."
            if recommendation != "dont_build"
            else None
        )

        return FeasibilityReport(
            idea=idea,
            market_overview=market_overview,
            competitors=competitors,
            opportunities=opportunities,
            gaps=gaps,
            technical_feasibility=technical_feasibility,
            risks=risks,
            recommendation=recommendation,
            confidence=0.55,
            reasoning=f"Based on a mock analysis, the recommendation is to {recommendation.replace('_', ' ')} due to market conditions.",
            mvp_suggestion=mvp_suggestion,
            engine="mock",
        )
