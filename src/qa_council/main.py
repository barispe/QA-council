"""QA-Council CLI entry point."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main():
    """CLI entry point for qa-council."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="qa-council",
        description="Multi-agent QA council for intelligent test automation.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'run' command
    run_parser = subparsers.add_parser("run", help="Run the QA council against a target")
    run_parser.add_argument("--url", required=True, help="Target API or application URL")
    run_parser.add_argument(
        "--mode",
        choices=["new", "extend", "maintain"],
        default="new",
        help="Operating mode (default: new)",
    )
    run_parser.add_argument("--output", default="./output", help="Output directory")
    run_parser.add_argument(
        "--preset",
        choices=["budget", "balanced", "premium"],
        help="Model preset to use",
    )
    run_parser.add_argument(
        "--checkpoints",
        choices=["none", "phase", "critical", "full"],
        default="critical",
        help="Checkpoint level (default: critical)",
    )
    run_parser.add_argument("--config", help="Path to config YAML file")
    run_parser.add_argument("--dry-run", action="store_true", help="Preview without LLM calls")
    run_parser.add_argument("--model", default=None, help="LLM model override for all agents")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "run":
        if args.dry_run:
            _dry_run(args)
        else:
            _run(args)


def _dry_run(args):
    """Show what agents would activate without making LLM calls."""
    from qa_council.config import load_config

    config = load_config(config_path=args.config, args=args)

    mode_agents = {
        "new": ["Moderator", "Scout", "Strategist", "Engineer", "Critic", "Reporter"],
        "extend": ["Moderator", "Scout", "Strategist", "Engineer", "Critic", "Reporter"],
        "maintain": ["Scout", "Engineer", "Critic"],
    }
    agents = mode_agents[config.mode]

    print(f"\n🔍 Dry Run — Mode: {config.mode.upper()}")
    print(f"   Target: {config.url}")
    print(f"   Output: {config.output}")
    print(f"   Checkpoints: {config.checkpoints}")
    print(f"   Model (default): {config.models.default}")

    # Show per-agent models if any differ from default
    overrides = {k: v for k, v in config.models.per_agent.items() if v != config.models.default}
    if overrides:
        print(f"   Model overrides: {overrides}")

    print(f"\n   Would activate: {', '.join(agents)}")
    print(f"   Total agents: {len(agents)}\n")


def _run(args):
    """Run the QA council."""
    from qa_council.config import load_config

    config = load_config(config_path=args.config, args=args)

    print(f"\n🚀 QA-Council — Mode: {config.mode.upper()}")
    print(f"   Target: {config.url}")
    print(f"   Model:  {config.models.default}")
    print(f"   Output: {config.output}")
    print(f"   Checkpoints: {config.checkpoints}")
    print("=" * 60)

    if config.mode == "new":
        _run_full_council(config)
    elif config.mode == "extend":
        _run_extend(config)
    else:
        _run_maintain(config)


def _run_full_council(config):
    """Run the full 6-agent council (NEW mode)."""
    from qa_council.crews.new_crew import build_new_crew

    crew = build_new_crew(
        target_url=config.url,
        output_dir=config.output,
        llm=config.models.default,
    )
    print("\n🏛️  Full council is in session (6 agents, 9 tasks)...\n")
    result = crew.kickoff()
    _save_result(result, config.output, "council_report.md")


def _run_extend(config):
    """Run the EXTEND mode crew."""
    from qa_council.crews.extend_crew import build_extend_crew

    crew = build_extend_crew(
        target_url=config.url,
        output_dir=config.output,
        llm=config.models.default,
    )
    print("\n📦 Extend mode — adding tests to existing coverage...\n")
    result = crew.kickoff()
    _save_result(result, config.output, "extend_report.md")


def _run_maintain(config):
    """Run the MAINTAIN mode crew."""
    from qa_council.crews.maintain_crew import build_maintain_crew

    crew = build_maintain_crew(
        target_url=config.url,
        output_dir=config.output,
        llm=config.models.default,
    )
    print("\n🔧 Maintain mode — fixing and updating tests...\n")
    result = crew.kickoff()
    _save_result(result, config.output, "maintain_report.md")


def _save_result(result, output_dir: str, filename: str):
    """Save crew result to file and print summary."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / filename
    output_file.write_text(str(result.raw), encoding="utf-8")

    print("\n" + "=" * 60)
    print("✅ Council session complete!")
    print(f"   Output saved to: {output_file}")

    if hasattr(result, "token_usage"):
        usage = result.token_usage
        print("\n📊 Token Usage:")
        print(f"   Total tokens: {usage.total_tokens}")
        print(f"   Prompt tokens: {usage.prompt_tokens}")
        print(f"   Completion tokens: {usage.completion_tokens}")
        if hasattr(usage, "successful_requests"):
            print(f"   API calls: {usage.successful_requests}")
    print()


if __name__ == "__main__":
    main()
