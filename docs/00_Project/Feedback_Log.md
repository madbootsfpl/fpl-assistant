# Tester Feedback Log

A running log of tester feedback on the live app, triaged into the **Sprint 060** backlog. Raw reports
come in via GitHub Issues (https://github.com/tesheridan/fpl-assistant/issues); this table is the
**triaged** view — one row per distinct item, newest first.

**Severity:** 🔴 broken/blocking · 🟠 confusing/wrong · 🟡 polish/nice-to-have · 💡 idea

| Date | Tester | Tab | What happened / suggested | Severity | → Backlog? |
|------|--------|-----|---------------------------|----------|-----------|
| 2026-08-06 | Owner | My Squad | Player photos are left-aligned in the pitch cards — centre them | 🟡 polish | ✅ Sprint 063 (US-188) |

---

## How this feeds Sprint 060

1. A report arrives (GitHub issue or direct note).
2. Add a **triaged row** here (dedupe against existing rows; group similar reports).
3. At Sprint 060 planning, promote the **🔴/🟠** items (and any high-value 💡) into the sprint backlog.

## Themes to watch (pre-seeded from the Sprint 058/059 retros)

- **Squad resets on refresh** until downloaded — the most likely confusion; the guide pre-empts it. If
  testers still trip on it, it argues for **Path 2** (server-side persistence).
- **Same-position-only swaps** — if people want cross-position reshapes, that's a multi-swap feature.
- **Data freshness** — do testers understand the "Data as of" snapshot / that refresh is local-only?
