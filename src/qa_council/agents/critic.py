"""Critic agent — devil's advocate quality reviewer."""

from qa_council.skill_loader import create_agent_from_skill


def create_critic(llm: str = "gpt-4o-mini"):
    """Create a Critic agent from its SKILL.md definition.

    The Critic challenges all outputs for completeness, correctness,
    and quality. Prevents echo chambers and catches blind spots.
    """
    return create_agent_from_skill(
        skill_dir="skills/critic",
        llm=llm,
        allow_delegation=False,
    )
