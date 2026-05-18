# ViBR: Android App Automation via ADB

Python-based agent that automates Android apps using ADB. Inspects screens, parses UI state, makes decisions, then executes actions (tap/type/swipe). Never acts blindly — always read screen → decide → act → verify.

## Tech Stack

- **Python 3.11+** (type hints mandatory)
- **ADB** for device control
- **pytest** for testing (mock ADB by default)
- **ruff** for linting/formatting
- **mypy** for type checking
- **Pydantic/dataclasses** for structured data

## Quick Start

```bash
# Install
uv sync
# or
pip install -e ".[dev]"

# Run app
python -m src.app.main

# Tests
pytest
pytest tests/test_file.py -q

# Lint
ruff check .
ruff format .

# Type check
mypy src
```

## Architecture: 3 Layers

**Layer 1: Device Control**

- ADB commands, screenshots, XML dumps, input events (tap/swipe/type)
- File: `adb_client.py` (raw shell calls only)

**Layer 2: Understanding**

- Parse screen text, buttons, activity state, visible elements
- Files: `screen_parser.py`, UI state models

**Layer 3: Decision & Workflow**

- Choose next action based on screen + goal
- Files: `planner.py`, `workflows.py` (app-specific flows), `verifier.py` (confirm success)

**Rule: Do NOT mix layers in one file.**

## File Layout

| File | Responsibility |
| --- | --- |
| `adb_client.py` | Only raw ADB shell calls, no parsing |
| `actions.py` | Tap, type, swipe, back, wait, open app helpers |
| `screen_parser.py` | Parse XML/screenshots into ScreenState |
| `planner.py` | Decide next step from current state |
| `workflows.py` | App-specific sequences (login flow, form filling, etc.) |
| `verifier.py` | Confirm action succeeded before continuing |
| `tests/` | Mock ADB unless marked `@pytest.mark.integration` |

Add new modules here. Do NOT scatter logic across files.

## Coding Rules

### Type Hints (Everywhere)

```python
def tap(self, x: int, y: int, reason: str) -> None: ...
def parse_screen(xml: str) -> ScreenState: ...
```

### Structured Data (Use Dataclass or Pydantic)

```python
@dataclass
class ScreenState:
    package: str
    activity: str
    visible_text: list[str]
    clickable_elements: list[str]

@dataclass
class TapAction:
    x: int
    y: int
    reason: str
    risk: Literal["safe", "medium", "high"] = "safe"
```

### Pure Functions for Logic

- Parsing, decision-making, validation → pure functions (no ADB calls inside)
- ADB side effects → isolated in `adb_client.py` or `actions.py`
- Keep functions small and testable

### No Secrets in Code

- Never hardcode: device IDs, package names, credentials, API keys
- No reading `.env.local` directly; use config module if needed

## Testing

**Default: Mock ADB**

```python
def test_parse_screen(mocker):
    mocker.patch("adb_client.AdbClient.shell", return_value=sample_xml)
    result = parse_screen(sample_xml)
    assert result.package == "com.example.app"
```

**Integration tests only when necessary** (mark with `@pytest.mark.integration`)

- Real device, real ADB calls
- Run separately: `pytest -m integration`

## Safety Rules (Non-Negotiable)

**NEVER automate without explicit approval:**

- Payments / financial transactions
- Password entry / auth changes
- Destructive deletes / data erasure
- Personal data submission

**Before risky actions: STOP and ASK**

**Always verify current screen before tapping:**

- Get screenshot/XML first
- Check package/activity
- Find UI element by text/resource-id/selector (not blind coordinates)

**Coordinates are last resort:**

- Prefer `text` or `resource-id` selectors
- If coordinates required → explain why in code + action reason

## Claude Workflow

1. **Inspect** relevant files first (use code-review-graph tools)
2. **Explain** plan before editing
3. **Make** smallest change (no cleanup unless asked)
4. **Test** with mocked ADB; add/update tests
5. **Lint/typecheck/test** — run all three: `ruff check . && mypy src && pytest`
6. **Summarize** changed files + risks

## Documentation Strategy

**IMPORTANT: Before implementing anything, always check `docs/` folder for existing architecture, workflows, constraints, and decisions. Do not reinvent patterns already documented.**

Think of it as: **CLAUDE.md = operating system, docs/ = long-term memory, ADRs = reasoning history, workflows/ = reusable automation intelligence.**

### docs/architecture.md

Source of truth for:

- System design and module boundaries
- Event/data flow and agent orchestration
- Threading/async strategy

Claude must follow this architecture unless explicitly instructed otherwise.

### docs/adb-commands.md

Contains:

- Approved ADB patterns and safe command usage
- Reusable snippets and device interaction standards

Before introducing new ADB logic:

1. Check existing commands
2. Reuse existing abstractions
3. Avoid duplicate shell wrappers

### docs/testing.md

Contains:

- Testing philosophy (integration vs mock)
- Flaky test handling
- Emulator/device setup rules

All new features must follow these testing standards.

### docs/safety-rules.md

**Highest priority document.**

Contains:

- Forbidden automation behaviors
- Risky workflows and approval requirements
- Sensitive action restrictions

Claude must never violate these rules.

### docs/decisions/

Architecture Decision Records (ADRs). Each file explains:

- Why a decision was made
- Alternatives considered
- Tradeoffs

Before refactoring: inspect related ADRs to preserve intentional design choices.

### docs/workflows/

Contains app-specific automation flows (login, onboarding, search, etc.).

Claude should extend existing workflows instead of duplicating logic.

### Documentation Maintenance Rules

Whenever making significant changes:

1. Update relevant docs
2. Add new ADR if decision is important
3. Keep examples synchronized with implementation

**If implementation differs from docs: either update implementation OR update docs. Never leave them inconsistent.**

### Preferred Development Flow

1. Read docs first
2. Inspect implementation second
3. Explain understanding
4. Propose plan
5. Implement minimal clean changes
6. Update docs if needed
7. Run tests and verification

### Anti-Patterns

Do NOT:

- Bypass documented abstractions
- Add duplicate utilities
- Create alternate ADB wrappers
- Hardcode device-specific assumptions
- Ignore existing workflows
- Introduce hidden side effects

## MCP Tools: code-review-graph

**IMPORTANT: Use code-review-graph MCP tools BEFORE Grep/Glob/Read.** Cheaper, faster, gives structural context (callers, tests, impact).

| Tool | Use when |
| --- | --- |
| `detect_changes` | Reviewing code changes — risk analysis |
| `get_review_context` | Need source snippets for review |
| `get_impact_radius` | Blast radius of a change |
| `get_affected_flows` | Which execution paths are impacted |
| `query_graph` | Trace callers, callees, imports, tests |
| `semantic_search_nodes` | Find functions/classes by keyword |
| `get_architecture_overview` | High-level codebase structure |
| `refactor_tool` | Plan renames, find dead code |

Graph auto-updates on file changes. Use `query_graph pattern="tests_for"` to verify coverage.

## Common Gotchas

- **Blind taps fail.** Always screenshot + parse before action.
- **Coordinates drift between devices.** Use selectors when possible.
- **Mocked tests != real behavior.** Add integration tests for critical flows.
- **ADB race conditions.** Add `wait` steps after action; verify state changed.
- **Hardcoded package names break.** Use constants or config.

## Secrets & Environment

- **Never read `.env.local`** in code
- Use environment variables or secure config module
- Never commit API keys, tokens, device IDs
- `.env.local` stays on local machine only
