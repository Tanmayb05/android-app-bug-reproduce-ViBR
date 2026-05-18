# Screen Parser Examples

How to parse XML and inspect screen state.

## Basic Parsing

```python
from screen_parser import parse_screen

xml = """
<hierarchy rotation="0">
    <node text="Login" resource-id="com.example:id/login_btn" bounds="[100,200][200,250]" />
    <node text="Password" resource-id="com.example:id/password" bounds="[100,260][200,310]" />
    <node package="com.example.app" activity="LoginActivity" />
</hierarchy>
"""

screen = parse_screen(xml)
print(screen.package)          # com.example.app
print(screen.activity)         # LoginActivity
print(screen.visible_text)     # ["Login", "Password"]
print(len(screen.clickable_elements))  # 2
```

## Finding Elements

```python
# Find by text
element = screen.find_text("Login")
if element:
    print(f"Button at {element.x}, {element.y}")
    print(f"Size: {element.width}x{element.height}")

# Find by resource-id
element = screen.find_resource_id("com.example:id/login_btn")
if element:
    adb.tap(element.x, element.y)

# Find by partial text match
for elem in screen.clickable_elements:
    if "Log" in elem.text:
        print(f"Found: {elem.text}")
```

## Filtering Elements

```python
# All clickable elements
clickable = screen.clickable_elements
for elem in clickable:
    print(f"{elem.text} @ {elem.x}, {elem.y}")

# Filter by text
buttons = [e for e in screen.clickable_elements if "button" in e.resource_id.lower()]

# Find visible elements only
visible = [e for e in screen.clickable_elements if e.visible]

# Check if element exists
has_login = any("Login" in e.text for e in screen.clickable_elements)
```

## State Inspection

```python
# Check what's visible
screen = parse_screen(adb.dump_xml())

if "Welcome" in screen.visible_text:
    print("Login successful")

if "Error" in screen.visible_text:
    print("Login failed")

# Check if we're on right screen
assert screen.activity == "MainActivity", f"Wrong activity: {screen.activity}"
assert screen.package == "com.example.app", f"Wrong package: {screen.package}"
```

## Before/After Comparison

```python
# Before action
before = parse_screen(adb.dump_xml())
before_text = set(before.visible_text)

# Perform action
adb.tap_by_text("Next")
time.sleep(1)

# After action
after = parse_screen(adb.dump_xml())
after_text = set(after.visible_text)

# Verify change
new_elements = after_text - before_text
if new_elements:
    print(f"New elements: {new_elements}")
else:
    print("No change detected")

# Verify activity changed
if before.activity != after.activity:
    print(f"Activity changed: {before.activity} → {after.activity}")
```

## Extract Data

```python
# Get all button labels
buttons = [e.text for e in screen.clickable_elements if e.clickable]
print(buttons)  # ["Login", "Sign Up", "Settings", ...]

# Get all visible text
all_text = " ".join(screen.visible_text)
print(all_text)

# Check for specific patterns
has_error = any("error" in text.lower() for text in screen.visible_text)
has_loading = any("loading" in text.lower() for text in screen.visible_text)
```

## Element Bounds & Position

```python
elem = screen.find_text("Login")

# Center of element
center_x = (elem.x + elem.width) // 2
center_y = (elem.y + elem.height) // 2

# Bottom center (useful for buttons)
bottom_x = (elem.x + elem.width) // 2
bottom_y = elem.y + elem.height - 5

# Tap at specific point within element
adb.tap(center_x, center_y)
```

## XML Navigation

```python
# Access raw XML if needed
screen = parse_screen(adb.dump_xml())

# Find elements by any attribute
for node in screen.xml_tree.findall(".//node[@package='com.example']"):
    text = node.get("text", "")
    resource_id = node.get("resource-id", "")
    print(f"{text} ({resource_id})")
```

## Full Example: Extract Form Data

```python
def extract_form_fields(adb: AdbClient) -> dict[str, str]:
    """Get all visible form fields and their values."""
    
    xml = adb.dump_xml()
    screen = parse_screen(xml)
    
    fields = {}
    for elem in screen.clickable_elements:
        # Assume EditText has resource-id like "field_username"
        if "field_" in elem.resource_id:
            field_name = elem.resource_id.split("field_")[1]
            field_value = elem.text or ""
            fields[field_name] = field_value
    
    return fields


def verify_navigation(adb: AdbClient, from_activity: str, to_activity: str) -> bool:
    """Verify navigation between screens."""
    
    # Get initial state
    before = parse_screen(adb.dump_xml())
    assert before.activity == from_activity
    
    # Perform some action (user will do this)
    time.sleep(2)  # wait for nav
    
    # Check final state
    after = parse_screen(adb.dump_xml())
    
    return after.activity == to_activity
```

## Testing with Parser

```python
import pytest
from screen_parser import parse_screen

SAMPLE_LOGIN_SCREEN = """
<hierarchy>
    <node text="Username" resource-id="com.example:id/username" />
    <node text="Password" resource-id="com.example:id/password" />
    <node text="Login" resource-id="com.example:id/login_btn" />
    <node package="com.example.app" activity="LoginActivity" />
</hierarchy>
"""

def test_parse_login_screen():
    screen = parse_screen(SAMPLE_LOGIN_SCREEN)
    
    assert screen.activity == "LoginActivity"
    assert "Login" in screen.visible_text
    assert len(screen.clickable_elements) >= 3

def test_find_elements():
    screen = parse_screen(SAMPLE_LOGIN_SCREEN)
    
    username = screen.find_text("Username")
    assert username is not None
    assert username.resource_id == "com.example:id/username"
```
