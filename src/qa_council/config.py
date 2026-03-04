"""Configuration loader — merges YAML config with CLI args."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


DEFAULT_CONFIG_PATHS = [
    "qa-council.config.yaml",
    "config/qa-council.config.yaml",
]


@dataclass
class ModelConfig:
    """Model configuration — which LLM each agent uses."""

    default: str = "gpt-4o-mini"
    base_url: str = ""  # For local LLMs (Ollama, LM Studio)
    per_agent: dict[str, str] = field(default_factory=dict)

    def get_model(self, agent_name: str) -> str:
        """Get the model for a specific agent, falling back to default."""
        return self.per_agent.get(agent_name, self.default)


@dataclass
class Config:
    """Full QA-Council configuration."""

    url: str = ""
    mode: str = "new"
    output: str = "./output"
    checkpoints: str = "critical"
    models: ModelConfig = field(default_factory=ModelConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load config from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        return cls._from_dict(raw)

    @classmethod
    def from_defaults(cls) -> Config:
        """Load from default config path, or use built-in defaults."""
        for config_path in DEFAULT_CONFIG_PATHS:
            if Path(config_path).exists():
                return cls.from_yaml(config_path)
        return cls()

    @classmethod
    def _from_dict(cls, raw: dict) -> Config:
        """Build a Config from a raw dictionary."""
        models_raw = raw.get("models", {})
        models = ModelConfig(
            default=models_raw.get("default", "gpt-4o-mini"),
            base_url=models_raw.get("base_url", ""),
            per_agent=models_raw.get("per_agent", {}),
        )
        return cls(
            url=raw.get("url", ""),
            mode=raw.get("mode", "new"),
            output=raw.get("output", "./output"),
            checkpoints=raw.get("checkpoints", "critical"),
            models=models,
        )

    def apply_preset(self, preset_name: str, presets: dict) -> None:
        """Apply a named model preset from config."""
        if preset_name not in presets:
            raise ValueError(
                f"Unknown preset '{preset_name}'. Available: {', '.join(presets.keys())}"
            )
        preset = presets[preset_name]
        self.models.default = preset.get("default", self.models.default)
        if "base_url" in preset:
            self.models.base_url = preset["base_url"]
        if "per_agent" in preset:
            self.models.per_agent.update(preset["per_agent"])

    def merge_cli_args(self, args) -> None:
        """Merge CLI arguments over config (CLI wins)."""
        if hasattr(args, "url") and args.url:
            self.url = args.url
        if hasattr(args, "mode") and args.mode:
            self.mode = args.mode
        if hasattr(args, "output") and args.output:
            self.output = args.output
        if hasattr(args, "checkpoints") and args.checkpoints:
            self.checkpoints = args.checkpoints
        if hasattr(args, "model") and args.model:
            self.models.default = args.model
        if hasattr(args, "base_url") and args.base_url:
            self.models.base_url = args.base_url


def load_config(config_path: Optional[str] = None, args=None) -> Config:
    """Load configuration with full merge chain.

    Priority: CLI args > custom config file > default config > built-in defaults.

    Args:
        config_path: Optional explicit path to a config YAML file.
        args: Optional argparse Namespace with CLI arguments.

    Returns:
        Merged Config object.
    """
    if config_path:
        config = Config.from_yaml(config_path)
    else:
        config = Config.from_defaults()

    # Apply preset if specified
    if args and hasattr(args, "preset") and args.preset:
        presets = _load_presets(config_path)
        config.apply_preset(args.preset, presets)

    # CLI args override everything
    if args:
        config.merge_cli_args(args)

    return config


def _load_presets(config_path: Optional[str] = None) -> dict:
    """Load preset definitions from config file."""
    paths_to_try = [config_path] if config_path else DEFAULT_CONFIG_PATHS
    for path in paths_to_try:
        if path and Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            return raw.get("presets", {})
    return {}
