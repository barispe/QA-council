"""Agent factory functions."""

from qa_council.agents.scout import create_scout
from qa_council.agents.critic import create_critic

__all__ = ["create_scout", "create_critic"]
