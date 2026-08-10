# Sprint 140: Tester-feedback polish + a beta waitlist

**Dates:** 2026-08-10
**Status:** 📝 Planned (polish stories + a waitlist gate) — **awaiting ADR-102 for the waitlist**
**Capacity:** ~¾ session (four one-liners + a card-fit tweak + a small store feature)
**Carried Over:** none

> **Direction (owner):** clear the tester-feedback annoyances (2026-08-10 intake) **and** add a **waitlist** — when
> a registration attempt fails (the cap is full **or** the invite code is wrong), **record the email** so the owner
> can invite them later. Owner's steer: *"inc #6 and use only waitlist #5"* → **one** waitlist capturing **both**
> the cap-full (#5) and wrong-code (#6) cases (not two separate mechanisms).

---

### 🔎 Verified at planning (on real data + the code)

- **The four quick fixes are confirmed real + tiny:**
  - **Price filter** — `filters.py` hardcodes `slider("Max price (£m)", 3.5, 15.0, 15.0)`, so **Haaland (£15.5m)** is
    excluded. Fix: max = the **highest player price** (rounded up), min 0.
  - **Card season label** — `player_card.py` hardcodes **"Season 24/25"**; preseason the stats are **last season's
    carryover**, so it mislabels. Fix: **"Last season"** (preseason) / the current season once GW1 plays.
  - **Trending order** — in the "💬 Talked about" tab, **Community Signals** renders *before* **🔥 Top discussions
    this week**, burying the sharper lens. Fix: Top discussions first.
  - **Help copy** — step 7 ("Save your team") doesn't mention **☁ Save/Load across devices** (the sidebar option).
- **The hover popover truncation** is the compact card being clipped / too tall. `player_card.py`'s `compact` shows
  5 stats + the header; on the pitch it can overflow. Fix: trim the compact set + tighten type, and confirm no
  container clips it (the pitch is `overflow:visible` already — likely the *content height*, not clipping).
- **The waitlist is a sibling of the registration capture (ADR-098).** `access._registration_gate` already handles
  **wrong code** (an error) and **"full"** (a waitlist note + `FPL_SIGNUP_URL`). A `beta_waitlist(email, reason,
  created_at)` table in the **existing Supabase** (endpoint derived from `FPL_STORE_URL`, reusing the key — **no new
  secret**, like `beta_users`) + a best-effort `waitlist.add(email, reason)` slots into those two branches. **New
  privacy surface:** it holds emails of people **not admitted** — incl. **wrong-code** attempts (possible typos/
  randoms) — so the decision + posture want recording → **ADR-102**.

---

### 🎯 Sprint Goal

**Objective:** ship the tester-visible polish (price cap · card label · Trending order · Help copy · card-hover
fit) **and** a **beta waitlist** that records a would-be tester's email on any failed registration (cap-full or
wrong code) — into one Supabase table, off by default, so the owner can invite them later.

#### Success criteria
- [x] **US-345 (polish bundle)** — (a) price filter max = the highest player price (Haaland included); (b) card band
      reads **"Last season"** preseason (not "Season 24/25"); (c) Trending shows **🔥 Top discussions this week**
      before Community Signals; (d) Help step 7 mentions **☁ Save/Load** (sidebar) as the better keep-your-team
      option. Display/config only. Small tests where they bite (price max admits the top player; card label; Help
      copy; Trending order).
- [x] **US-346 (card hover fit)** — the compact hover popover **fits without truncation**: trim the compact stat set
      (~4) + tighten type/width; verify no clipping. AppTest (the compact popover renders) + a manual browser check.
- [ ] **ADR-102 (the gate)** — record the **beta waitlist**: capture the email on a **failed** registration
      (cap-full **or** wrong invite code) into one `beta_waitlist` table (reuses the store, no new secret); the
      **privacy posture** (holds emails of the *non-admitted*, incl. wrong-code — minimal, "remove me = delete the
      row", owner-only); **off by default** (registration mode + store); a **4th** opt-in, secret-gated server write
      (after squad-save/registration/analytics); extends **ADR-098**.
- [ ] **US-347 (the waitlist)** — `web_streamlit/waitlist.py` (`add(email, reason)` → a `beta_waitlist` upsert,
      best-effort, `reason ∈ {"full","bad_code"}`, reuses `user_store`'s endpoint-derivation + `clean_email`); wire
      into `_registration_gate` — on **"full"** and on a **wrong code with an email**, `waitlist.add(...)` (never
      blocks the gate). Off by default; idempotent (email PK). Unit-tested (monkeypatched requests) + a gate test.
- [ ] **No unintended drift** — the waitlist write is opt-in + secret-gated + best-effort (unset store → no write);
      existing **928** stay green; ruff clean.
- [ ] **Docs** — ADR-102 + index; BETA.md (§4 — the `beta_waitlist` table SQL + how to see/invite waitlisters);
      Help; PROJECT_STATUS; Architecture.

---

### 🧭 Design sketch

**US-345/346 — polish.** `filters.py`: `hi = max((p["price"] for p in players), default=15.0)`; `slider("Max price
(£m)", 0.0, ceil(hi*2)/2, ceil(hi*2)/2, step=0.5)`. `player_card.py`: the band label → `"Last season"` (a constant;
a later GW1 tweak can make it current-season). `6_Trending.py`: swap the two blocks in the "Talked about" tab.
`7_Help.py`: append the ☁ line to step 7. `player_card.py` compact: `order[:4]` + a slightly narrower popover.

**ADR-102 + US-347 — the waitlist.** `waitlist.py` mirrors `user_store`: `_endpoint()` derives `.../beta_waitlist`
from `FPL_STORE_URL`'s base; `add(email, reason)` = a best-effort upsert `{email, reason, created_at}` (idempotent
on `email`; keeps the first/most-relevant reason or overwrites — TBD, simplest = upsert). In `_registration_gate`:
```
if status == "full":          waitlist.add(email, "full")     # #5
elif code and entered_code != code and email:   waitlist.add(email, "bad_code")   # #6
```
Best-effort (a store hiccup never blocks the gate; wrapped like the analytics write). Off by default (no store /
no cap → no write). The owner sees the list in Supabase → invite → optionally delete the row.

**Deferred (backlog):** unique per-user invite codes; email verification; an in-app waitlist/roster admin view.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-345 | **Polish bundle** — price max · card label · Trending order · Help copy. | High | ✅ Done | ~¼ session |
| US-346 | **Card hover fit** — the compact popover shows without truncation. | Med | ✅ Done | ~¼ session |
| ADR-102 | **The beta waitlist** — capture failed-registration emails (the gate). | High | ⬜ To do | gate |
| US-347 | **The waitlist store + wiring** — `waitlist.py` + `_registration_gate`. | High | ⬜ To do | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you — when enabling the waitlist)

