# Tester Feedback Log

A running log of tester feedback on the live app, triaged into the **Sprint 060** backlog. Raw reports
come in via GitHub Issues (https://github.com/tesheridan/fpl-assistant/issues); this table is the
**triaged** view — one row per distinct item, newest first.

**Severity:** 🔴 broken/blocking · 🟠 confusing/wrong · 🟡 polish/nice-to-have · 💡 idea

| Date | Tester | Tab | What happened / suggested | Severity | → Backlog? |
|------|--------|-----|---------------------------|----------|-----------|
| 2026-08-07 | Owner | Squads → My Squad | Redesign the **My Squad graphic** closer to the **Fantasy Football Hub** pitch — it "looks like a **poor cousin**". | 💡 | ✅ Sprint 099 (US-257/258, ADR-084) — a green FFH-style pitch (kits in formation + a bench strip, xP chips, (C) armband + sub badges, crowd/set-piece flags) replaces the native card-grid. Owner approved the preview ("looks great") |
| 2026-08-07 | Owner | Squads → My Squad | When I select a captain, the **GW xP doesn't account for the captain double points** — should it double for next GW or all selected? (Chips are next-GW only.) | 🟠 wrong | ✅ Sprint 098 (US-256, ADR-083) — Projected XI now adds the captain's ×2 for the **next GW only** (owner steer; captaincy is a weekly decision), with a caption saying so; "Captain (2×)" reframed to next-GW |
| 2026-08-07 | Owner | Players / Squads | If a player has **no photo**, use the **club shirt** image instead of a blank. | 💡 | ✅ Sprint 098 (US-255) — the photo falls back to the club-shirt kit (GK variant for keepers) via a cached CDN existence check; ~25% of players (no photo file despite a code) now show a shirt |
| 2026-08-07 | Owner | Squads → My Squad | Each selected player should show its **Set Piece attributes** (pens/corners/FK takers), **like it does for Trends**. | 💡 | ✅ Sprint 097 (US-253/254, extends ADR-081) — a `set_piece_flags` ⚽/🚩/🎯 line on the My Squad pitch cards + a "Set" column next to "Trends" on the Build/Health/Captain tables (and "In set" on Transfer) |
| 2026-08-07 | Owner | Squads | **Chip Strategy Guidance** — AI advice on when to use **Wildcard · Free Hit · Bench Boost · Triple Captain** from your squad, fixtures, and mini-league position. (One of 5 intake requests — the fixtures-now slice.) | 💡 | ◑ Sprint 096 (US-251/252, ADR-082) — a v0 chip-timing advisor (`chip_advisor` + a `chips` `ask` intent + a Squads "Chips" view) from per-GW xP + fixture run. Deferred: DGW/BGW (in-season) + mini-league position (leagues API, GW1) |
| 2026-08-07 | Owner | Players | **Set Piece & Ownership** — clear info on who takes **penalties · corners · free-kicks** per team + **ownership combinations** to find high-value, low-ownership **differentials**. (One of 5 intake requests — the buildable-now one.) | 💡 | ✅ Sprint 095 (US-249/250, ADR-081) — ingested corner/FK orders + `set_piece_flags`; a Players **"Set pieces"** view (order + Own%/Val/£m, filterable, differential caption) + a Pool **"Set"** flag. The other 4 intake requests remain in the Backlog (Elite Manager Comparison GW1-gated; AI Chat Assistant needs an ADR; Chip Strategy / Price Predictor partly gated) |
| 2026-08-07 | Owner | Squads → My Squad | Use the banner real estate for a **quick-view team summary** — xP over the gameweeks, players injured/suspended, etc. | 💡 | ✅ Sprint 090 (US-239/240) — a metrics row (Projected XI / Captain / Bench / Unavailable / Doubtful) + a who's-flagged caption |
| 2026-08-07 | Owner | Squads (all sub-tabs) | Want to **select the number of gameweeks** predicted over — 4–6 for a wildcard/start, 1–2 mid-season; a dropdown throughout the tab. | 💡 | ✅ Sprint 089 (US-237/238, ADR-077) — a "Gameweeks ahead" dropdown (1–8, default 5) across Build · My Squad · Health · Transfer · AI Tips; Captain stays next-GW |
| 2026-08-07 | Owner | Trending → Talked about | Only shows **1 mention** regardless of the number of mentions — can we count **all mentions**? | 🟠 wrong | ✅ Sprint 087 (US-232/233, ADR-076) — the counter was fine (1–4); the default feed is only 25 posts → now `?limit=100` (~100 posts) + the board paginated |
| 2026-08-07 | Owner | Squads → Build | On the **Preview the best XI in a shape**, show the **XI score** so a user can see the effect of different formations. | 💡 | ✅ Sprint 086 (US-230/231, ADR-075) — a "Projected XI xP" metric per shape + a gated compare-all-formations table (Δ vs best) |
| 2026-08-06 | Owner | Players → xG | **Flaw in logic:** goalkeepers with `xGI 0`/`0.04` are rated **🟢 excellent** — "how can 0 be good and 56 be good?" | 🟠 wrong | ✅ Sprint 084 (US-225, ADR-073) — rate xGI only for outfield ≥900-min players (vs that pool); GKs/low-minutes show `—`; column renamed "xGI rating" beside xGI |
| 2026-08-06 | Owner | Squads | Rename the **This week** tab to **AI Tips**. | 💡 | ✅ Sprint 084 (US-226) — label renamed; the gameweek engine (ADR-070) unchanged |
| 2026-08-06 | Owner | Ask | Show a few **example prompts** in the Ask tab. | 💡 | ✅ Sprint 084 (US-227) — an expander of 7 copy-paste examples |
| 2026-08-06 | Owner | Help | Update the **Help** tab with recent changes and improvements. | 💡 | ✅ Sprint 083 (US-224) — This week / the gameweek plan, the 🟢…🔴 ratings, the table-first Pool, a new Ask example |
| 2026-08-06 | Owner | Players / tables | **Number formatting** — keep to xx.x (Val/£m `24.2345` → `24.2`; cost `6` → `6.0`) to keep tables aligned. | 🟡 polish | ✅ Sprint 083 (US-223, ADR-072) — a shared `NumberColumn` convention (1dp money/%, 2dp xG family, integer counts, signed diffs) across the Pool, stat boards & squad tables |
| 2026-08-06 | Owner | All tabs | Home has a nice **⚽ graphic** header — do the same on every other tab. | 💡 | ✅ Sprint 082 (US-222) — an emoji-led title + tagline on all 7 tabs (👟📅🧩💬📰📈🧭) |
| 2026-08-06 | Owner | Players (stat boards) | What does a raw stat mean (**xGI/xGC**) — is it absolute or just relative? Could a **colour graphic** beside the score help a casual user read it? | 💡 | ✅ Sprint 082 (US-221, ADR-071) — a relative 🟢…🔴 **quality rating** + percentile on Clean sheets (xGC/90) & xG (xGI); clearer captions + tooltips on all four boards. (Verified: a fixed ChatGPT band table would mislabel 91/117 defenders "poor" → rate relative to the pool) |
| 2026-08-06 | Owner | Squads | Want an **AI recommendation on your squad for the upcoming gameweek**. | 💡 | ✅ Sprint 081 (US-220, ADR-070) — a grounded "this week" plan (captain·lineup·transfer·flags); an `ask` intent + a **Squads → This week** view |
| 2026-08-06 | Owner | All (data) | CLI refreshed **572** players but the app shows **569–570** — how do I ensure the Streamlit app is on fresh data? | 🟠 confusing | ✅ Sprint 081 (US-219) — the freshness caption shows the **player count** + a cloud snapshot note; a one-command **`reseed`**; DEPLOY/Help explain cloud vs local refresh |
| 2026-08-06 | Owner | Players → Pool | Flip the bar chart and table — the **table matters most**, show it first. | 🟡 polish | ✅ Sprint 081 (US-218) — `render_pool` renders the table before the top-15 bar |
| 2026-08-06 | Owner | Players / Player Stats / Trending | The filter's **Player** multiselect lists all ~570 names — scope it to the selected team(s). | 🟡 polish | ✅ Sprint 077 (US-213) — scoped by team ∧ position in the shared filter |
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
