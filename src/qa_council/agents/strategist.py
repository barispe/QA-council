"""Strategist agent — test strategy and risk analysis designer."""

from qa_council.skill_loader import create_agent_from_skill


def create_strategist(llm: str = "gpt-4o-mini", base_url: str | None = None):
    """Create a Strategist agent from its SKILL.md definition.

    The Strategist designs risk-prioritized test plans from
    the Scout's reconnaissance data.
    """
    return create_agent_from_skill(
        skill_dir="skills/strategist",
        llm=llm,
        base_url=base_url,
        allow_delegation=True,
    )
