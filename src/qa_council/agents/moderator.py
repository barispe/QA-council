"""Moderator agent — orchestrates the council process."""

from qa_council.skill_loader import create_agent_from_skill


def create_moderator(llm: str = "gpt-4o-mini"):
    """Create a Moderator agent from its SKILL.md definition.

    The Moderator sequences phases, routes outputs between agents,
    and manages debate rounds. Used as the manager_agent in
    hierarchical process mode.
    """
    return create_agent_from_skill(
        skill_dir="skills/moderator",
        llm=llm,
        allow_delegation=True,
    )
