"""MAINTAIN mode crew — lightweight Scout + Engineer + Critic for fixing broken tests."""

from crewai import Crew, Process

from qa_council.agents.scout import create_scout
from qa_council.agents.engineer import create_engineer
from qa_council.agents.critic import create_critic
from qa_council.tasks.recon import (
    create_explore_task,
    create_critique_recon_task,
    create_revised_explore_task,
)
from qa_council.tasks.implement import (
    create_implement_task,
    create_critique_code_task,
)
from qa_council.tools.http_client import HttpClientTool
from qa_council.tools.file_writer import FileWriterTool
from qa_council.tools.test_runner import TestRunnerTool


def build_maintain_crew(
    target_url: str,
    output_dir: str = "./output",
    llm: str = "gpt-4o-mini",
    base_url: str | None = None,
) -> Crew:
    """Build a crew for MAINTAIN mode — fixing and updating existing tests.

    Lightweight pipeline with only Scout, Engineer, and Critic.
    No Strategist (uses existing strategy), no Reporter (quick fix mode).

    Args:
        target_url: The API URL to explore changed areas.
        output_dir: Directory for generated files.
        llm: LLM model string.
        base_url: Optional base URL for local LLM server.

    Returns:
        A configured Crew ready to kickoff().
    """
    http_tool = HttpClientTool()
    file_tool = FileWriterTool(output_dir=output_dir)
    test_tool = TestRunnerTool(output_dir=output_dir)

    scout = create_scout(llm=llm, base_url=base_url, tools=[http_tool])
    engineer = create_engineer(llm=llm, base_url=base_url, tools=[file_tool, test_tool, http_tool])
    critic = create_critic(llm=llm, base_url=base_url)

    # Quick recon — focus on changed areas
    explore_task = create_explore_task(scout, target_url)
    critique_recon = create_critique_recon_task(critic, explore_task)
    revised_recon = create_revised_explore_task(scout, explore_task, critique_recon)

    # Direct to implementation — no strategy phase
    implement_task = create_implement_task(engineer, revised_recon, critique_recon)
    critique_code = create_critique_code_task(critic, implement_task)

    return Crew(
        agents=[scout, engineer, critic],
        tasks=[
            explore_task,
            critique_recon,
            revised_recon,
            implement_task,
            critique_code,
        ],
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,
    )
