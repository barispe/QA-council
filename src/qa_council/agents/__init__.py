"""Agent factory functions."""

from qa_council.agents.scout import create_scout
from qa_council.agents.critic import create_critic
from qa_council.agents.strategist import create_strategist
from qa_council.agents.engineer import create_engineer
from qa_council.agents.reporter import create_reporter
from qa_council.agents.moderator import create_moderator

__all__ = [
    "create_scout",
    "create_critic",
    "create_strategist",
    "create_engineer",
    "create_reporter",
    "create_moderator",
]
