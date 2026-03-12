# Readme

# Web Automation Agent

A deterministic browser automation project built with Python and Playwright.

This repository is being developed as a structured agent-style automation system focused on reliable web workflows, explicit rules, safe defaults, and maintainable architecture.

## Current Status

This project is currently in **Phase 0**.

Implemented so far:

- project bootstrap and package structure
- environment-based configuration
- structured logging
- Playwright browser bootstrap
- allowed-domain validation
- screenshot capture service
- minimal pages/flows seam
- smoke tests for bootstrap and first deterministic flow

No real business workflow is implemented yet.

## Development Approach

This project is being built with an AI-assisted development workflow using Codex and VS Code/CLI-based iteration.

The workflow emphasizes:

- clear repository instructions through `AGENTS.md`
- small, reviewable changes
- staged diffs and human validation
- smoke-test verification
- incremental commits by phase

AI assistance is used to accelerate implementation, while architecture decisions, review, and validation remain human-driven.

## What This Project Demonstrates

- agent-oriented project structure
- deterministic browser automation design
- safe configuration patterns
- modular Python architecture
- testable Playwright bootstrap
- incremental development with clear phases

## Tech Stack

- Python 3.11+
- Playwright
- Pytest
- Pydantic
- python-dotenv
- PyYAML

## Setup

Use Python 3.11 or newer.

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

## Install

Install the project and development dependencies:

```bash
pip install -e ".[dev]"
playwright install
```

Create your local environment file:

```bash
cp .env.example .env
```

## First Run

Phase 0 includes a minimal bootstrap path only.

Run the bootstrap:

```bash
python -m src.main
```

This will:

- load settings from environment
- validate the configured allowed domain
- launch a Playwright browser session
- run the first deterministic landing flow
- capture a checkpoint screenshot

## Run Tests

```bash
pytest
```

## Roadmap

Planned next steps include:

- page object structure
- deterministic workflow modules
- login/session handling
- retry and resilience improvements
- result export
- scheduled execution support

##
