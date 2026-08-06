# Tester Feedback Log

A running log of tester feedback on the live app, triaged into the **Sprint 060** backlog. Raw reports
come in via GitHub Issues (https://github.com/tesheridan/fpl-assistant/issues); this table is the
**triaged** view — one row per distinct item, newest first.

**Severity:** 🔴 broken/blocking · 🟠 confusing/wrong · 🟡 polish/nice-to-have · 💡 idea

| Date | Tester | Tab | What happened / suggested | Severity | → Backlog? |
|------|--------|-----|---------------------------|----------|-----------|
| 2026-08-06 | Owner | Trending | Trending needs a **filter**, same as Players and Player Stats. | 💡 | ✅ Sprint 075 (US-210) — reused the shared Team/Position/Player filter (ADR-064) |
| 2026-08-06 | Owner | All | Add a small **ⓘ help tooltip** over all feature options so users understand what each does. | 💡 | ✅ Sprint 074 (US-208/209, ADR-065) — `help=` on every input control + a coverage test |
| 2026-08-06 | Owner | Players / Player Stats | Need a **filter** (by player(s) / team / position, combinable, multi-select) on both. Players' top **graph isn't adding value** — remove/replace. | 🟡 polish / 💡 | ✅ Sprint 073 (US-206/207, ADR-064) — shared Team/Position/Player filter on both; scatter → a filter-responsive top-15 bar |
| 2026-08-06 | Owner | Player Stats | The CLI's **Overperf / DefCon / Cleansheet** (and xG) aren't in the web — add a Stats tab; **Players** caps at 50 (page through all + sort by team/position); **Trending** caps at 30 (page all four boards). | 🟠 gap / 💡 | ✅ Sprint 072 (US-203/204/205, ADR-063) — Player Stats page + shared paginator |
| 2026-08-06 | Owner | Build / Ask / My Squad | The web can't build a squad with the **full CLI `squad` options** (include · exclude · bench · formation · objective · no-xmins · weekly/bench-boost · include-unavailable — only budget/cheap/premium/differential are exposed). Want to build with any/all options, save it into the session so **My Squad** picks it up to tweak, then download. | 🟠 gap / 💡 | ✅ Sprint 071 (US-200/201/202, ADR-062) — full options on **Build Squad**; Ask offers "Use this squad →"; tabs renamed/regrouped |
| 2026-08-06 | Owner | My Squad | Player photos are left-aligned in the pitch cards — centre them | 🟡 polish | ✅ Sprint 063 (US-188) |
| 2026-08-06 | Owner | Ask | Ask ignores the loaded/session squad — "captain/analyse RoboTS" falls back to "(all players)" (picks B.Fernandes, who isn't in RoboTS). Ask only sees server-side `SquadStore`, not the session active squad. | 🔴 broken | ✅ Sprint 066 |

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
