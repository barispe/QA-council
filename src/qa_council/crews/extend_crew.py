"""EXTEND mode crew — subset of agents for adding tests to existing projects."""

from crewai import Crew, Process

from qa_council.agents.scout import create_scout
from qa_council.agents.strategist import create_strategist
from qa_council.agents.engineer import create_engineer
from qa_council.agents.critic import create_critic
from qa_council.agents.reporter import create_reporter
from qa_council.agents.moderator import create_moderator
from qa_council.tasks.recon import (
    create_explore_task,
    create_critique_recon_task,
    create_revised_explore_task,
)
from qa_council.tasks.strategy import create_strategy_task
from qa_council.tasks.implement import (
    create_implement_task,
    create_critique_code_task,
    create_fix_tests_task,
)
from qa_council.tasks.report import create_report_task
from qa_council.tools.http_client import HttpClientTool
from qa_council.tools.spec_parser import SpecParserTool
from qa_council.tools.file_writer import FileWriterTool
from qa_council.tools.test_runner import TestRunnerTool


def build_extend_crew(target_url: str, output_dir: str = "./output", llm: str = "gpt-4o-mini") -> Crew:
    """Build a crew for EXTEND mode — adding tests to existing coverage.

    Same as NEW mode but Scout focuses only on new/changed areas,
    and the Strategist prioritizes gaps in existing coverage.

    Args:
        target_url: The API URL to explore.
        output_dir: Directory for generated files.
        llm: LLM model string.

    Returns:
        A configured Crew ready to kickoff().
    """
    http_tool = HttpClientTool()
    spec_tool = SpecParserTool()
    file_tool = FileWriterTool(output_dir=output_dir)
    test_tool = TestRunnerTool(output_dir=output_dir)

    scout = create_scout(llm=llm, tools=[http_tool, spec_tool])
    strategist = create_strategist(llm=llm)
    engineer = create_engineer(llm=llm, tools=[file_tool, test_tool, http_tool])
    critic = create_critic(llm=llm)
    reporter = create_reporter(llm=llm)
    moderator = create_moderator(llm=llm)

    # Recon — Scout focuses on new areas
    explore_task = create_explore_task(scout, target_url)
    critique_recon = create_critique_recon_task(critic, explore_task)
    revised_recon = create_revised_explore_task(scout, explore_task, critique_recon)

    # Strategy
    strategy_task = create_strategy_task(strategist, revised_recon)

    # Implementation (skip strategy critique — trust existing patterns)
    implement_task = create_implement_task(engineer, strategy_task, strategy_task)
    critique_code = create_critique_code_task(critic, implement_task)
    fix_task = create_fix_tests_task(engineer, implement_task, critique_code)

    # Report
    report_task = create_report_task(reporter, [revised_recon, strategy_task, fix_task])

    return Crew(
        agents=[scout, strategist, engineer, critic, reporter],
        tasks=[
            explore_task, critique_recon, revised_recon,
            strategy_task,
            implement_task, critique_code, fix_task,
            report_task,
        ],
        process=Process.sequential,
        manager_agent=moderator,
        verbose=True,
        memory=True,
        respect_context_window=True,
    )
