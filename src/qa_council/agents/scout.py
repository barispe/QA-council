"""Scout agent — API and application explorer."""

from qa_council.skill_loader import create_agent_from_skill


def create_scout(llm: str = "gpt-4o-mini", base_url: str | None = None, tools: list | None = None):
    """Create a Scout agent from its SKILL.md definition.

    The Scout explores and maps target applications, discovering endpoints,
    data shapes, and authentication requirements.
    """
    return create_agent_from_skill(
        skill_dir="skills/scout",
        llm=llm,
        base_url=base_url,
        tools=tools or [],
        allow_delegation=False,
    )
