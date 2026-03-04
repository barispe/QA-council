"""Reporter agent — compiles results into reports."""

from qa_council.skill_loader import create_agent_from_skill


def create_reporter(llm: str = "gpt-4o-mini", base_url: str | None = None):
    """Create a Reporter agent from its SKILL.md definition.

    The Reporter compiles all session outputs into clear,
    actionable markdown reports.
    """
    return create_agent_from_skill(
        skill_dir="skills/reporter",
        llm=llm,
        base_url=base_url,
        allow_delegation=False,
    )
