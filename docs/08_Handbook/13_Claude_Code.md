# Chapter 13 — Claude Code

**Badges:** 📖 🧪 💻

---

## Purpose

Claude Code is an AI coding assistant that runs in the terminal. On this project it
handles implementation, refactoring, testing, and documentation work.

---

## Why We Use It

Defined in the `CLAUDE.md` AI Team Roles: Claude Code is the **implementer**. It
reads the project's docs and conventions and works within them, while Tony stays the
decision-maker who must *understand* everything before accepting it.

---

## Concepts

- **`CLAUDE.md`:** project instructions Claude Code reads and must follow (philosophy,
  coding principles, documentation rules, the "confirm before big changes" approach).
- **Confirm-first workflow:** for significant changes, explain *what/why/risks* and
  confirm before acting — a rule this project enforces.
- **Small, reviewable steps:** changes arrive as focused commits you can read.

---

## Examples

In Session 2, Claude Code was used to: draft the Sprint 001 plan, write Architecture
v0.1, produce ADR-001/ADR-002, update the journal/glossary/status, and build this
handbook — each as a separate, clearly-messaged commit.

---

## Best Practices

- Keep `CLAUDE.md` current — it's how the assistant learns the house style.
- Ask for *what/why/risks* before big changes; accept only what you understand.
- Prefer small commits so each change is easy to review.

---

## Common Mistakes

- Accepting generated code without understanding it (against the Charter's
  "AI is a Team Member" principle).
- Letting the assistant run ahead of an agreed design.

---

## Lessons Learned

- The assistant is most useful when the docs are good: clear conventions in
  `CLAUDE.md` and the docs folder produce work that fits the project.

---

## Related Documents

- [CLAUDE.md](../../CLAUDE.md)
- [Chapter 14 — ChatGPT](./14_ChatGPT.md)
- [Chapter 15 — Prompt Engineering](./15_Prompt_Engineering.md)
