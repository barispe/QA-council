"""Reconnaissance tasks — Scout explores, Critic challenges, Scout revises."""

from crewai import Task, Agent


def create_explore_task(scout: Agent, target_url: str) -> Task:
    """Create the initial API exploration task for the Scout.

    The Scout systematically discovers endpoints, methods, schemas,
    and error behaviors at the target URL.
    """
    return Task(
        description=(
            f"Explore the API at {target_url}. Your mission:\n\n"
            f"1. First, check for an OpenAPI/Swagger spec at common paths:\n"
            f"   - {target_url}/swagger.json\n"
            f"   - {target_url}/openapi.json\n"
            f"   - {target_url}/api-docs\n\n"
            f"2. If a spec is found, parse it to understand the full API surface.\n\n"
            f"3. For each endpoint group, make actual HTTP requests to verify:\n"
            f"   - What status codes are returned\n"
            f"   - What the response shapes look like\n"
            f"   - What happens with invalid inputs\n\n"
            f"4. Test at least 3 different endpoint groups thoroughly.\n\n"
            f"5. Document any authentication requirements you discover.\n\n"
            f"Build a complete API map with your findings."
        ),
        expected_output=(
            "A structured API map in markdown format containing:\n"
            "- List of all discovered endpoints with their HTTP methods\n"
            "- Request parameters (path, query, body) for each endpoint\n"
            "- Sample response shapes/schemas\n"
            "- Authentication requirements\n"
            "- Error codes observed\n"
            "- Any rate limiting or pagination patterns"
        ),
        agent=scout,
    )


def create_critique_recon_task(critic: Agent, explore_task: Task) -> Task:
    """Create the critique task where the Critic challenges the Scout's findings.

    The Critic receives the Scout's API map and looks for gaps,
    missing edge cases, and untested paths.
    """
    return Task(
        description=(
            "Review the Scout's API exploration results. Your job is to find what's MISSING.\n\n"
            "Challenge the findings on:\n"
            "1. **Missing endpoints**: Are there common REST patterns not explored? "
            "(e.g., pagination, filtering, sorting, search)\n"
            "2. **Untested methods**: If GET was tested, what about POST, PUT, DELETE?\n"
            "3. **Error coverage**: Were invalid inputs tested? Wrong data types? "
            "Missing required fields? Boundary values?\n"
            "4. **Authentication edges**: What about expired tokens, wrong roles, "
            "missing auth headers?\n"
            "5. **Data validation**: Special characters, empty strings, very large payloads?\n"
            "6. **Missing metadata**: Rate limits, pagination limits, API versions?\n\n"
            "Be specific — don't just say 'test more endpoints'. "
            "Name exact endpoints and scenarios that should be tested."
        ),
        expected_output=(
            "A structured critique with:\n"
            "- Critical gaps that must be addressed (specific endpoints/scenarios)\n"
            "- Missing edge cases with exact test scenarios\n"
            "- Improvement suggestions\n"
            "- Acknowledgment of what was done well"
        ),
        agent=critic,
        context=[explore_task],
    )


def create_revised_explore_task(
    scout: Agent, explore_task: Task, critique_task: Task
) -> Task:
    """Create the revision task where the Scout addresses the Critic's feedback.

    The Scout receives both its original findings and the Critic's challenges,
    then performs additional exploration to fill the gaps.
    """
    return Task(
        description=(
            "The Critic has reviewed your API exploration and found gaps. "
            "Address their feedback:\n\n"
            "1. Review each critical gap the Critic identified\n"
            "2. Perform additional API requests to fill the gaps\n"
            "3. Test the specific scenarios and edge cases they called out\n"
            "4. Update your API map with the new findings\n\n"
            "Focus on the Critic's CRITICAL items first. "
            "You don't need to test every single suggestion, but address "
            "the most important gaps."
        ),
        expected_output=(
            "An updated, comprehensive API map that incorporates the Critic's feedback. "
            "Include:\n"
            "- All original findings\n"
            "- New findings from addressing the critique\n"
            "- A brief note on which Critic points were addressed and which were deferred\n"
            "- Final summary of API coverage"
        ),
        agent=scout,
        context=[explore_task, critique_task],
    )
