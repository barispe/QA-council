"""QA-Council CLI entry point."""

import argparse
import sys


def main():
    """CLI entry point for qa-council."""
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
    run_parser.add_argument("--output", default="./output", help="Output directory (default: ./output)")
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
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what agents would activate without making LLM calls",
    )

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
    mode_agents = {
        "new": ["Moderator", "Scout", "Strategist", "Engineer", "Critic", "Reporter"],
        "extend": ["Moderator", "Scout (new areas)", "Strategist", "Engineer", "Critic", "Reporter"],
        "maintain": ["Moderator", "Scout (changed areas)", "Engineer", "Critic"],
    }
    agents = mode_agents[args.mode]
    print(f"\n🔍 Dry Run — Mode: {args.mode.upper()}")
    print(f"   Target: {args.url}")
    print(f"   Output: {args.output}")
    print(f"   Checkpoints: {args.checkpoints}")
    print(f"\n   Would activate: {', '.join(agents)}")
    print(f"   Total agents: {len(agents)}\n")


def _run(args):
    """Run the QA council. (Phase 1 implementation will fill this in.)"""
    print(f"\n🚀 QA-Council — Mode: {args.mode.upper()}")
    print(f"   Target: {args.url}")
    print(f"   Output: {args.output}")
    print(f"   Checkpoints: {args.checkpoints}")
    print("\n⚠️  Full execution not yet implemented. Use --dry-run to preview.\n")


if __name__ == "__main__":
    main()
