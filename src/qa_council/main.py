"""QA-Council CLI entry point."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main():
    """CLI entry point for qa-council."""
    # Load .env file for API keys
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
    run_parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model to use for all agents (default: gpt-4o-mini)",
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
    """Run the Scout + Critic debate crew."""
    from crewai import Crew, Process

    from qa_council.agents.scout import create_scout
    from qa_council.agents.critic import create_critic
    from qa_council.tasks.recon import (
        create_explore_task,
        create_critique_recon_task,
        create_revised_explore_task,
    )
    from qa_council.tools.http_client import HttpClientTool

    print(f"\n🚀 QA-Council — Mode: {args.mode.upper()}")
    print(f"   Target: {args.url}")
    print(f"   Model:  {args.model}")
    print(f"   Output: {args.output}")
    print("=" * 60)

    # Create tools
    http_tool = HttpClientTool()

    # Create agents from SKILL.md files
    scout = create_scout(llm=args.model, tools=[http_tool])
    critic = create_critic(llm=args.model)

    # Create the debate tasks
    explore_task = create_explore_task(scout, args.url)
    critique_task = create_critique_recon_task(critic, explore_task)
    revised_task = create_revised_explore_task(scout, explore_task, critique_task)

    # Assemble the crew
    crew = Crew(
        agents=[scout, critic],
        tasks=[explore_task, critique_task, revised_task],
        process=Process.sequential,
        verbose=True,
    )

    # Run the council
    print("\n🏛️  Council is in session...\n")
    result = crew.kickoff()

    # Save output
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "api_map.md"
    output_file.write_text(str(result.raw), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"✅ Council session complete!")
    print(f"   Output saved to: {output_file}")

    # Print usage metrics if available
    if hasattr(result, "token_usage"):
        usage = result.token_usage
        print(f"\n📊 Token Usage:")
        print(f"   Total tokens: {usage.total_tokens}")
        print(f"   Prompt tokens: {usage.prompt_tokens}")
        print(f"   Completion tokens: {usage.completion_tokens}")
        if hasattr(usage, "successful_requests"):
            print(f"   API calls: {usage.successful_requests}")
    print()


if __name__ == "__main__":
    main()
