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

# Browser Tools for Frontend Debugging

The `browser-tools/` directory contains lightweight Puppeteer-based scripts that enable Claude to inspect and interact with the web frontend without requiring MCP servers. This approach is simpler, more token-efficient, and easier to extend than traditional MCP-based browser automation.

## Available Tools

### Screenshot Tool
Takes screenshots of web pages for visual inspection.

```bash
node browser-tools/screenshot.js <output-path> [url]
```

Examples:
```bash
# Screenshot the frontend
node browser-tools/screenshot.js /tmp/frontend.png http://localhost:3000

# Screenshot current page (requires existing browser)
node browser-tools/screenshot.js /tmp/page.png
```

### Navigate Tool
Opens URLs in the browser.

```bash
node browser-tools/navigate.js <url> [--new-tab]
```

Examples:
```bash
# Navigate to frontend
node browser-tools/navigate.js http://localhost:3000

# Open in new tab
node browser-tools/navigate.js http://localhost:3000 --new-tab
```

### Evaluate Tool
Executes JavaScript in the browser context and returns results.

```bash
node browser-tools/evaluate.js <javascript-code>
```

Examples:
```bash
# Get page title
node browser-tools/evaluate.js "document.title"

# Get all text content
node browser-tools/evaluate.js "document.body.innerText"

# Check for elements
node browser-tools/evaluate.js "document.querySelector('.workflow-list') !== null"

# Get button text
node browser-tools/evaluate.js "Array.from(document.querySelectorAll('button')).map(b => b.textContent)"
```

### Click Tool
Clicks on elements specified by CSS selectors.

```bash
node browser-tools/click.js <css-selector>
```

Examples:
```bash
# Click a button
node browser-tools/click.js "button.tab-button:nth-child(2)"

# Click by class
node browser-tools/click.js ".workflow-item"
```

## Usage Pattern

When debugging frontend issues:

1. Take a screenshot to see the current state
2. Use evaluate to inspect DOM elements or application state
3. Use click to interact with the UI
4. Take another screenshot to verify the result

Example debugging workflow:
```bash
# See what's displayed
node browser-tools/screenshot.js /tmp/before.png http://localhost:3000

# Click on Workflows tab
node browser-tools/evaluate.js "document.querySelector('button.tab-button:nth-child(2)').click(); 'clicked'"

# Verify workflows are showing
node browser-tools/screenshot.js /tmp/after.png
```

## Why Not MCP?

This approach is preferred over MCP-based browser automation because:
- **Token efficient**: Simple documentation vs 13,000+ tokens for MCP servers
- **Lightweight**: No complex server infrastructure needed
- **Composable**: Scripts work with files, easy to chain operations
- **Debuggable**: Standard Node.js scripts you can run manually
- **Extensible**: Add new tools by creating simple JavaScript files

See [browser-tools/README.md](browser-tools/README.md) for more details.
