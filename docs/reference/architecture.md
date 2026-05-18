# Architecture

## System Design

ViBR is a three-layer Android automation agent:

```
┌─────────────────────────────────────────┐
│  Layer 3: Decision & Workflow            │
│  planner.py, workflows.py, verifier.py   │
│  → What should agent do next?            │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  Layer 2: Understanding                  │
│  screen_parser.py, state models          │
│  → What's on screen? What can I click?   │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  Layer 1: Device Control                 │
│  adb_client.py, actions.py               │
│  → Execute ADB commands, get screenshots │
└─────────────────────────────────────────┘
```

## Module Boundaries

### adb_client.py

Raw ADB wrapper. No parsing, no decision logic.

- `shell(command: str) -> str` — execute adb shell, return output
- `tap(x, y) -> None` — input tap
- `text(value) -> None` — input text
- `screenshot() -> bytes` — get PNG
- `dump_xml() -> str` — get UI hierarchy XML

**Rule: This file touches ADB only. No screen parsing. No workflow logic.**

### actions.py

High-level action wrappers. Still no parsing or decision logic.

- `tap_by_text(text: str) -> bool` — find element by text, tap it
- `type_text(value: str) -> None` — type with safe escaping
- `wait_for_activity(activity: str, timeout: int) -> bool`
- `open_app(package: str) -> None`
- `go_back() -> None`

These call `adb_client` + simple screen state checks. Return success/failure flags.

### screen_parser.py

Parse XML/screenshot into structured ScreenState.

```python
@dataclass
class ScreenState:
    package: str
    activity: str
    visible_text: list[str]
    clickable_elements: list[Element]
    xml_tree: ElementTree

def parse_screen(xml: str) -> ScreenState:
    """Pure function. No ADB calls."""
```

**Rule: Pure functions only. Testable without device.**

### workflows.py

App-specific multi-step sequences.

```python
def login_flow(adb: AdbClient, username: str, password: str) -> bool:
    """Login to app. Check docs/workflows/login-flow.md."""
    
def search_flow(adb: AdbClient, query: str) -> list[Result]:
    """Search and return results."""
```

### planner.py

Decides what to do next.

```python
def next_action(state: ScreenState, goal: Goal) -> Action:
    """Given current screen + goal, return next action."""
```

### verifier.py

Confirms action succeeded.

```python
def verify_action(before: ScreenState, after: ScreenState, action: Action) -> bool:
    """Did the action have the expected effect?"""
```

## Data Flow

```
Goal
  ↓
planner.next_action(screen_state, goal)
  ↓
Action (tap, type, wait, swipe, etc.)
  ↓
actions.py executes via adb_client.py
  ↓
adb_client.screenshot() + adb_client.dump_xml()
  ↓
screen_parser.parse_screen() → new ScreenState
  ↓
verifier.verify_action(before, after, action)
  ↓
success? → loop or return result
```

## Threading & Async

Currently **synchronous**. ADB calls block.

If adding async:
- Keep Layer 1 (adb_client) synchronous for simplicity
- Layer 2 (parsing) stays pure functions
- Layer 3 can use asyncio for orchestration

Document decision in `docs/decisions/` if changing.

## Import Rules

```
workflows.py  → imports planner, actions, screen_parser
planner.py    → imports screen_parser, actions
actions.py    → imports adb_client, screen_parser (light)
screen_parser → imports nothing from our code (pure)
adb_client    → imports nothing from our code (raw ADB)
verifier.py   → imports screen_parser (pure comparison)
```

No circular imports. No cross-layer shortcuts.

## Adding New Workflows

1. Create `docs/workflows/my-flow.md` explaining the steps
2. Implement in `workflows.py` as a function
3. Call existing actions/parsers; don't duplicate logic
4. Add tests with mocked ADB
5. Update this file if architecture changes