# madboots.com — homepage copy

**Audited:** 2026-08-29 against the live page and the live app.
**Status:** ✅ **Both changes applied 2026-08-29** — awaiting deploy.

**📍 The source is `~/madboots-site/index.html`** (with `favicon.png` + `og-image.png`). Not in this repo and
not a git repo; it was missed for two audits because the search only ever covered `~/Projects`. **Look there
first next time.** Deploy is a drag-and-drop of that folder to Cloudflare Pages — no `wrangler.toml`, no
`package.json`, nothing to build.

⚠️ **No backup was taken** — the `cp` was in a command the sandbox blocked, so `index.html` is edited in
place. The original wording is quoted verbatim below if it ever needs reverting.

✅ **Checked and needing nothing:** the `og-image.png`, the `<title>`, and every `og:` / `twitter:` meta tag.
They describe the **product** (*"does the maths for you"*, *"one honest expected-points number"*) and never
the feature list — so they do not go stale when a page is renamed. The perishable copy was all in the body.

> **This file was rewritten, not appended to.** It had grown three stacked "update" sections whose replacement
> grid still advertised **Ask** — a deck about stale copy, going stale. One current version only, from here on.

---

## ✅ What is accurate today — leave alone

- The hero: *"The FPL tool that does the maths for you — captain, transfers, fixtures and your whole squad,
  all from one honest expected-points number. The analytics decide; you stay in control."*
  **Note the site already dropped *"The AI explains"*** from its tagline — it was ahead of the app, which only
  caught up on 2026-08-29 (ADR-168).
- *"🔒 Invite-only beta — Free · email-only sign-in · your data stays yours · a personal project."*
- The sign-in line, the disclaimer, the footer.
- **🎯 One honest number** and **⚙️ Your whole week** — both still true.

---

## ✅ Change 1 (APPLIED) — the ✅ card claimed an AI that isn't there

**Currently:**

> ✅ **Grounded, not guessing** — Answers are checked against the real data and marked ✓ or ⚠.
> **The AI only puts it into words** — the analytics make the call.

The second sentence is **not true of the hosted app**. There is no model on Streamlit Cloud, so nothing puts
anything into words for a visitor who signs up — `DEPLOY.md` has said so all along, and ADR-168 removed the
same claim from the in-app mantra. It is the last place still making it.

**Replace with:**

> ✅ **Grounded, not guessing** — Every answer is checked against the real data and marked ✓ or ⚠, and shows
> the working behind it: the number, where it came from, and what we don't know.

That is what the app actually does, everywhere, including on Cloud — the trust line, the named outlet behind a
reported transfer, the reasons under a shortlist pick.

---

## ✅ Change 2 (APPLIED) — "What's inside" described an older app

Two entries are renamed, one is retired, and the most distinctive things built since are missing.

| currently | reality |
|---|---|
| **Fixtures** — a difficulty ticker + who to target | split into **FDR** (the ticker) and **Team DNA** (ADR-169) |
| **Squad optimiser** — a legal 15 to your budget | renamed **Squad Lab**, now inside My Squad (ADR-166) |
| **Ask** — plain-English questions, grounded answers | 🔴 **retired** (ADR-168) — must go |
| — | **Signals** missing — press + crowd departure detection, the most distinctive thing in the app |
| — | **Leagues** missing — effective ownership, captain split, head-to-head |
| — | **Scout** missing — the players two or more stat boards agree on |
| Players · Transfers · Captain | accurate, keep |

**Replacement grid (six slots, same voice — name, em dash, one plain claim):**

- **Players** — the whole pool, sortable stats
- **Signals** — injuries, unexplained sell-offs and reported moves out of the league, most reliable first
- **Transfers & captain** — the best swaps by XI gain, and who to armband, with the why
- **Leagues** — effective ownership, the captain split, and a head-to-head against any rival
- **Team DNA & FDR** — how strong every club is at both ends, and the week-by-week difficulty
- **Squad Lab** — a legal 15 to your budget, for a wildcard or a fresh season

**Seven shipped, not six.** `.chips` is `display:flex; flex-wrap:wrap` — a wrapping pill list, not a 2×3
grid — so the seventh reflows rather than stranding itself, and **Scout** is the clearest example of what the
app does that a spreadsheet doesn't.

---

## 🎯 What to lead with, if the grid is ever reordered

The competitive read (Roadmap): fplapex is the solver, aceanalyst the visualiser, FFH the card-and-menu.
**Nobody else is doing Signals** — press and crowd agreeing that a player is leaving the league, sourced and
dated. **Nobody else shows its working** the way the ✓/⚠ trust line does.

*"Ask it anything"* is what every tool claims. **"Here is the number, here is why, and here is what we don't
know"** is what almost none of them do — and it is now the app's actual mantra:
*"The analytics decide. Every answer shows its working. You make the call."*

---

## ✅ Resolved

**`hello@` and `info@madboots.com` both receive email** — owner-confirmed, 2026-08-28.
The in-app Home tour is fixed **and guarded by a test** that derives the page list from `pages/` (US-433).
**This page has no such guard**, because its source is not in the repo — which remains the strongest argument
for moving it here (see ADR-103's parked brand-infra changeover).
