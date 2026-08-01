# Chapter 15 — Prompt Engineering

**Badges:** 📖 🧪

---

## Purpose

Prompt engineering is the skill of asking AI tools clearly enough to get useful,
correct results — and of setting up standing instructions so you don't repeat
yourself.

---

## Why We Use It

We work with two AI team members (Claude Code, ChatGPT). Good prompts and good
standing instructions (`CLAUDE.md`) are what make their output fit the project.

---

## Concepts

- **Standing instructions:** `CLAUDE.md` is a persistent prompt — house rules the
  assistant follows every session.
- **Be specific:** state the goal, the constraints, and what "done" looks like.
- **Confirm-first prompts:** ask for *what/why/risks* before large changes.
- **Small scoped asks:** one clear task at a time beats a vague mega-request.

---

## Examples

Patterns that worked on this project:

- "Draft X, don't implement code yet" — kept the design phase clean.
- "Explain what will change and why before doing it" — matches the Charter approach.
- Asking for honest stubs rather than invented content (this handbook only documents
  what's actually been used).

---

## Best Practices

- Put durable rules in `CLAUDE.md`; put one-off intent in the prompt.
- Ask for reasoning, not just output, so you can learn from it.

---

## Common Mistakes

- Vague asks ("make it better") produce vague results.
- Requesting big changes without a confirm step.

---

## Lessons Learned

- The clearer the project's written conventions, the less prompting each task needs.

---

## Related Documents

- [Chapter 13 — Claude Code](./13_Claude_Code.md)
- [Chapter 14 — ChatGPT](./14_ChatGPT.md)
- [CLAUDE.md](../../CLAUDE.md)
