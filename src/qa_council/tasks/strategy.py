"""Strategy tasks — Strategist designs test plan, Critic reviews it."""

from crewai import Task, Agent


def create_strategy_task(strategist: Agent, explore_task: Task) -> Task:
    """Create the test strategy design task."""
    return Task(
        description=(
            "Using the Scout's API map, design a comprehensive test strategy.\n\n"
            "1. Categorize all discovered endpoints by risk level (CRITICAL/HIGH/MEDIUM/LOW)\n"
            "2. For each priority level, define specific test scenarios\n"
            "3. Include both positive and negative test cases\n"
            "4. Identify cross-cutting concerns (auth, rate limits, data consistency)\n"
            "5. Estimate coverage percentage\n\n"
            "Focus on scenarios that are ACTIONABLE — the Engineer needs to implement them directly."
        ),
        expected_output=(
            "A structured test strategy with:\n"
            "- Priority matrix (endpoint → risk level → scenario count)\n"
            "- Detailed test scenarios per priority level\n"
            "- Cross-cutting test concerns\n"
            "- Coverage estimate"
        ),
        agent=strategist,
        context=[explore_task],
    )


def create_critique_strategy_task(critic: Agent, strategy_task: Task) -> Task:
    """Create the task where the Critic reviews the test strategy."""
    return Task(
        description=(
            "Review the Strategist's test plan. Challenge it:\n\n"
            "1. Are the risk priorities correct? Could anything rated MEDIUM actually be CRITICAL?\n"
            "2. Are there missing scenarios? What edge cases are absent?\n"
            "3. Is the coverage estimate realistic?\n"
            "4. Are the scenarios specific enough for the Engineer to implement?\n"
            "5. Are there any redundant scenarios that can be consolidated?\n\n"
            "Be specific — name exact scenarios that should be added or changed."
        ),
        expected_output=(
            "A structured critique with critical issues, gaps found, "
            "improvements, and acknowledgment of what's good."
        ),
        agent=critic,
        context=[strategy_task],
    )
