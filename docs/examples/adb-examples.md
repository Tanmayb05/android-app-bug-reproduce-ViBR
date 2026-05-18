# ADB Examples

Copy-paste ready code snippets for common ADB operations.

## Screenshots & Inspection

```python
from adb_client import AdbClient
from screen_parser import parse_screen

adb = AdbClient()

# Get current screen
xml = adb.dump_xml()
screenshot = adb.screenshot()

# Parse it
screen = parse_screen(xml)
print(screen.package)
print(screen.activity)
print(screen.visible_text)
```

## Tapping

### By Text

```python
# Tap button labeled "Login"
adb.tap_by_text("Login")

# Verify it worked
xml = adb.dump_xml()
assert "Welcome" in xml or "Loading" in xml
```

### By Resource ID

```python
# Tap button with resource-id
adb.tap_by_resource_id("com.example:id/login_button")
```

### By Coordinates (Last Resort)

```python
# Only if no selector available
adb.tap(540, 920)  # center-bottom of screen
```

## Text Input

```python
# Type text (with space escaping)
adb.text("hello world")  # outputs: input text hello%sworld

# For special chars, use clipboard
adb.shell('echo "value\'s data" | xclip -selection clipboard')
adb.key(PASTE)
```

## Navigation

```python
# Open app
adb.open_app("com.example.app", "com.example.app.MainActivity")

# Go back
adb.back()

# Go home
adb.home()

# Wait for activity
adb.wait_for_activity("LoginActivity", timeout=5)
```

## Scrolling

```python
# Swipe down (scroll)
adb.swipe(540, 400, 540, 100, duration=500)

# Multiple scrolls
for _ in range(3):
    adb.swipe(540, 400, 540, 100)
    time.sleep(0.5)
```

## Waiting

```python
# Wait for specific activity
if adb.wait_for_activity("MainActivity", timeout=5):
    print("Activity loaded")
else:
    print("Timeout waiting for activity")

# Wait for text to appear
if adb.wait_for_text("Welcome", timeout=5):
    print("Login successful")
else:
    print("Login failed")

# Wait with explicit polling
start = time.time()
while time.time() - start < 10:
    xml = adb.dump_xml()
    if "Welcome" in xml:
        break
    time.sleep(0.5)
```

## State Checks

```python
# Check current package
current = adb.get_package()
assert current == "com.example.app"

# Check current activity
activity = adb.get_activity()
assert activity == "MainActivity"

# Check screen contains element
xml = adb.dump_xml()
screen = parse_screen(xml)
element = screen.find_text("Settings")
if element:
    adb.tap(element.x, element.y)
```

## Error Recovery

```python
# If tap fails, retry
success = False
for attempt in range(3):
    try:
        adb.tap_by_text("Login")
        time.sleep(1)
        xml = adb.dump_xml()
        if "Welcome" in xml:
            success = True
            break
    except Exception as e:
        print(f"Attempt {attempt} failed: {e}")
        time.sleep(1)

if not success:
    raise RuntimeError("Login failed after 3 attempts")
```

## Device Info

```python
# Get Android version
version = adb.shell("getprop ro.build.version.release")
print(f"Android {version}")

# Get device model
model = adb.shell("getprop ro.product.model")
print(f"Device: {model}")

# Get all properties
props = adb.shell("getprop")
```

## Debugging

```python
# Dump full XML for inspection
xml = adb.dump_xml()
print(xml)

# Save screenshot for debugging
screenshot = adb.screenshot()
with open("/tmp/screenshot.png", "wb") as f:
    f.write(screenshot)

# Get last logcat lines
logs = adb.shell("logcat -d | tail -50")
print(logs)
```

## Full Example: Login Flow

```python
def login_flow(adb: AdbClient, username: str, password: str) -> bool:
    """Complete login workflow."""
    
    # Start app
    adb.open_app("com.example.app", "MainActivity")
    time.sleep(1)
    
    # Navigate to login screen
    adb.tap_by_text("Sign In")
    
    # Wait for login form
    if not adb.wait_for_text("Username", timeout=5):
        return False
    
    # Enter credentials
    adb.tap_by_text("Username")
    adb.text(username)
    
    adb.tap_by_text("Password")
    adb.text(password)
    
    # Submit
    adb.tap_by_text("Login")
    
    # Verify success
    if adb.wait_for_text("Welcome", timeout=5):
        return True
    
    # Check for error
    xml = adb.dump_xml()
    if "Invalid" in xml:
        return False
    
    return False
```
