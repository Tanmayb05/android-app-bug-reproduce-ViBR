# Testing

## Testing Philosophy

**Default: Mock ADB. Tests must run without device.**

- Fast feedback loop
- No device dependency
- Deterministic results
- CI/CD compatible

**Exception: Integration tests.** Mark with `@pytest.mark.integration`. Require real device.

## Mock Pattern

```python
import pytest
from unittest.mock import Mock, patch

def test_parse_screen():
    sample_xml = """
    <hierarchy rotation="0">
        <node text="Login" resource-id="com.example:id/login_btn" />
    </hierarchy>
    """
    
    screen = parse_screen(sample_xml)
    assert screen.visible_text == ["Login"]

def test_tap_by_text(mocker):
    mock_adb = Mock()
    mock_adb.dump_xml.return_value = """
    <node text="Login" bounds="[100, 200][200, 250]" />
    """
    
    screen = parse_screen(mock_adb.dump_xml())
    elem = screen.find_text("Login")
    assert elem is not None
```

## Fixture Pattern

```python
@pytest.fixture
def sample_screen():
    return """
    <hierarchy>
        <node package="com.example" activity="MainActivity" />
        <node text="Settings" resource-id="com.example:id/settings" />
    </hierarchy>
    """

def test_login_flow(sample_screen, mocker):
    mock_adb = Mock()
    mock_adb.dump_xml.return_value = sample_screen
    
    # test code
```

## Integration Tests

For tests that require real ADB/device:

```python
@pytest.mark.integration
@pytest.mark.skip(reason="Requires emulator running")
def test_real_login_flow():
    """Test against actual app. Run manually only."""
    adb = AdbClient()
    adb.open_app("com.example")
    
    xml = adb.dump_xml()
    assert "Login" in xml
```

Run separately:
```bash
pytest -m integration
```

## Flaky Test Handling

If test fails intermittently:

1. **Add waits** — ADB ops may be slow
   ```python
   time.sleep(0.5)  # let animation finish
   ```

2. **Increase timeout** — device may be slow
   ```python
   adb.wait_for_activity("LoginActivity", timeout=10)
   ```

3. **Screenshot on failure** — debug output
   ```python
   def test_something(mocker, capsys):
       # ... test code ...
       if assertion_fails:
           print(capsys.readouterr())
           pytest.fail("Debug: see output above")
   ```

4. **Document why** — comment in code
   ```python
   # Flaky: emulator is slow on CI machines
   # Workaround: explicit wait instead of implicit
   ```

## Test Organization

```
tests/
  test_screen_parser.py      # Pure functions, always fast
  test_actions.py            # Mock ADB
  test_workflows.py          # Mock ADB, longer tests
  test_integration_login.py   # Real ADB, mark integration
  
  fixtures/
    sample_screens.py        # Reusable XML fixtures
    mock_adb.py              # Mock AdbClient
```

## Coverage Expectations

- **Layer 2 (parser)** — 100% unit tests
- **Layer 1 (adb_client)** — mocked, test edge cases (empty output, timeouts)
- **Layer 3 (planner/workflows)** — 80%+ mocked tests, some integration

New features without tests won't merge.

## Running Tests

```bash
# All (except integration)
pytest

# With coverage
pytest --cov=src

# Only integration
pytest -m integration

# One file
pytest tests/test_screen_parser.py -v

# One test
pytest tests/test_screen_parser.py::test_parse_login_screen -v
```

## Emulator Setup (for integration)

```bash
# Start emulator
emulator -avd Nexus_5_API_30 -no-window &

# Wait for boot
adb wait-for-device

# Check it's there
adb devices

# Run integration tests
pytest -m integration
```

## CI/CD Rules

- **Unit tests** — required for all PRs
- **Integration tests** — optional, skip in CI unless explicitly needed
- **Coverage** — 80%+ for new code

Use `pytest -m "not integration"` in CI pipeline.

## Mocking AdbClient

```python
@pytest.fixture
def mock_adb(mocker):
    adb = Mock(spec=AdbClient)
    adb.dump_xml.return_value = """
    <hierarchy>
        <node text="Login" bounds="[0,0][100,100]" />
    </hierarchy>
    """
    adb.screenshot.return_value = b"PNG_DATA"
    adb.get_package.return_value = "com.example"
    adb.get_activity.return_value = "MainActivity"
    return adb

def test_workflow(mock_adb):
    # use mock_adb
    assert mock_adb.dump_xml.called
```

## Common Test Pitfalls

**Don't:**
- Test ADB commands directly (mock them)
- Hardcode coordinates in tests
- Skip waiting for state changes
- Assume device state persists between tests
- Leave tests that require manual setup

**Do:**
- Mock at Layer 1, test Layers 2-3
- Use selectors + parsed state
- Add waits + assertions
- Reset device state or use isolated test accounts
- Make tests self-contained and repeatable
