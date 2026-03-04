"""Full council crew — all 6 agents with hierarchical process (NEW mode)."""

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
from qa_council.tasks.strategy import (
    create_strategy_task,
    create_critique_strategy_task,
)
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


def build_new_crew(
    target_url: str,
    output_dir: str = "./output",
    llm: str = "gpt-4o-mini",
    base_url: str | None = None,
) -> Crew:
    """Build the full 6-agent council crew for NEW mode.

    This is the complete pipeline:
    1. Scout explores the target API
    2. Critic challenges the Scout's findings
    3. Scout revises based on critique
    4. Strategist designs test plan from the revised map
    5. Critic reviews the strategy
    6. Engineer implements tests
    7. Critic reviews the code
    8. Engineer fixes issues
    9. Reporter compiles the final report

    Args:
        target_url: The API URL to explore and test.
        output_dir: Directory for generated test files and reports.
        llm: LLM model string for all agents.
        base_url: Optional base URL for local LLM server.

    Returns:
        A configured Crew ready to kickoff().
    """
    # Create tools
    http_tool = HttpClientTool()
    spec_tool = SpecParserTool()
    file_tool = FileWriterTool(output_dir=output_dir)
    test_tool = TestRunnerTool(output_dir=output_dir)

    # Create agents from SKILL.md files
    scout = create_scout(llm=llm, base_url=base_url, tools=[http_tool, spec_tool])
    strategist = create_strategist(llm=llm, base_url=base_url)
    engineer = create_engineer(llm=llm, base_url=base_url, tools=[file_tool, test_tool, http_tool])
    critic = create_critic(llm=llm, base_url=base_url)
    reporter = create_reporter(llm=llm, base_url=base_url)
    moderator = create_moderator(llm=llm, base_url=base_url)

    # Phase 1: Reconnaissance (Scout explores → Critic challenges → Scout revises)
    explore_task = create_explore_task(scout, target_url)
    critique_recon = create_critique_recon_task(critic, explore_task)
    revised_recon = create_revised_explore_task(scout, explore_task, critique_recon)

    # Phase 2: Strategy (Strategist plans → Critic reviews)
    strategy_task = create_strategy_task(strategist, revised_recon)
    critique_strategy = create_critique_strategy_task(critic, strategy_task)

    # Phase 3: Implementation (Engineer writes → Critic reviews → Engineer fixes)
    implement_task = create_implement_task(engineer, strategy_task, critique_strategy)
    critique_code = create_critique_code_task(critic, implement_task)
    fix_task = create_fix_tests_task(engineer, implement_task, critique_code)

    # Phase 4: Reporting
    report_task = create_report_task(
        reporter,
        context_tasks=[revised_recon, strategy_task, fix_task],
    )

    # Assemble the crew with hierarchical process
    crew = Crew(
        agents=[scout, strategist, engineer, critic, reporter],
        tasks=[
            # Phase 1: Recon
            explore_task,
            critique_recon,
            revised_recon,
            # Phase 2: Strategy
            strategy_task,
            critique_strategy,
            # Phase 3: Implementation
            implement_task,
            critique_code,
            fix_task,
            # Phase 4: Report
            report_task,
        ],
        process=Process.sequential,
        manager_agent=moderator,
        verbose=True,
        memory=True,
        respect_context_window=True,
    )

    return crew
