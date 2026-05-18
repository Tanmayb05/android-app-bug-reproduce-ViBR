# Architecture Decision Records (ADRs)

Record significant architectural decisions here. Helps future Claude understand *why* code is structured the way it is.

## When to Write an ADR

- New abstraction (e.g., "mock ADB for testing")
- Design trade-off (e.g., "sync vs async")
- Technology choice (e.g., "use Pydantic vs dataclasses")
- Constraint (e.g., "never use coordinates, always selectors")

Do NOT write ADRs for:
- Bug fixes
- Minor refactors
- Adding features to existing patterns
- Code style choices (those go in [coding-standards.md](../coding-standards.md))

## How to Write an ADR

Use [0001-template.md](0001-template.md) as your starting point.

1. Copy template
2. Name file: `000N-decision-name.md` (N = next number)
3. Fill sections: Context, Decision, Alternatives, Consequences, Related
4. Link from main [INDEX.md](../INDEX.md)

## Reading ADRs

Before refactoring a major system:

1. Find related ADR
2. Understand the context/constraints
3. Check if refactoring still respects the decision
4. Update ADR or create new one if you're changing the decision

## Active ADRs

None yet. Add as decisions are made.

Format: `000N-title` → status, date, summary

## Deprecated ADRs

None yet. Moves here when superseded by newer decision.
