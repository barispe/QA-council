"""SKILL.md loader — bridges the Agent Skills open standard to CrewAI agents.

Parses SKILL.md files (YAML frontmatter + markdown instructions) and creates
CrewAI Agent instances from them. This allows agent behavior to be defined
in editable markdown files instead of hardcoded Python strings.

See: https://agentskills.io/specification
"""

import yaml
from pathlib import Path
from crewai import Agent


def load_skill(skill_dir: str | Path) -> dict:
    """Parse a SKILL.md file and return its components.

    Args:
        skill_dir: Path to the skill directory containing a SKILL.md file.

    Returns:
        Dict with 'name', 'description', and 'instructions' keys.

    Raises:
        FileNotFoundError: If SKILL.md doesn't exist in the directory.
        ValueError: If SKILL.md is missing required frontmatter fields.
    """
    skill_path = Path(skill_dir) / "SKILL.md"

    if not skill_path.exists():
        raise FileNotFoundError(f"No SKILL.md found in {skill_dir}")

    content = skill_path.read_text(encoding="utf-8")

    # Split YAML frontmatter from markdown body
    # Format: ---\nfrontmatter\n---\nbody
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"SKILL.md in {skill_dir} is missing YAML frontmatter (--- delimiters)")

    metadata = yaml.safe_load(parts[1])

    if not metadata or "name" not in metadata:
        raise ValueError(f"SKILL.md in {skill_dir} is missing required 'name' field")
    if "description" not in metadata:
        raise ValueError(f"SKILL.md in {skill_dir} is missing required 'description' field")

    return {
        "name": metadata["name"],
        "description": metadata["description"],
        "instructions": parts[2].strip(),
    }


def create_agent_from_skill(
    skill_dir: str | Path,
    llm: str = "gpt-4o-mini",
    tools: list | None = None,
    **kwargs,
) -> Agent:
    """Create a CrewAI Agent from a SKILL.md file.

    Maps SKILL.md fields to CrewAI Agent parameters:
      - name (frontmatter) → role
      - description (frontmatter) → goal
      - markdown body → backstory

    Args:
        skill_dir: Path to skill directory containing SKILL.md.
        llm: LLM model string (e.g. 'gpt-4o-mini', 'claude-sonnet-4-20250514').
        tools: List of CrewAI tools this agent can use.
        **kwargs: Additional CrewAI Agent parameters (e.g. allow_delegation, allow_code_execution).

    Returns:
        A configured CrewAI Agent instance.
    """
    skill = load_skill(skill_dir)
    return Agent(
        role=skill["name"],
        goal=skill["description"],
        backstory=skill["instructions"],
        llm=llm,
        tools=tools or [],
        verbose=True,
        **kwargs,
    )
