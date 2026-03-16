# Readme

# Web Automation Agent

A deterministic browser automation project built with Python and Playwright.

This repository is being developed as a structured agent-style automation system focused on reliable web workflows, explicit rules, safe defaults, and maintainable architecture.

## Current Status

This project is currently in **Phase 2 in progress**.

Implemented so far:

- project bootstrap and package structure
- environment-based configuration
- structured logging
- configurable Playwright browser bootstrap
- allowed-domain validation
- screenshot capture service
- per-run artifact organization
- concise execution summary logging
- reusable UI action helpers
- generic target page/flow seam
- minimal pages/flows seam
- private authenticated marketplace flow scaffold that stops before final publish
- first deterministic landing flow
- Firefox persistent-profile local run support with manual login pause
- failure evidence capture on landing-flow errors
- smoke tests for bootstrap and landing flow

The browser automation foundation is complete, and the first deterministic flow is in place. Broader business workflows are not implemented yet.

The current private site-specific step is limited to navigating an authenticated marketplace management area, opening the group-share flow, selecting the destination group, and stopping at a non-destructive composer checkpoint before the final publish action.

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

The current bootstrap runs a landing precheck and then the non-destructive marketplace group-share flow.

Run the bootstrap:

```bash
python -m src.main
```

This will:

- load settings from environment
- validate the configured allowed domain
- launch the configured Playwright browser session
- optionally reuse a persistent browser profile
- optionally pause after opening `BASE_URL` so you can complete login manually and press Enter in the terminal
- run the landing precheck flow
- run the marketplace group-share flow with the configured listing title and group name
- create a per-run artifact directory under the configured screenshot base path
- emit a concise execution summary for the run
- capture a success checkpoint screenshot
- capture failure evidence if the landing flow raises after navigation starts
- stop before the final publish action

## Local Real-Web Run

Recommended local `.env`:

```dotenv
BASE_URL=https://www.facebook.com
ALLOWED_DOMAIN=facebook.com
BROWSER=firefox
HEADLESS=false
BROWSER_PROFILE_DIR=./runtime/profiles/firefox-marketplace
SCREENSHOT_DIR=./screenshots
WAIT_FOR_MANUAL_READY=true
MARKETPLACE_LISTING_TITLE=Botitas de gamuza tipo desert
MARKETPLACE_GROUP_NAME=Las Piedras, la paz Progreso, Colon
```

Relevant variables:

- `BROWSER=chromium|firefox|webkit`
- `BROWSER_PROFILE_DIR` enables Playwright persistent context when set
- `WAIT_FOR_MANUAL_READY=true` opens `BASE_URL` and waits for Enter before continuing
- `MARKETPLACE_LISTING_TITLE` is matched partially to tolerate punctuation or truncated UI text
- `MARKETPLACE_GROUP_NAME` selects the destination group in the share flow

## Run Tests

```bash
pytest
```

## Roadmap

Planned next steps include:

- login/session handling
- retry and resilience improvements
- richer flow result handling and downstream consumers
- result export
- scheduled execution support

##
