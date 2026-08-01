# Chapter 17 — Software Engineering Principles

**Badges:** 📖 🧪 💻

---

## Purpose

The working principles that guide *how* this project is built — the habits behind
the code and docs, drawn from the Charter and `CLAUDE.md` and proven in practice.

---

## Why We Use It

Principles keep decisions consistent when the project grows. They're the reason the
docs are tidy and the commits are small — and they're a learning goal in themselves.

---

## The principles (and how we apply them)

- **Learn first.** Understanding beats speed. Don't accept code you can't explain.
- **Small steps.** Build small working pieces; avoid large unfinished systems.
  → e.g. Sprint 001 is one vertical slice, capped at four stories.
- **Keep it simple.** Choose the simplest thing that works.
  → e.g. console output before FastAPI (ADR-002); SQLite before PostgreSQL.
- **Document the why.** Record decisions so the reasoning survives.
  → e.g. ADR-001/002 capture *why*, not just *what*.
- **One-way data flow.** External API → storage → analysis → presentation
  (Architecture §3) — lower layers never depend on higher ones.
- **Comment why, not what.** Code says what; comments explain the reason.
- **Continuous improvement.** Leave the project slightly better each session.

---

## Definition of Done (from the Charter)

A feature is complete when: code works · tests pass (where appropriate) ·
documentation updated · committed to Git · reviewed · **and you understand how it
works**.

---

## Common Mistakes

- Adding complexity "for the future" before it's needed (premature FastAPI/ORM/Redis).
- Letting layers leak into each other (e.g. display code calling the API directly).
- Big vague commits that hide the reasoning.

---

## Lessons Learned

- Agreeing the design and writing decisions down *before* coding made Sprint 001's
  scope obvious and stopped it ballooning.

---

## Related Documents

- [Project Charter](../00_Project/Project_Charter.md)
- [CLAUDE.md](../../CLAUDE.md)
- [Architecture v0.1](../03_Architecture/Architecture.md)
- [Decisions (ADRs)](../06_Decisions/)
