"""Engineer agent — test code writer and executor."""

from qa_council.skill_loader import create_agent_from_skill


def create_engineer(llm: str = "gpt-4o-mini", base_url: str | None = None, tools: list | None = None):
    """Create an Engineer agent from its SKILL.md definition.

    The Engineer writes test code using pytest/httpx and runs tests.
    Has code execution enabled with Docker sandboxing.
    """
    return create_agent_from_skill(
        skill_dir="skills/engineer",
        llm=llm,
        base_url=base_url,
        tools=tools or [],
        allow_code_execution=True,
        allow_delegation=False,
    )
