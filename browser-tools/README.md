# Browser Tools for Claude

Simple browser automation tools using Puppeteer for Claude Code to interact with web applications without MCP.

## Overview

These lightweight Node.js scripts provide Claude with the ability to:
- Take screenshots of web pages
- Navigate to URLs
- Execute JavaScript in the browser context

This approach is simpler and more token-efficient than MCP servers while giving Claude visual feedback from your frontend.

## Installation

```bash
cd browser-tools
npm install
```

## Tools

### 1. Screenshot Tool

Takes a screenshot of the current page and saves it to a file.

**Usage:**
```bash
node screenshot.js <output-path> [url]
```

**Examples:**
```bash
# Take screenshot of current page
node screenshot.js /tmp/page.png

# Navigate to URL and take screenshot
node screenshot.js /tmp/frontend.png http://localhost:3000
```

### 2. Navigate Tool

Navigates to a URL in a new or existing tab.

**Usage:**
```bash
node navigate.js <url> [--new-tab]
```

**Examples:**
```bash
# Navigate in current tab
node navigate.js http://localhost:3000

# Open in new tab
node navigate.js http://localhost:3000 --new-tab
```

### 3. Evaluate Tool

Executes JavaScript code in the browser context and returns the result as JSON.

**Usage:**
```bash
node evaluate.js <javascript-code>
```

**Examples:**
```bash
# Get page title
node evaluate.js "document.title"

# Get all text content
node evaluate.js "document.body.innerText"

# Query specific elements
node evaluate.js "document.querySelector('h1').textContent"

# Get all links
node evaluate.js "Array.from(document.querySelectorAll('a')).map(a => a.href)"

# Check if element exists
node evaluate.js "document.querySelector('.workflow-list') !== null"

# Get element text content
node evaluate.js "document.querySelector('.workflow-list')?.innerText || 'Not found'"
```

## How It Works

- The tools connect to Chrome via remote debugging on port 9222
- If no browser is running, screenshot and navigate will launch Chrome automatically
- Results (screenshots, console output) are saved to files that Claude can read
- Very lightweight - this README is only ~225 tokens vs 13,000+ for MCP servers

## Benefits Over MCP

1. **Token Efficient**: Minimal documentation needed
2. **Simple**: No complex server setup or protocol
3. **Composable**: Scripts output to files for easy chaining
4. **Extensible**: Easy to add new tools with just JavaScript
5. **Debuggable**: Standard Node.js scripts you can run and test manually

## Usage with Claude

Claude can use these tools through bash commands:

```bash
# Take a screenshot to see the current state
cd browser-tools && node screenshot.js /tmp/frontend.png http://localhost:3000
```

Then Claude can read the screenshot to understand what's displayed and debug issues.

## Chrome Remote Debugging

These tools use Chrome's remote debugging protocol on port 9222. The navigate and screenshot tools will automatically launch Chrome if it's not already running.

If you want to manually start Chrome with remote debugging:

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222

# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

## Extending

To add new tools, simply create a new Node.js script that:
1. Connects to the browser via puppeteer-core
2. Performs the desired action
3. Outputs results to console or files

Keep it simple and focused on one task per tool.
