# Claude Code Project Instructions

## Scope & Boundaries

- **Only operate within this project folder.** Do not read, modify, create, or delete files outside of this directory under any circumstances — even if a task seems to require it.
- If a task appears to need changes outside this folder, stop and explain why, then ask how to proceed.

---

## Approval Before Changes

Before modifying any existing project file, you must:

1. **State clearly** which file(s) you intend to change and why.
2. **Show a summary** of what will be added, removed, or refactored.
3. **Wait for explicit approval** (e.g. "yes", "go ahead", "approved") before making any edits.

> This applies to all file types: source code, configs, assets, environment files, etc.
> New file creation in the project folder is allowed without approval unless it involves sensitive config files (`.env`, credentials, etc).

---

## Updating This File (CLAUDE.md)

- You may **suggest updates** to this file when:
  - A new consistent workflow or rule has emerged during our work.
  - A repeated task could benefit from a documented standard.
  - Project scope, structure, or stack has changed significantly.
  - A skill has been created that should be referenced here.

- When suggesting an update, present the proposed change and say:
  > *"I'd like to update CLAUDE.md to reflect this — shall I?"*

- **Never modify CLAUDE.md without explicit permission.**

---

## Skill Recommendations

When you identify a task that is routine, repetitive, or complex enough to benefit from a reusable skill, proactively recommend it. Use this format:

> 💡 **Skill Suggestion:** This task (e.g. generating release notes, scaffolding components, formatting reports) seems like a good candidate for a saved skill. Want me to create one?

Recommend a skill when:
- The same type of task is likely to recur (e.g. database migrations, test scaffolding, API boilerplate).
- A task involves a multi-step workflow that should stay consistent.
- An external tool or format is involved (e.g. Excel exports, PDF generation, slide decks).
- A task takes significant setup that could be templated.

---

## General Behavior

- Be concise in explanations — prefer showing over telling.
- When refactoring, preserve existing logic unless explicitly asked to change it.
- Flag any deprecated dependencies, security concerns, or anti-patterns you notice, but don't fix them unless asked.
- Always confirm the intended outcome before beginning large or multi-file tasks.
- If something is ambiguous, ask one focused clarifying question before proceeding.