# Context for Claude

The implementation plan is tracked in the PLAN.md file.
When going through the implementation plan, please check off tasks in the file as they are completed.

Additional context for the plan, including the background research, is included in the RESEARCH.md file.

Do not write additional README or markdown files at the end of a session unless explicitly prompted.

# Python Development

Use the `uv` package for all python development.
You can run python scripts with `uv run python3 ...`.
There is an existing Python venv, so you should not need to create one.
Dependencies should be added using `uv add` such that the lockfile is updated accordingly.

All tests should be pytest compatible and be located in the ./tests directory.
Tests should not use mocks; write tests against the running architecture.
Tests should assume that python package is already installed and on the PATH; do not add to the system path, the venv handles package discovery.
Run pytest with `uv run pytest ...`.

Ephemeral scripts should go in the ./scripts directory.

## Code Preferences

Minimize usage of broad try/except statements in python; only use try/except when branching or critical logging context is needed.

## Container development

When possible, run all tasks and tests inside of one of the available containers through docker compose.
