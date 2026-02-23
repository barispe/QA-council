"""Implementation tasks — Engineer writes tests, Critic reviews code."""

from crewai import Task, Agent


def create_implement_task(engineer: Agent, strategy_task: Task, critique_task: Task) -> Task:
    """Create the test implementation task."""
    return Task(
        description=(
            "Using the test strategy (incorporating the Critic's feedback), "
            "write the actual test code.\n\n"
            "1. Create a conftest.py with shared fixtures (base URL, HTTP client)\n"
            "2. Implement CRITICAL priority tests first\n"
            "3. Use pytest + httpx patterns from your training\n"
            "4. Each test file should be self-contained and runnable\n"
            "5. Use the file_writer tool to save each test file\n\n"
            "Write real, runnable pytest code. Not pseudocode."
        ),
        expected_output=(
            "Complete pytest test files written to disk via the file_writer tool. "
            "Include: conftest.py, at least one test file per priority level, "
            "and a brief summary of what was written and why."
        ),
        agent=engineer,
        context=[strategy_task, critique_task],
    )


def create_critique_code_task(critic: Agent, implement_task: Task) -> Task:
    """Create the task where the Critic reviews the test code."""
    return Task(
        description=(
            "Review the Engineer's test code. Focus on:\n\n"
            "1. Are assertions specific enough? (not just status codes)\n"
            "2. Are tests independent? (no shared mutable state)\n"
            "3. Is there proper cleanup/teardown?\n"
            "4. Are there missing negative tests?\n"
            "5. Could any tests be flaky? (timing dependencies, order dependencies)\n"
            "6. Do test names clearly describe what's being tested?\n\n"
            "Provide specific code-level feedback."
        ),
        expected_output=(
            "A code review with specific issues, suggested fixes, "
            "and quality assessment of the test suite."
        ),
        agent=critic,
        context=[implement_task],
    )


def create_fix_tests_task(
    engineer: Agent, implement_task: Task, critique_task: Task
) -> Task:
    """Create the task where the Engineer fixes issues from the code review."""
    return Task(
        description=(
            "Address the Critic's code review feedback.\n\n"
            "1. Fix any critical issues identified\n"
            "2. Improve assertions where suggested\n"
            "3. Add any missing tests the Critic flagged\n"
            "4. Use the file_writer tool to update the test files\n"
            "5. Use the test_runner tool to verify the tests pass\n\n"
            "Focus on CRITICAL feedback first. Note any suggestions you deferred."
        ),
        expected_output=(
            "Updated test files written to disk, test run results, "
            "and a summary of what was fixed vs. deferred."
        ),
        agent=engineer,
        context=[implement_task, critique_task],
    )
