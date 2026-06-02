# Claude Repo Rules

## Project Goal
This is a Python-based Android app automation project.
It uses ADB/UI automation to inspect screens, tap/type/swipe, and run safe workflows.

## Commands
Always use `.venv/bin/python` (or activate `.venv/bin/activate` first):

- Install: `uv sync` or `pip install -e ".[dev]"`
- Run app: `.venv/bin/python approach/segment_replay.py <app_name> <good|bad> [--algo ssim|clip]`
- Run tests: `.venv/bin/python -m pytest`
- Run one test: `.venv/bin/python -m pytest tests/test_file.py -q`
- Lint: `.venv/bin/python -m ruff check .`
- Format: `.venv/bin/python -m ruff format .`
- Typecheck: `.venv/bin/python -m mypy approach/ --ignore-missing-imports`

## Claude Skills
- `/find-problem` — Analyze ViBR run, identify failures, write issue report with ViBR paper categories

## Code Style
- Python 3.11+
- Use type hints everywhere.
- Use Pydantic/dataclasses for structured data.
- Keep functions small and testable.
- No hardcoded device IDs, package names, credentials, or secrets.
- Prefer pure functions for parsing and decision logic.
- Keep ADB side effects isolated inside `adb_client.py` or `actions.py`.

## Architecture Rules
- `adb_client.py`: raw ADB commands only.
- `actions.py`: tap, type, swipe, back, wait, open app.
- `screen_parser.py`: parse XML/screenshot/screen state.
- `workflows.py`: app-specific flows.
- `planner.py`: decides next step.
- `verifier.py`: confirms action succeeded.
- Tests should mock ADB unless explicitly marked integration.

## Safety Rules
- Never automate payments, password entry, destructive deletes, or personal data submission without explicit approval.
- Before any risky action, stop and ask.
- Always verify current screen before tapping.
- Prefer selectors/text/resource-id over raw coordinates.
- If using coordinates, explain why.

## Claude Workflow
1. Read relevant files first.
2. Explain plan before editing.
3. Make the smallest change.
4. Add/update tests.
5. Run lint/typecheck/tests.
6. Summarize changed files and remaining risks.

## Coding Style to Follow

### ADB Client Pattern

```python
class AdbClient:
    def shell(self, command: str) -> str:
        ...

    def tap(self, x: int, y: int) -> None:
        self.shell(f"input tap {x} {y}")

    def text(self, value: str) -> None:
        safe = value.replace(" ", "%s")
        self.shell(f"input text {safe}")
```

### Actions Pattern

```python
@dataclass
class TapAction:
    x: int
    y: int
    reason: str
    risk: Literal["safe", "medium", "high"] = "safe"
```

### Screen State Pattern

```python
@dataclass
class ScreenState:
    package: str
    activity: str
    visible_text: list[str]
    clickable_elements: list[str]
```

## Best Claude Prompt for This Project

You are working in my Python Android automation repo.

First inspect the repo structure and relevant files.
Then propose a minimal implementation plan.

Rules:
- Keep ADB commands isolated.
- Prefer UI selectors over coordinates.
- Add tests with mocked ADB.
- Do not automate risky actions like payments/passwords/deletes.
- Run ruff, mypy, and pytest after changes.

Task: [describe task here]

## Three-Layer Architecture

Layer 1: Device control
- ADB, screenshots, XML dumps, taps, swipes

Layer 2: Understanding
- Parse screen text, buttons, app state

Layer 3: Decision/workflow
- What should the agent do next?

Do **not** mix all three in one file.

## Example Skills to Add

```
.claude/skills/
  add-adb-action/SKILL.md
  create-workflow/SKILL.md
  fix-flaky-test/SKILL.md
  safety-review/SKILL.md
```

## Most Important Rule

Claude should never tap blindly.
It should read screen → decide → act → verify.

## Secrets and Environment

Never read .env.local

## Logging & Recording Structure

Input videos: `apps/<app_name>/<quality>-quality.mp4`
- `good-quality.mp4` = reference/correct behavior
- `bad-quality.mp4` = buggy behavior to analyze

Log output: `apps/<app_name>/run_<quality>.log`
- Overwritten each run (not appended)
- Descriptive timestamps, log levels (INFO/DEBUG/WARNING/ERROR)
- Module names included for traceability

All outputs go in `apps/<app_name>/` directory alongside inputs.
