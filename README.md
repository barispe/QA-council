# QA-Council

> Multi-agent QA council that debates, challenges, and collaborates to handle testing workflows.

## What Is This?

QA-Council is a multi-agent system built on [CrewAI](https://www.crewai.com/) where specialized AI agents collaborate as a "council" to perform QA tasks — from API exploration to test strategy to code generation. Each agent has a distinct role, and they debate each other's work to catch blind spots.

### The Council

| Agent | Role |
|---|---|
| 🔍 **Scout** | Discovers and maps APIs, endpoints, and data shapes |
| 🧠 **Strategist** | Designs test strategies and prioritizes by risk |
| 🛠️ **Engineer** | Writes test code and maintains test infrastructure |
| 👁️ **Critic** | Challenges everything — finds gaps, edge cases, and blind spots |
| 📝 **Reporter** | Compiles results into clear, actionable reports |
| 🎯 **Moderator** | Orchestrates the council, sequences phases, manages debate |

### Key Feature: SKILL.md

Agent behavior is defined in **SKILL.md** files (following the [Agent Skills open standard](https://agentskills.io/)), not hardcoded in Python. This means:

- ✏️ Edit agent behavior by changing a markdown file — no code changes needed
- 🔄 Skills are portable across platforms (Claude Code, Copilot, etc.)
- 📦 Version-controlled and reviewable in PRs

## Status

🚧 **Early development** — Phase 0 (project setup) complete. Phase 1 (Scout + Critic debate) up next.

## Quick Start

```bash
# Clone
git clone https://github.com/barispe/QA-council.git
cd QA-council

# Install
pip install -e ".[dev]"

# Set up your API key
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Dry run (preview which agents would activate)
qa-council run --url https://petstore.swagger.io/v2 --mode new --dry-run

# Run tests
pytest tests/ -v
```

## Project Structure

```
QA-Council/
├── skills/                    # SKILL.md files define agent behavior
│   ├── scout/SKILL.md
│   ├── critic/SKILL.md
│   ├── strategist/SKILL.md
│   ├── engineer/SKILL.md
│   ├── reporter/SKILL.md
│   └── moderator/SKILL.md
├── src/qa_council/
│   ├── skill_loader.py        # SKILL.md → CrewAI Agent bridge
│   ├── main.py                # CLI entry point
│   ├── agents/                # Agent factory functions
│   ├── tasks/                 # Task definitions
│   ├── tools/                 # Custom CrewAI tools
│   └── crews/                 # Crew compositions per mode
├── config/
│   └── qa-council.config.yaml
└── tests/
```

## Requirements

- Python 3.11+
- An LLM API key (OpenAI or Anthropic)

## License

MIT
