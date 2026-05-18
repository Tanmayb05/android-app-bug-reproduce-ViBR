# Documentation Index

Welcome to ViBR docs. Start here.

## 📚 Core Reading Order

1. [Safety Rules](reference/safety-rules.md) ⚠️ — forbidden actions, read first
2. [Architecture](reference/architecture.md) — system design, layer breakdown
3. [ADB Commands](reference/adb-commands.md) — approved patterns
4. [Testing](reference/testing.md) — how to test safely
5. [Coding Standards](reference/coding-standards.md) — code style guide

## 📖 Reference Docs (Claude Implementation Guides)

- **[ADB Commands](reference/adb-commands.md)** — approved patterns, snippets, common fixes
- **[Testing](reference/testing.md)** — mock vs integration, patterns, CI rules
- **[Coding Standards](reference/coding-standards.md)** — type hints, naming, structure
- **[Safety Rules](reference/safety-rules.md)** — forbidden actions, approval checklist (read first!)
- **[Architecture](reference/architecture.md)** — 3-layer design, module structure, data flow

## 🚀 Onboarding (User Setup Guides)

- **[README](onboarding/README.md)** — project overview
- **[Getting Started](onboarding/GETTING_STARTED.md)** — quick navigation
- **[Quickstart](onboarding/QUICKSTART.md)** — 5-min setup
- **[Setup](onboarding/SETUP.md)** — full installation
- **[Setup Status](onboarding/SETUP_STATUS.md)** — what was installed

## 🎯 Project Context

**[projects/](projects/)** — ViBR-specific tools and notes

- [AGENTS.md](projects/AGENTS.md) — tool configurations
- [CHECKLIST.md](projects/CHECKLIST.md) — progress tracking
- [GEMINI.md](projects/GEMINI.md) — Gemini integration notes

## 📊 Decision History

**[decisions/](decisions/)** — Architecture Decision Records (ADRs)

Before refactoring or making big changes, check ADRs to understand *why* code is structured this way.

- [Template](decisions/0001-template.md) — how to write an ADR
- [README](decisions/README.md) — when to write, how to organize

## 🔧 Workflow Documentation


**[workflows/](workflows/)** — App-specific automation sequences

- [README](workflows/README.md) — how to document workflows
- (Add app-specific workflows here as they're built)

Examples:
- `login-flow.md`
- `search-flow.md`
- `checkout-flow.md`

## 📝 Code Examples

**[examples/](examples/)** — Copy-paste ready snippets

- **[adb-examples.md](examples/adb-examples.md)** — tap, type, screenshot, wait
- **[parser-examples.md](examples/parser-examples.md)** — parse screen, find elements

## Folder Structure

```text
docs/
├── INDEX.md                    ← You are here
│
├── reference/                  ← Claude implementation guides
│   ├── architecture.md         ← System design (read 2nd)
│   ├── safety-rules.md         ← Forbidden actions (read 1st!)
│   ├── adb-commands.md         ← ADB patterns (read 3rd)
│   ├── testing.md              ← Testing guide (read 4th)
│   └── coding-standards.md     ← Code style (read 5th)
│
├── onboarding/                 ← User setup guides
│   ├── README.md               ← Project overview
│   ├── GETTING_STARTED.md      ← Quick navigation
│   ├── QUICKSTART.md           ← 5-min setup
│   ├── SETUP.md                ← Full installation
│   └── SETUP_STATUS.md         ← What was installed
│
├── projects/                   ← ViBR-specific context
│   ├── AGENTS.md               ← Tool configurations
│   ├── CHECKLIST.md            ← Progress tracking
│   └── GEMINI.md               ← Gemini integration
│
├── decisions/                  ← Architecture Decision Records
│   ├── README.md               ← How to write ADRs
│   └── 000N-*.md               ← Individual decisions
│
├── workflows/                  ← App automation flows
│   ├── README.md               ← How to structure workflows
│   └── *.md                    ← App-specific flows
│
└── examples/                   ← Copy-paste code snippets
    ├── adb-examples.md         ← ADB patterns
    └── parser-examples.md      ← Screen parser usage
```

---

## Quick Lookup

### "How do I...?"

| Question | Answer |
| --- | --- |
| Tap a button? | [adb-examples.md](examples/adb-examples.md#tapping) |
| Parse screen XML? | [architecture.md](architecture.md#screenparser) + [parser-examples.md](examples/parser-examples.md) |
| Write a test? | [testing.md](testing.md#mock-pattern) |
| Add new workflow? | [workflows/README.md](workflows/README.md) |
| Understand design choice? | [decisions/](decisions/) → find ADR |
| Is this action safe? | [safety-rules.md](safety-rules.md#forbidden-actions) |
| Name a variable? | [coding-standards.md](coding-standards.md#naming) |
| Mock ADB? | [testing.md](testing.md#mock-pattern) |
| Use screen parser? | [parser-examples.md](examples/parser-examples.md) |

---

## Core Principles

1. **Read docs first** — before implementing anything
2. **Follow patterns** — reuse existing abstractions, don't duplicate
3. **Keep docs in sync** — if code changes, update docs
4. **Add ADR for big decisions** — document *why*, not just *what*
5. **Never tap blindly** — always read screen state first

---

## For Claude

**IMPORTANT: Before any task in ViBR:**

1. Check [INDEX.md](INDEX.md) (this file)
2. Scan relevant doc ([safety-rules.md](safety-rules.md), [architecture.md](architecture.md), etc.)
3. Look for examples in [examples/](examples/)
4. Check [decisions/](decisions/) if refactoring
5. Then write code

docs/ is long-term memory. Use it to stay consistent across sessions.

---

## Documentation Maintenance

When you make significant changes:

1. **Update relevant doc** — architecture change? Update [architecture.md](architecture.md)
2. **Add ADR if needed** — big design decision? Create [decisions/000N-*.md](decisions/0001-template.md)
3. **Add workflow if needed** — new automation sequence? Create [workflows/flow-name.md](workflows/README.md)
4. **Add examples if helpful** — copy-paste code? Put it in [examples/](examples/)

Keep implementation and docs in sync. Never leave them inconsistent.
