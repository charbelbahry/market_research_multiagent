def get_mock_search_results(query: str) -> str:
    """Returns deterministic mock search results based on the query."""

    query_lower = query.lower()

    if "competitor" in query_lower or "market" in query_lower:
        return (
            "1. Market Leader Corp - The dominant player in this space with 40% market share.\n"
            "2. Agile Startup Inc - A new entrant focusing on AI-driven solutions for this niche.\n"
            "3. Legacy Systems LLC - An older company with high enterprise penetration but outdated UX."
        )
    elif "risk" in query_lower or "challenge" in query_lower:
        return (
            "1. Regulatory compliance is a major barrier to entry in this sector.\n"
            "2. High customer acquisition costs typically kill new startups here.\n"
            "3. Data privacy concerns require significant upfront engineering investment."
        )
    elif "opportunity" in query_lower or "trend" in query_lower:
        return (
            "1. Growing demand for automation among mid-sized enterprises.\n"
            "2. Consumers are actively seeking cheaper alternatives to current enterprise options.\n"
            "3. Integration with popular chat platforms is a highly requested missing feature."
        )
    else:
        return (
            f"Search results for '{query}':\n"
            "1. General interest in this topic has grown 25% year-over-year.\n"
            "2. Several open-source projects have attempted to solve this with mixed success.\n"
            "3. Users report frustration with the complexity of existing enterprise tools."
        )
