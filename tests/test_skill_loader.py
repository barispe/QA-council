"""Tests for SKILL.md loader."""

import tempfile
import pytest
from pathlib import Path

from qa_council.skill_loader import load_skill, create_agent_from_skill


@pytest.fixture
def valid_skill_dir(tmp_path):
    """Create a temporary directory with a valid SKILL.md."""
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        """---
name: test-agent
description: >
  A test agent that does testing things.
  It tests very well.
---

# Test Agent

You are a test agent.

## Instructions

1. Do testing
2. Report results
""",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def missing_name_skill_dir(tmp_path):
    """SKILL.md without a name field."""
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        """---
description: A broken skill.
---

# Broken
""",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def no_frontmatter_skill_dir(tmp_path):
    """SKILL.md without YAML frontmatter."""
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# Just markdown, no frontmatter", encoding="utf-8")
    return tmp_path


class TestLoadSkill:
    """Tests for the load_skill function."""

    def test_parses_valid_skill(self, valid_skill_dir):
        """Should parse name, description, and instructions from a valid SKILL.md."""
        result = load_skill(valid_skill_dir)

        assert result["name"] == "test-agent"
        assert "test agent that does testing things" in result["description"]
        assert "# Test Agent" in result["instructions"]
        assert "1. Do testing" in result["instructions"]

    def test_raises_on_missing_file(self, tmp_path):
        """Should raise FileNotFoundError if SKILL.md doesn't exist."""
        with pytest.raises(FileNotFoundError, match="No SKILL.md found"):
            load_skill(tmp_path)

    def test_raises_on_missing_name(self, missing_name_skill_dir):
        """Should raise ValueError if name field is missing."""
        with pytest.raises(ValueError, match="missing required 'name' field"):
            load_skill(missing_name_skill_dir)

    def test_raises_on_no_frontmatter(self, no_frontmatter_skill_dir):
        """Should raise ValueError if frontmatter delimiters are missing."""
        with pytest.raises(ValueError, match="missing YAML frontmatter"):
            load_skill(no_frontmatter_skill_dir)

    def test_strips_instructions_whitespace(self, valid_skill_dir):
        """Instructions should be stripped of leading/trailing whitespace."""
        result = load_skill(valid_skill_dir)
        assert not result["instructions"].startswith("\n")
        assert not result["instructions"].endswith("\n")

    def test_accepts_path_object(self, valid_skill_dir):
        """Should accept both str and Path objects."""
        result = load_skill(Path(valid_skill_dir))
        assert result["name"] == "test-agent"


class TestLoadActualSkills:
    """Tests that verify the real SKILL.md files in the skills/ directory parse correctly."""

    def test_scout_skill_loads(self):
        """Scout SKILL.md should parse without errors."""
        result = load_skill("skills/scout")
        assert result["name"] == "qa-scout"
        assert "endpoint" in result["description"].lower() or "discover" in result["description"].lower()
        assert len(result["instructions"]) > 100  # should have substantial content

    def test_critic_skill_loads(self):
        """Critic SKILL.md should parse without errors."""
        result = load_skill("skills/critic")
        assert result["name"] == "qa-critic"
        assert "challenge" in result["description"].lower() or "completeness" in result["description"].lower()
        assert len(result["instructions"]) > 100