1. **Create the table:** in Supabase, `create table beta_waitlist(email text primary key, reason text, created_at
   timestamptz default now())` + the anon RLS (BETA.md §4).
2. It's automatic once the table exists + `FPL_USER_CAP` is set: over-cap or wrong-code attempts land in
   `beta_waitlist`. Invite from there; delete a row when done.

---

### ✅ Definition of Done

1. **Tests** — the price filter admits the £15.5m player; the card band says "Last season"; Trending renders Top
   discussions first; Help mentions ☁ Save/Load; the compact popover renders (no full grid). `waitlist.add` upserts
   with the right endpoint/reason (monkeypatched `requests`) + is a no-op without the store; the gate calls it on
   full + wrong-code (a gate test); **off by default** (no write without the store). Existing **928** green; ruff clean.
2. **Manual smoke** — Players filter shows Haaland; the card reads "Last season"; the pitch hover card fits;
   Trending order; with the store + `FPL_USER_CAP`: a wrong code / over-cap → a `beta_waitlist` row.
3. **Docs** — ADR-102 + index; BETA.md; Help; PROJECT_STATUS; Architecture.

---

### 📝 Session Progress Log

- **US-345 (polish bundle)** — four tester-visible fixes: (a) **price filter** — `filters.py` now caps at the
  **highest player price** rounded to £0.5 (`max(15.0, ceil(max_price·2)/2)`, min 0) so **Haaland (£15.5m)** is no
  longer filtered out by a stale fixed £15.0; (b) **card label** — the band reads **"Last season"** (was the
  hardcoded/misleading "Season 24/25"; the stats are last season's carryover preseason); (c) **Trending** — the
  "💬 Talked about" tab now shows **🔥 Top discussions this week first**, the long Community Signals list below;
  (d) **Help** — step 7 ("Save your team") leads with **☁ Save/Load across devices** (sidebar) as the better
  keep-your-team option. Display/config only. **+4 tests** (the pool includes the £15.5m player · the card says
  "Last season" not "24/25" · Trending order · Help mentions ☁). ruff clean. **928 → 932.** (US-346 = the card
  hover-popover fit; then ADR-102 + US-347 the waitlist.)
- **US-346 (card hover fit)** — the compact hover popover (My Squad pitch) was truncating; **zoomed it down**:
  compact `_stat_rows` now returns **4** stats (was 5), added `.pl-card.compact` CSS overrides (58px photo, smaller
  name/meta/flags/stat type, tighter padding), and narrowed the pitch `.kit-pop` to **250px** — so the whole card
  fits without cutting off. Full card (Players) unchanged. Refreshed the **Artifact preview** with the compact card
  shown beneath the full cards. Tightened the compact test (`<= 4` stats). Display-only. ruff clean. **932** (no
  net test change). *(The exact fit is a browser thing — the manual smoke on the deploy confirms no clipping,
  esp. bench kits.)* (Next: ADR-102 + US-347 the waitlist.)

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony — confirm before I gate ADR-102

1. **The waitlist scope** — I read *"inc #6 and use only waitlist #5"* as **one** `beta_waitlist` capturing **both**
   over-cap (#5, `reason="full"`) **and** wrong-code (#6, `reason="bad_code"`) emails. Correct? *(If you meant #5
   only, I'll drop the wrong-code capture.)*
2. **The gate** — a short **ADR-102** for the waitlist (it holds emails of the *non-admitted*, a real privacy
   decision), or extend **ADR-098** with a note? *(My rec: ADR-102 — the failed-attempt capture deserves its own
   record.)*
3. **Card label** — **"Last season"** now (simplest, honest preseason), auto-switching to the current season at GW1
   as a tiny follow-up? *(My rec: yes.)*
