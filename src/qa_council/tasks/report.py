"""Report tasks — Reporter compiles the final session report."""

from crewai import Task, Agent


def create_report_task(reporter: Agent, context_tasks: list[Task]) -> Task:
    """Create the final reporting task.

    Args:
        reporter: The Reporter agent.
        context_tasks: All prior tasks to compile from.
    """
    return Task(
        description=(
            "Compile the entire QA council session into a final report.\n\n"
            "Gather all outputs from the session:\n"
            "- Scout's API exploration results\n"
            "- Strategist's test plan\n"
            "- Critic's feedback (all rounds)\n"
            "- Engineer's test code and test results\n\n"
            "Create a polished markdown report with:\n"
            "1. Executive summary (2-3 sentences)\n"
            "2. API surface discovered\n"
            "3. Test results (pass/fail counts)\n"
            "4. Critical findings\n"
            "5. Coverage analysis\n"
            "6. Key debate highlights (how the Critic improved the output)\n"
            "7. Recommendations for follow-up"
        ),
        expected_output=(
            "A comprehensive markdown report following the Reporter's template. "
            "Should be actionable and under 500 lines."
        ),
        agent=reporter,
        context=context_tasks,
    )
