# QA-Council

> An open-source, multi-agent QA council that **debates, challenges, and collaborates** to handle testing workflows — powered by CrewAI and the SKILL.md open standard.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-38%20passing-brightgreen.svg)](#running-tests)

---

## Table of Contents

- [What Is This?](#what-is-this)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
  - [The Council (6 Agents)](#the-council-6-agents)
  - [Why These Roles](#why-these-roles)
  - [Architecture Diagram](#architecture-diagram)
- [Operating Modes](#operating-modes)
- [How the Council Debates](#how-the-council-debates)
  - [The Debate Loop](#the-debate-loop)
  - [Debate Flow Example](#debate-flow-example-extend-mode)
- [Human Checkpoint System](#human-checkpoint-system)
- [SKILL.md — Agent Behavior Definition](#skillmd--agent-behavior-definition)
  - [Why SKILL.md](#why-skillmd)
  - [SKILL.md Format](#skillmd-format)
  - [How SKILL.md Maps to CrewAI](#how-skillmd-maps-to-crewai)
- [CLI Reference](#cli-reference)
- [Configuration](#configuration)
  - [Config File](#config-file)
  - [Model Presets](#model-presets)
  - [Using Local Models (Ollama / LM Studio)](#using-local-models-ollama--lm-studio)
- [Custom Tools](#custom-tools)
- [Security Model](#security-model)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Requirements](#requirements)
- [Roadmap](#roadmap)
- [Non-Goals](#non-goals)
- [License](#license)

---

## What Is This?

Senior QA engineers spend significant time on mechanical work — boilerplate scaffolding, basic happy-path coverage, broken selector updates, repetitive data factory patterns — instead of higher-order thinking: risk analysis, edge case design, and test strategy.

**QA-Council is a multi-agent system** where specialized AI agents collaborate as a deliberative council to handle the mechanical layers of the testing workflow. Instead of a single AI doing everything, six agents **debate each other's work** — catching blind spots, challenging assumptions, and producing higher-quality test strategies and code.

The QA engineer provides direction and owns quality decisions. The council handles the mechanical execution and uses structured debate to catch what any single agent would miss.

```
🔍 Scout explores API  →  👁️ Critic challenges findings  →  🔍 Scout revises
    🧠 Strategist plans  →  👁️ Critic challenges plan
        🛠️ Engineer codes  →  👁️ Critic reviews code  →  🛠️ Engineer fixes
            📝 Reporter compiles final report
```

### Guiding Principles

- **Council, not pipeline** — agents deliberate and challenge each other, not just pass output forward
- **Human-in-the-loop** — configurable checkpoints where the human approves or redirects
- **Right-sized for the task** — not every task needs the full council; simple tasks use fewer agents
- **Open and local-first** — runs locally, works with free local models (Ollama, LM Studio)

---

## Quick Start

```bash
# Clone
git clone https://github.com/barispe/QA-council.git
cd QA-council

# Install (Python 3.11+ required)
pip install -e ".[dev]"

# Preview what would happen (no LLM calls)
qa-council run --url https://petstore.swagger.io/v2 --mode new --dry-run

# Run with a cloud API key
cp .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-...
qa-council run --url https://petstore.swagger.io/v2 --mode new

# Or run with a local model (no API key needed!)
qa-council run --url https://petstore.swagger.io/v2 --preset ollama
```

---

## Architecture

### The Council (6 Agents)

The system is composed of **5 specialized council roles + 1 Moderator**, built on [CrewAI](https://www.crewai.com/) (open-source, MIT license).

| Agent | Responsibilities | Tools | When Active |
|---|---|---|---|
| 🎯 **Moderator** | Mode detection, debate orchestration, convergence tracking, phase sequencing | — | Always |
| 🔍 **Scout** | Endpoint/page discovery, API crawling, data shape inference, auth probing | `HttpClientTool`, `SpecParserTool` | NEW: full · EXTEND: new areas · MAINTAIN: changed areas |
| 🧠 **Strategist** | Test strategy, risk prioritization, edge case identification, coverage planning | — | NEW: full · EXTEND: new feature focus · MAINTAIN: not needed |
| 🛠️ **Engineer** | Test code writing, test execution, fixture setup, selector maintenance | `FileWriterTool`, `TestRunnerTool` | Always |
| 👁️ **Critic** | Code review, assumption challenging, gap finding, edge case injection | — | Always (the most important non-obvious role) |
| 📝 **Reporter** | Run summaries, coverage gap analysis, test repository packaging | — | End of every session |

### Why These Roles

The council is designed around real QA workflows, not arbitrary agent splits:

- **Scout + Strategist** (vs. a single "Analyst") — Exploration and planning are distinct cognitive tasks. Separating them enables debate between discovery and strategy.
- **Engineer** (single role, not split into Architect + Writer) — The person designing the framework IS the one writing code. Splitting them creates artificial handoff friction.
- **Critic is essential** — Without an explicit challenger, you get a pipeline with extra steps, not a council. The Critic prevents echo chambers and catches what others miss.
- **Moderator is essential** — Required for debate orchestration. Someone must decide when discussion has converged and it's time to move on.

### Architecture Diagram

```
                         USER INPUT
                    (URL / spec / "new feature X")
                              │
                              ▼
                   ┌──────────────────┐
                   │    MODERATOR     │
                   │                  │
                   │  • Mode detect   │  Detects: NEW / EXTEND / MAINTAIN
                   │  • Debate mgmt  │  Activates only needed agents
                   │  • Checkpoints  │  Tracks convergence, handles failures
                   │  • Sequencing   │  Manages phase transitions
                   └────────┬─────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌──────▼─────┐
    │   SCOUT   │◄──►│ STRATEGIST│◄──►│  ENGINEER  │
    │           │    │           │    │            │
    │ Explore   │    │ Analyze   │    │ Write code │
    │ Discover  │    │ Prioritize│    │ Run tests  │
    │ Recon     │    │ Plan      │    │ Fix issues │
    └─────┬─────┘    └─────┬─────┘    └──────┬─────┘
          │                │                 │
          └────────────────┼─────────────────┘
                           │
                    ┌──────▼──────┐
                    │   CRITIC    │  Reviews ALL outputs
                    │  (Devil's   │  Challenges assumptions
                    │   Advocate) │  Injects edge cases
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  REPORTER   │  Compiles results
                    │             │  Creates test repo
                    │             │  Coverage analysis
                    └─────────────┘

    ◄──► = bidirectional debate (any agent can challenge any other)
```

---

## Operating Modes

90% of QA work is NOT creating frameworks from scratch. The council handles the full spectrum:

### 🟢 NEW Mode (~5% of real-world tasks)

**Trigger**: "Here's an API/app, test it from scratch"

Full council activation. All 6 agents participate with full debate. Creates scaffold, patterns, data factories, and initial test suite.

```bash
qa-council run --url https://api.example.com --mode new
```

### 🔵 EXTEND Mode (~80% of real-world tasks)

**Trigger**: "I added a new endpoint / feature, write tests for it"

The most common mode. Scout only explores new areas. Strategist designs scenarios referencing existing coverage. Engineer writes tests in the EXISTING framework patterns. Critic reviews for consistency and coverage gaps.

```bash
qa-council run --url https://api.example.com --mode extend
```

### 🟠 MAINTAIN Mode (~15% of real-world tasks)

**Trigger**: "Tests are failing after the latest deploy" / "UI changed, selectors broke"

Lightweight — only Scout, Engineer, and Critic. Scout re-explores changed areas. Engineer fixes broken selectors/assertions. Critic verifies fixes match actual app behavior. Strategist and Reporter are not needed.

```bash
qa-council run --url https://api.example.com --mode maintain
```

| Mode | Agents | Tasks | Pipeline |
|---|---|---|---|
| **NEW** | 6 | 9 | Explore → Critique → Revise → Strategize → Critique → Implement → Review → Fix → Report |
| **EXTEND** | 6 | 8 | Explore → Critique → Revise → Strategize → Implement → Review → Fix → Report |
| **MAINTAIN** | 3 | 5 | Explore → Critique → Revise → Implement → Review |

---

## How the Council Debates

### The Debate Loop

This is what makes QA-Council a **council**, not just a pipeline:

```
1. Moderator assigns work to an agent (or set of agents)
2. Agent produces output
3. Moderator routes output to Critic for review
4. Critic challenges, questions, or approves
5. Original agent responds to challenges and revises
6. Moderator detects convergence or hits round cap
7. Human checkpoint (if configured)
8. Proceed to next phase
```

### Debate Flow Example: EXTEND Mode

Here's what happens when you run `qa-council run --url <API> --mode extend`:

```
PHASE 1: RECONNAISSANCE
────────────────────────
Moderator → Scout: "Explore the new POST /users/export endpoint"
Scout: "Found endpoint. Accepts: { format: csv|json, filters: {...} }.
        Returns 202 with job ID. GET /users/export/{id} for status."

Moderator → Critic: "Review Scout's findings"
Critic: "What about error cases? What happens with invalid format?
         What's the max export size? Rate limiting?"
Scout: "Good points. Tested: invalid format → 400.
        No apparent size limit. Rate limited at 10 req/min."

PHASE 2: STRATEGY
─────────────────
Moderator → Strategist: "Design test scenarios for this feature"
Strategist: "6 test scenarios:
  1. Happy path: CSV export with valid filters
  2. Happy path: JSON export
  3. Error: Invalid format → 400
  4. Error: Invalid filters → 422
  5. Async: Poll status until complete
  6. Edge: Large dataset export timeout"

Moderator → Critic: "Challenge the strategy"
Critic: "Missing: concurrent exports by same user.
         Missing: export with no results (empty dataset).
         Test 5 needs a timeout boundary — what's 'too long'?"
Strategist: "Adding concurrent export test. Adding empty dataset.
             Timeout: 30s based on rate limit window."

PHASE 3: IMPLEMENTATION
───────────────────────
Moderator → Engineer: "Write the tests using existing framework"
Engineer: [reads existing patterns, writes 8 test cases]

Moderator → Critic: "Review the code"
Critic: "Test 3 doesn't assert the error message body.
         You're not using the existing data factory for user fixtures."
Engineer: "Fixed. Using UserFactory.create() and asserting error body."

PHASE 4: REPORT
───────────────
Reporter: "Added 8 tests covering user export feature.
           Coverage: all documented endpoints covered.
           Gaps: no load testing for concurrent exports (out of scope)."
```

---

## Human Checkpoint System

Checkpoints let you stay in control. At each checkpoint, the Moderator summarizes what was decided and what the Critic challenged, then asks you to **approve, modify, or reject**.

| Level | Description |
|---|---|
| `none` | Fully autonomous — council runs end-to-end, you review the final output |
| `phase` | Pause after each major phase (recon → strategy → implementation → report) |
| `critical` | Pause only at strategy approval and after recon (recommended default) |
| `full` | Pause after every single task (useful for debugging/learning) |

```bash
# Set via CLI
qa-council run --url <URL> --checkpoints phase

# Or in config
# qa-council.config.yaml
checkpoints: critical
```

At a checkpoint, type:
- **Enter** to continue
- **`s`** to skip remaining checkpoints
- **`q`** to quit the session

---

## SKILL.md — Agent Behavior Definition

### Why SKILL.md

Agent behavior is defined in **SKILL.md** files following the [Agent Skills open standard](https://agentskills.io/), not hardcoded in Python. This means:

- **Editable by non-programmers** — QA engineers tweak agent behavior by editing markdown, no Python needed
- **Version-controlled** — Git-trackable, diffable, reviewable in PRs
- **Portable** — same skills work across Claude Code, OpenCode, Copilot, and our CrewAI agents
- **Community-shareable** — contributors can add/improve skills without touching orchestration code
- **Token-efficient** — only load what each agent needs at each step

### SKILL.md Format

```markdown
---
name: qa-scout
description: >
  Discovers and maps API endpoints, pages, and data shapes.
  Use this skill when you need to explore a target application.
---

# QA Scout

You are an expert API and application explorer for QA purposes.

## When to activate
- User provides a URL or API base path
- A new feature needs scoping before test design

## Step-by-step process
1. Check for OpenAPI/Swagger spec at common paths
2. If spec found: parse all endpoints, methods, schemas
3. If no spec: crawl from base URL, test common routes
4. For each endpoint: test all HTTP methods, document parameters
5. Probe error cases: invalid params, missing auth, wrong methods

## Output format
Return a structured API map with endpoints, methods, params, schemas...
```

### How SKILL.md Maps to CrewAI

A `skill_loader.py` utility parses each SKILL.md and injects its content into CrewAI's `Agent()` parameters:

| SKILL.md Field | CrewAI Agent Parameter |
|---|---|
| `name` (YAML frontmatter) | `role` |
| `description` (YAML frontmatter) | `goal` |
| Markdown body (instructions) | `backstory` |

```
skills/
├── scout/SKILL.md          # API/app exploration instructions
├── strategist/SKILL.md     # Test strategy & risk analysis
├── engineer/SKILL.md       # Framework scaffold & test writing
├── critic/SKILL.md         # Adversarial review patterns
├── reporter/SKILL.md       # Report generation templates
└── moderator/SKILL.md      # Phase sequencing & debate management
```

---

## CLI Reference

```bash
# Full council (NEW mode) — 6 agents, 9 tasks
qa-council run --url <URL> --mode new

# Extend existing tests — 6 agents, 8 tasks
qa-council run --url <URL> --mode extend

# Quick fix mode — 3 agents, 5 tasks
qa-council run --url <URL> --mode maintain

# Cloud model presets
qa-council run --url <URL> --preset budget      # gpt-4o-mini everywhere
qa-council run --url <URL> --preset balanced    # mix of models
qa-council run --url <URL> --preset premium     # claude-sonnet-4-20250514 everywhere

# Local model presets (no API key needed!)
qa-council run --url <URL> --preset ollama          # llama3 via Ollama
qa-council run --url <URL> --preset ollama-qwen     # qwen2.5:14b via Ollama
qa-council run --url <URL> --preset ollama-mistral   # mistral via Ollama
qa-council run --url <URL> --preset lmstudio        # loaded model via LM Studio

# Direct local model (auto-detects base URL from prefix)
qa-council run --url <URL> --model ollama/llama3
qa-council run --url <URL> --model lm_studio/qwen2.5

# Manual base URL for any OpenAI-compatible server
qa-council run --url <URL> --model my-model --base-url http://localhost:11434

# Checkpoint levels
qa-council run --url <URL> --checkpoints none       # fully autonomous
qa-council run --url <URL> --checkpoints phase      # pause after each phase
qa-council run --url <URL> --checkpoints critical   # pause at key decisions (default)
qa-council run --url <URL> --checkpoints full       # pause after every task

# Custom config file
qa-council run --url <URL> --config my-config.yaml

# Custom output directory
qa-council run --url <URL> --output ./my-output

# Dry run — preview agents without making LLM calls
qa-council run --url <URL> --dry-run
```

### All CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--url` | *(required)* | Target API or application URL |
| `--mode` | `new` | Operating mode: `new`, `extend`, `maintain` |
| `--preset` | — | Model preset name (e.g. `budget`, `ollama`, `lmstudio`) |
| `--model` | `gpt-4o-mini` | Override default model for all agents |
| `--base-url` | — | Base URL for local LLM server |
| `--checkpoints` | `critical` | Checkpoint level: `none`, `phase`, `critical`, `full` |
| `--config` | — | Path to custom config YAML file |
| `--output` | `./output` | Output directory for generated files |
| `--dry-run` | `false` | Preview without making LLM calls |

---

## Configuration

### Config File

Default config lives at `config/qa-council.config.yaml`:

```yaml
checkpoints: critical   # none | phase | critical | full

models:
  default: "gpt-4o-mini"
  # base_url: ""  # Set for local LLMs (Ollama/LM Studio)
  per_agent:
    scout: "gpt-4o-mini"
    strategist: "gpt-4o-mini"
    engineer: "gpt-4o-mini"
    critic: "gpt-4o-mini"       # tip: use a stronger model here
    reporter: "gpt-4o-mini"
    moderator: "gpt-4o-mini"
```

**Priority order**: CLI args > config file > built-in defaults.

### Model Presets

Presets let you switch between model configurations with a single flag:

| Preset | Default Model | Notes |
|---|---|---|
| `budget` | `gpt-4o-mini` | Cheapest cloud option |
| `balanced` | `claude-sonnet-4-20250514` | Strong models where it matters, cheaper for Scout/Reporter |
| `premium` | `claude-sonnet-4-20250514` | Best model everywhere |
| `ollama` | `ollama/llama3` | Free, local via Ollama |
| `ollama-qwen` | `ollama/qwen2.5:14b` | Larger local model |
| `ollama-mistral` | `ollama/mistral` | Fast local model |
| `lmstudio` | `lm_studio/loaded-model` | Whatever you loaded in LM Studio |

### Using Local Models (Ollama / LM Studio)

No API key needed — run everything locally for free.

**With Ollama:**
```bash
# 1. Install Ollama → https://ollama.com
# 2. Pull a model
ollama pull llama3
# 3. Run QA-Council
qa-council run --url https://petstore.swagger.io/v2 --preset ollama
```

**With LM Studio:**
```bash
# 1. Install LM Studio → https://lmstudio.ai
# 2. Download a model and start the local server (port 1234)
# 3. Run QA-Council
qa-council run --url https://petstore.swagger.io/v2 --preset lmstudio
```

**Auto-detection:** Model prefixes `ollama/` and `lm_studio/` automatically configure the correct base URL — no extra config needed:
```bash
qa-council run --url <URL> --model ollama/qwen2.5:14b   # just works
```

---

## Custom Tools

Each agent has access to specific tools for its role:

| Tool | Used By | Description |
|---|---|---|
| `HttpClientTool` | Scout | Makes HTTP requests to target APIs. Supports GET/POST/PUT/DELETE with headers, params, and body. Auto-truncates large responses. |
| `SpecParserTool` | Scout | Fetches and parses OpenAPI/Swagger specifications. Extracts endpoints, methods, parameters, and schemas into a structured summary. |
| `FileWriterTool` | Engineer | Writes generated test files to disk. Includes path traversal protection to prevent writes outside the output directory. |
| `TestRunnerTool` | Engineer | Executes pytest as a subprocess with timeout handling. Captures stdout/stderr and returns pass/fail results. |

All tools are written in-house, version-controlled, and auditable — no untrusted third-party tool code.

---

## Security Model

| Concern | Mitigation |
|---|---|
| **API credentials** | Passed via `.env` environment variables, never logged or sent to LLM context |
| **No open ports** | CrewAI is a pure Python library — no WebSocket gateway, no network exposure |
| **LLM data handling** | API responses are summarized before passing to agents, not sent raw |
| **Test execution** | Docker-sandboxed via CrewAI's `code_execution_mode: "safe"` |
| **No stored secrets** | Config file references env vars, never plaintext secrets |
| **Path traversal protection** | `FileWriterTool` validates all write paths are within the output directory |
| **Custom tools only** | All tools are written by us and version-controlled. No untrusted third-party code |

---

## Project Structure

```
QA-Council/
├── skills/                       # Agent behavior (SKILL.md files)
│   ├── scout/SKILL.md            # API exploration instructions
│   ├── critic/SKILL.md           # Adversarial review patterns
│   ├── strategist/SKILL.md       # Risk-based test planning
│   ├── engineer/SKILL.md         # pytest/httpx code patterns
│   ├── reporter/SKILL.md         # Report templates
│   └── moderator/SKILL.md        # Phase sequencing rules
├── src/qa_council/
│   ├── main.py                   # CLI entry point (argparse)
│   ├── config.py                 # YAML config loader with presets
│   ├── checkpoints.py            # Interactive checkpoint system
│   ├── skill_loader.py           # SKILL.md → CrewAI Agent bridge
│   ├── agents/                   # Agent factory functions
│   │   ├── scout.py
│   │   ├── critic.py
│   │   ├── strategist.py
│   │   ├── engineer.py
│   │   ├── reporter.py
│   │   └── moderator.py
│   ├── tasks/                    # Task definitions per phase
│   │   ├── recon.py              # explore → critique → revise
│   │   ├── strategy.py           # plan → critique
│   │   ├── implement.py          # write → review → fix
│   │   └── report.py             # compile final report
│   ├── tools/                    # Custom CrewAI tools
│   │   ├── http_client.py        # HTTP requests
│   │   ├── spec_parser.py        # OpenAPI spec parser
│   │   ├── file_writer.py        # Write test files (path-safe)
│   │   └── test_runner.py        # Run pytest subprocess
│   └── crews/                    # Crew compositions per mode
│       ├── new_crew.py           # Full 9-task pipeline
│       ├── extend_crew.py        # 8-task pipeline
│       └── maintain_crew.py      # 5-task lightweight pipeline
├── config/
│   └── qa-council.config.yaml    # Default configuration
├── tests/                        # 38 unit tests
│   ├── test_skill_loader.py      # SKILL.md parsing (8 tests)
│   ├── test_tools.py             # HTTP client tool (11 tests)
│   ├── test_config.py            # Config loading (10 tests)
│   └── test_checkpoints.py       # Checkpoint system (10 tests)
├── PRD.md                        # Full product requirements document
├── pyproject.toml                # Package config & dependencies
├── .env.example                  # Environment variable template
└── .gitignore
```

---

## Running Tests

```bash
# Run all 38 tests
pytest tests/ -v

# Run specific test module
pytest tests/test_skill_loader.py -v
pytest tests/test_tools.py -v
pytest tests/test_config.py -v
pytest tests/test_checkpoints.py -v

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

---

## Requirements

- **Python 3.11+**
- **An LLM** — either:
  - A cloud API key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env`), or
  - A local model via [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai) (free!)

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| **V1: API Testing** | ✅ Shipped | HTTP-based API testing with pytest + httpx generation |
| **V2: UI Testing** | 🔜 Planned | Playwright-driven crawl, Page Object Model, TypeScript test generation |
| **V3: Scheduled Mode** | 🔜 Planned | Cron-based execution, post-deploy webhooks, Slack/email notifications |
| **V4: Visualization** | 💡 Stretch | Agent graph traces via Langfuse, cost/token dashboards |

---

## Non-Goals

Things QA-Council intentionally does **not** try to be:

- **Not a test management platform** — no UI dashboard, no test case database
- **Not a load/performance testing tool** — focused on functional correctness
- **Not a replacement for the QA engineer** — the agent cannot understand business logic intent; the human owns assertion quality and edge case judgment
- **Not a SaaS product** — open source only, runs locally
- **Not model-locked** — designed to work with any LLM provider (OpenAI, Anthropic, Ollama, LM Studio, or any OpenAI-compatible server)

---

## License

MIT
