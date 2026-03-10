# AGENTS.md

## Project purpose
This repository contains a web automation agent for deterministic browser-based workflows.

## General rules
- Keep the architecture simple and modular.
- Prefer clarity over unnecessary complexity.
- Do not hardcode secrets, credentials, or environment-specific values.
- Keep business logic outside page classes whenever possible.
- Use explicit names for flows, pages, and services.
- Prioritize deterministic behavior over autonomous reasoning.

## Security rules
- Do not add destructive actions by default.
- Do not implement CAPTCHA solving or anti-bot evasion.
- Require explicit flags for submit/finalize operations.
- Restrict automation to approved domains only.

## Code conventions
- Use Python for implementation.
- Keep code, comments, documentation, and commit messages in English.
- Add logging around important steps.
- Capture screenshots on important checkpoints and on failures.
- Avoid arbitrary sleeps when Playwright provides stronger waiting mechanisms.

## Testing
- Add at least one smoke path for each important flow.
- Keep selectors centralized and easy to update.
- Prefer resilient locators.

## Delivery style
- Make small, reviewable changes.
- Update README whenever operational behavior changes.
- Leave clear TODOs where target-site details are still missing.