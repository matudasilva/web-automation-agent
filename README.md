# Web Automation Agent

Phase 0 repository setup for a deterministic browser automation project.

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

No application flow is implemented yet in Phase 0.

After installation, you can verify the environment with:

```bash
pytest
```
