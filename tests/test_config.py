"""Tests for the config loader."""

import pytest
from types import SimpleNamespace

from qa_council.config import Config, ModelConfig, load_config


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file."""
    config_yaml = tmp_path / "test-config.yaml"
    config_yaml.write_text(
        """
checkpoints: phase
models:
  default: "gpt-4o-mini"
  per_agent:
    critic: "claude-sonnet-4-20250514"
presets:
  budget:
    default: "gpt-4o-mini"
  premium:
    default: "claude-sonnet-4-20250514"
    per_agent:
      scout: "gpt-4o-mini"
""",
        encoding="utf-8",
    )
    return str(config_yaml)


class TestModelConfig:
    """Tests for ModelConfig."""

    def test_get_model_returns_default(self):
        mc = ModelConfig(default="gpt-4o-mini")
        assert mc.get_model("scout") == "gpt-4o-mini"

    def test_get_model_returns_per_agent_override(self):
        mc = ModelConfig(default="gpt-4o-mini", per_agent={"critic": "claude-sonnet-4-20250514"})
        assert mc.get_model("critic") == "claude-sonnet-4-20250514"
        assert mc.get_model("scout") == "gpt-4o-mini"


class TestConfig:
    """Tests for Config loading and merging."""

    def test_from_yaml(self, config_file):
        config = Config.from_yaml(config_file)
        assert config.checkpoints == "phase"
        assert config.models.default == "gpt-4o-mini"
        assert config.models.get_model("critic") == "claude-sonnet-4-20250514"

    def test_from_yaml_missing_file(self):
        with pytest.raises(FileNotFoundError):
            Config.from_yaml("nonexistent.yaml")

    def test_from_defaults_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config = Config.from_defaults()
        assert config.models.default == "gpt-4o-mini"
        assert config.checkpoints == "critical"

    def test_merge_cli_args(self):
        config = Config()
        args = SimpleNamespace(
            url="https://api.test.com",
            mode="extend",
            output="./out",
            checkpoints="full",
            model="gpt-4",
        )
        config.merge_cli_args(args)
        assert config.url == "https://api.test.com"
        assert config.mode == "extend"
        assert config.output == "./out"
        assert config.checkpoints == "full"
        assert config.models.default == "gpt-4"

    def test_apply_preset(self, config_file):
        config = Config.from_yaml(config_file)
        presets = {
            "premium": {
                "default": "claude-sonnet-4-20250514",
                "per_agent": {"scout": "gpt-4o-mini"},
            }
        }
        config.apply_preset("premium", presets)
        assert config.models.default == "claude-sonnet-4-20250514"
        assert config.models.get_model("scout") == "gpt-4o-mini"

    def test_apply_unknown_preset_raises(self):
        config = Config()
        with pytest.raises(ValueError, match="Unknown preset"):
            config.apply_preset("nonexistent", {})


class TestLoadConfig:
    """Tests for the load_config convenience function."""

    def test_load_with_explicit_path(self, config_file):
        config = load_config(config_path=config_file)
        assert config.checkpoints == "phase"

    def test_cli_args_override_config(self, config_file):
        args = SimpleNamespace(
            url="https://override.com",
            mode="maintain",
            output="./custom",
            checkpoints="none",
            model="gpt-4",
            preset=None,
        )
        config = load_config(config_path=config_file, args=args)
        assert config.url == "https://override.com"
        assert config.mode == "maintain"
        assert config.checkpoints == "none"
