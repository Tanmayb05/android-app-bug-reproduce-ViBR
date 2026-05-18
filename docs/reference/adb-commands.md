# ADB Commands

## Approved Patterns

All ADB interaction goes through `adb_client.py`. Never call `adb` directly from anywhere else.

### Basic Input

```python
adb.tap(x, y)           # Tap at coordinates
adb.swipe(x1, y1, x2, y2, duration=1000)  # Swipe
adb.text("hello")       # Type text (with space escaping)
adb.key(66)             # Send key (66 = Enter)
```

### Screen Inspection

```python
adb.screenshot()        # Returns PNG bytes
adb.dump_xml()          # Returns UI hierarchy XML string
adb.get_package()       # Get current package name
adb.get_activity()      # Get current activity
```

### Navigation

```python
adb.back()              # Press back button
adb.home()              # Press home button
adb.open_app(package)   # Launch app (requires Activity name)
```

### Waits

```python
adb.wait_for_activity(activity, timeout=10)
adb.wait_for_text(text, timeout=10)
adb.wait_for_package(package, timeout=10)
```

## Text Input Safety

ADB `input text` fails with spaces. Always use escaping:

```python
# Bad — will fail
adb.shell("input text hello world")  # space breaks it

# Good — use wrapper
adb.text("hello world")  # wrapper escapes spaces as %s
# outputs: adb shell input text hello%sworld
```

For special chars (quotes, newlines), use clipboard paste:

```python
adb.shell('echo "hello\'s world" | xclip -selection clipboard')
adb.shell('input keyevent PASTE')
```

## Device State Queries

```python
# Current package
adb.shell("dumpsys window | grep mCurrentFocus")

# All activities in stack
adb.shell("dumpsys activity recents")

# Logcat last N lines
adb.shell("logcat -d | tail -20")

# Property values
adb.shell("getprop ro.build.version.release")  # Android version
```

## Screenshot + XML Pattern

Standard before-action pattern:

```python
# Get baseline
before_xml = adb.dump_xml()
before_state = parse_screen(before_xml)

# Act
adb.tap_by_text("Login")
time.sleep(1)

# Verify change
after_xml = adb.dump_xml()
after_state = parse_screen(after_xml)

# Did it work?
assert before_state.activity != after_state.activity, "Activity should change"
```

## Common Issues & Fixes

### "waiting for device"
Device not connected or ADB daemon dead.
```bash
adb kill-server
adb start-server
adb devices
```

### Text input fails
Use text escaping or clipboard:
```python
adb.text("value%swith%sspaces")  # or
adb.paste("value with spaces")
```

### Tap doesn't work
Coordinates out of bounds or app doesn't respond.
```python
# Verify screen state first
xml = adb.dump_xml()
elements = parse_screen(xml).clickable_elements
print(elements)  # inspect what's actually there

# Use selector instead
adb.tap_by_text("Button Name")
```

### Activity not transitioning
App is loading or screen is frozen.
```python
adb.wait_for_activity("NewActivity", timeout=5)
# or check for loading spinner to disappear
xml = adb.dump_xml()
assert "Loading" not in xml
```

## Reusable Snippets

### Swipe to scroll

```python
def scroll_down(adb: AdbClient, times: int = 1):
    for _ in range(times):
        adb.swipe(540, 400, 540, 100, duration=500)
        time.sleep(0.5)
```

### Find and tap element

```python
def tap_if_exists(adb: AdbClient, text: str, timeout: int = 2) -> bool:
    try:
        xml = adb.dump_xml()
        screen = parse_screen(xml)
        for elem in screen.clickable_elements:
            if elem.text == text:
                adb.tap(elem.x, elem.y)
                return True
        return False
    except Exception:
        return False
```

### Wait for specific UI

```python
def wait_for_ui(adb: AdbClient, text: str, timeout: int = 10) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        xml = adb.dump_xml()
        if text in xml:
            return True
        time.sleep(0.5)
    return False
```

## Don't Duplicate

Before adding a new ADB wrapper, check `adb_client.py` and `actions.py` for existing abstractions. Reuse instead.

If pattern is missing, add it to `adb_client.py` (if raw ADB) or `actions.py` (if higher-level).

Update this doc when adding new commands.
