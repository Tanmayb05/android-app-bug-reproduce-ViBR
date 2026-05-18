# Safety Rules

**HIGHEST PRIORITY DOCUMENT.** Claude must never violate these. Ask user before proceeding if unclear.

## Forbidden Actions (Never Automate)

**DO NOT automate without explicit user approval:**

- **Payments** — any financial transaction, purchase, transfer
- **Password entry** — auth changes, account recovery, credential submission
- **Destructive deletes** — removing accounts, data deletion, cache clear, uninstall
- **Personal data submission** — forms with PII, location sharing, analytics consent
- **System permissions** — granting camera, location, contacts access
- **Account linking** — OAuth flows, service integrations without clear approval

## Before Any Risky Action

1. **STOP** — do not proceed silently
2. **Ask user** — explain what will happen, get explicit OK
3. **Verify screen** — screenshot before acting
4. **Explain risk** — note if action is irreversible

## Screen Verification (Mandatory)

Before tapping anything:

```python
# Get current state
screenshot = adb.screenshot()
xml = adb.dump_xml()
screen = parse_screen(xml)

# Verify we're where we think
assert screen.package == "com.example.app"
assert "Login" in screen.visible_text

# Only then tap
adb.tap_by_text("Sign In")
```

**Never blind tap.** If you can't verify the screen, ask user first.

## UI Selector Hierarchy

**Prefer this order:**

1. **Text matching** — `tap_by_text("Sign In")`
2. **Resource ID** — `tap_by_resource_id("com.example:id/login_btn")`
3. **Accessibility ID** — `tap_by_accessibility_id("login_button")`
4. **Coordinates** — only if no selector works, and **explain why**

If using coordinates, add comment:

```python
# Coordinates used because button has no text/resource-id and is dynamically positioned
adb.tap(540, 920)  # "Next" button (center-bottom of screen)
```

## Race Conditions & Flakiness

ADB calls can race. After any action:

```python
adb.tap_by_text("Login")
time.sleep(1)  # wait for screen transition

# Verify new screen arrived
screenshot = adb.screenshot()
assert "Welcome" in screenshot or "Loading" in screenshot
```

**Never assume action succeeded.** Always verify state changed.

## Device-Specific Logic

**Never hardcode device IDs or package names.**

```python
# Bad
if device_id == "emulator-5554":
    adb.tap(100, 200)

# Good
screen = parse_screen(adb.dump_xml())
adb.tap_by_text(screen.find_button("Next"))
```

Use selectors + screen state. This works across devices.

## Credentials & Secrets

**Never hardcode, log, or send credentials.**

```python
# Bad
adb.text("password123")  # visible in logs

# Good
password = os.getenv("TEST_PASSWORD")  # from .env.local
adb.text(password)  # still logged, but user expects this
```

Even better: use mock auth or skip password-protected flows in tests.

## Integration Test Safeguards

Mark risky tests:

```python
@pytest.mark.integration
@pytest.mark.skip(reason="Requires real device with test account")
def test_login_flow():
    adb.text(os.getenv("TEST_USER"))
    adb.text(os.getenv("TEST_PASS"))
```

Run these manually, not in CI/CD.

## Flaky Test Handling

If a test fails intermittently:

1. Add explicit wait + state verification
2. Increase timeout
3. Add screenshot dump on failure
4. Document why it's flaky in code comment

```python
# Flaky: activity transition is slow on low-end devices
# Workaround: wait longer + verify text appears
adb.wait_for_activity("LoginActivity", timeout=5)
assert "Login" in parse_screen(adb.dump_xml()).visible_text
```

## Approval Checklist

Before implementing any workflow:

- [ ] Does it touch payments, passwords, or deletion? → User approval needed
- [ ] Does it submit personal data? → User approval needed
- [ ] Does it change device settings? → User approval needed
- [ ] Can I verify the screen state? → Yes, or skip until mockable
- [ ] Have I added waits + verification? → Yes, no blind taps
- [ ] Are selectors device-agnostic? → Yes, no hardcoded coords
- [ ] Are credentials in .env? → Yes, or skipped in tests
- [ ] Can test run without real device? → Yes (mock), or marked integration

## When in Doubt

**Ask.** Better to pause than to tap wrong button.