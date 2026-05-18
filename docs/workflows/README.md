# Workflows

Each workflow is an app-specific multi-step automation sequence.

## Structure

Each workflow file should document:

1. **Goal** — what the workflow accomplishes
2. **Preconditions** — what state must be true before starting
3. **Steps** — ordered actions with expected outcomes
4. **Postconditions** — final state after success
5. **Error handling** — what happens if a step fails
6. **Examples** — code snippet showing usage

## Template

```markdown
# [Workflow Name]

## Goal
[What does this do?]

## Preconditions
- App is open
- User is logged in
- [Other preconditions]

## Steps

1. Navigate to [screen]
   - Expected: [UI element visible]
2. Tap [element]
   - Expected: [screen transition]
3. Enter [data]
   - Expected: [confirmation]

## Postconditions
- [Result visible]
- [Data stored/visible]

## Error Handling
- If [condition]: [recovery action]
- If [other]: [other recovery]

## Example Code
\`\`\`python
def example_workflow(adb: AdbClient):
    # implementation
\`\`\`

## Related Workflows
- [[workflow-name]]
```

## Existing Workflows

None yet. Add as you build them.

## Guidelines

1. **One workflow per file** — `login-flow.md`, `search-flow.md`, etc.
2. **Keep steps atomic** — each step is one user action
3. **Document assumptions** — what packages/activities expected?
4. **Test coverage** — link to test file if it exists
5. **Update when code changes** — keep doc + implementation in sync

## Reusing Workflows

In code:
```python
from workflows import login_flow

# Reuse don't duplicate
login_flow(adb, username, password)
```

Don't copy-paste workflow logic into multiple files.
