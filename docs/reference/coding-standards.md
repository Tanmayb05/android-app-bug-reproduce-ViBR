# Coding Standards

## Type Hints (Mandatory)

Every function, every variable.

```python
# Bad
def parse_screen(xml):
    return result

# Good
def parse_screen(xml: str) -> ScreenState:
    elements: list[Element] = []
    return ScreenState(elements=elements)
```

### Collections

```python
list[str]           # list of strings
dict[str, int]      # dict with string keys, int values
tuple[int, str]     # tuple of (int, string)
set[str]            # set of strings
Optional[str]       # may be None
```

### Union Types

```python
from typing import Literal

result: str | None  # Python 3.10+
risk: Literal["safe", "medium", "high"] = "safe"
```

### Functions with Multiple Returns

```python
def find_element(xml: str, text: str) -> Element | None:
    """Returns element if found, None otherwise."""
```

## Dataclasses & Pydantic

Use for structured data. No plain dicts.

```python
from dataclasses import dataclass

@dataclass
class ScreenState:
    package: str
    activity: str
    visible_text: list[str]
    clickable_elements: list[Element]

# Usage
state = ScreenState(
    package="com.example",
    activity="MainActivity",
    visible_text=["Login"],
    clickable_elements=[]
)
```

For validation/serialization, use Pydantic:

```python
from pydantic import BaseModel, Field

class TapAction(BaseModel):
    x: int = Field(gt=0)  # x must be > 0
    y: int = Field(gt=0)
    reason: str
    risk: Literal["safe", "medium", "high"] = "safe"
```

## Naming

### Variables & Functions

- `snake_case` for functions and variables
- `UPPER_CASE` for constants
- `PascalCase` for classes

```python
TIMEOUT_SECONDS = 10
MAX_RETRIES = 3

def tap_by_text(text: str) -> bool:
    pass

class ScreenState:
    pass
```

### Private vs Public

- `_prefix` for internal (used within module only)
- No prefix for public (used elsewhere)

```python
class ScreenParser:
    def parse(self, xml: str) -> ScreenState:  # public
        result = self._parse_elements(xml)      # private
        return self._build_state(result)

    def _parse_elements(self, xml: str) -> list:  # internal only
        pass

    def _build_state(self, elements: list) -> ScreenState:
        pass
```

## Function Size

Keep functions small. One job each.

```python
# Bad - does too much
def login(adb: AdbClient, username: str, password: str) -> bool:
    adb.open_app("com.example")
    time.sleep(1)
    xml = adb.dump_xml()
    # ... 50 lines of logic

# Good - breaks into pieces
def login(adb: AdbClient, username: str, password: str) -> bool:
    navigate_to_login(adb)
    enter_credentials(adb, username, password)
    return verify_login_success(adb)

def navigate_to_login(adb: AdbClient) -> None:
    adb.open_app("com.example")
    wait_for_login_screen(adb)

def enter_credentials(adb: AdbClient, username: str, password: str) -> None:
    adb.tap_by_text("Username")
    adb.text(username)
    adb.tap_by_text("Password")
    adb.text(password)
```

## Imports

Group by category, alphabetical within group.

```python
# Standard library
import os
import time
from dataclasses import dataclass
from typing import Literal

# Third-party
import pytest
from pydantic import BaseModel

# Local
from adb_client import AdbClient
from screen_parser import ScreenState, parse_screen
```

Never circular imports. Follow [Architecture](architecture.md) import rules.

## Docstrings

One-liner or none. No multi-line docstring unless *why* is non-obvious.

```python
# Good - obvious from name + signature
def tap_by_text(text: str) -> bool:
    """Tap UI element with matching text."""

def parse_screen(xml: str) -> ScreenState:
    """Parse XML into ScreenState."""

# Good - explains why, not what
def wait_for_activity(activity: str, timeout: int) -> bool:
    """Wait for activity transition. Workaround for emulator lag."""

# Bad - restates code
def find_element(xml: str) -> Element | None:
    """Find an element in xml."""  # obvious, skip
```

## Constants

All at module top.

```python
TIMEOUT_SECONDS = 10
MAX_RETRIES = 3
DEFAULT_PACKAGE = "com.example"
SAFE_ACTIONS = {"tap", "swipe", "type"}

def some_function():
    # uses TIMEOUT_SECONDS
    pass
```

Never magic numbers in code.

## Error Handling

Validate at boundaries. Trust internal code.

```python
# Good - validate user input
def open_app(adb: AdbClient, package: str) -> None:
    if not package:
        raise ValueError("package cannot be empty")
    adb.shell(f"am start {package}")

# Bad - over-defensive
def parse_screen(xml: str) -> ScreenState:
    if xml is None:
        return None  # trust caller
    if not isinstance(xml, str):
        raise TypeError("xml must be string")  # obvious if types correct
    # parse...
```

## Logging

Print for debugging during tests/dev. No logging module in automated flows.

```python
# OK during test
print(f"Screen state: {screen}")
print(screen.visible_text)

# In production code, prefer assertions + explicit state checking
assert "Login" in screen.visible_text, "Expected login button"
```

## Code Comments

None by default. Only when *why* is non-obvious.

```python
# Bad
x = x + 1  # increment x

# Good
# Emulator adds 50ms delay; sleep longer than real device
time.sleep(1.0)

# Good
# Hardcoded: button has no text/resource-id, position stable across app versions
adb.tap(540, 920)
```

## Testing

- Test pure functions (Layer 2: parser, planner)
- Mock Layer 1 (adb_client)
- Don't test test infrastructure

```python
# Good - unit test of pure function
def test_parse_login_screen():
    xml = "<node text='Login' />"
    screen = parse_screen(xml)
    assert "Login" in screen.visible_text

# Good - mock ADB, test Layer 3 logic
def test_workflow_decision(mocker):
    mock_adb = Mock()
    mock_adb.dump_xml.return_value = SAMPLE_LOGIN_SCREEN
    result = planner.next_action(screen, goal)
    assert result.action == "tap"

# Bad - testing mock, not code
def test_mock_setup():
    m = Mock()
    m.return_value = "test"
    assert m() == "test"  # pointless
```

## No Exceptions for Control Flow

```python
# Bad
try:
    element = find_element(xml, text)
    tap(element)
except ElementNotFound:
    return False

# Good
element = find_element(xml, text)
if element is None:
    return False
tap(element)
```

## Line Length

Keep under 100 chars. Use parentheses for long lines.

```python
# OK
adb.tap_by_text("Login")

# OK - split when long
result = parse_screen_state(
    xml_data,
    include_clickable=True,
    timeout=10
)

# Bad - too long
result = parse_screen_state(xml_data, include_clickable=True, timeout=10)
```

## Blank Lines

- 2 blanks between top-level functions/classes
- 1 blank between methods in class
- 1 blank between logical sections within function

```python
def function_one():
    pass


def function_two():
    pass


class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        section_a()

        section_b()
```
