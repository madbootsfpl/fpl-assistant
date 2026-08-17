# Sprint 159: "Your team" visibility polish (US-386 / US-387)

**Dates:** 2026-08-17
**Status:** ✅ Complete — US-386 + US-387 (extends ADR-113, display-only, no new ADR). 994 → 998 tests.
**Capacity:** ~⅓ session
**Carried Over:** none

> **Trigger — smoke-test feedback (tester, 2026-08-17) on the Sprint-158 persistence work.** The **win:** made a
> transfer on iPhone → refreshed Mac → the change showed. Cross-device account sync **works**. The gaps were all
> *visibility*: **"it's not obvious where Save/Persist/Backup is"** (the biggest point); **"my team needs to stand
> out — box it in colour"**; the upload label wording; and a downloaded `TS.json` came back as `squad-13.json`.

---

### 🎯 Delivered

**US-386 — the brand "Your team" status card.** `team_banner_html(squad, *, is_yours, synced)` renders a prominent
MADBOOTS-boxed card at the **top of My Squad** (purple→orange accent bar, brand tint, the MADBOOTS mark):
- **Your team:** the **team name** big + a **"🔄 Synced across your devices"** pill (signed in) / **"💾 This
  session"** pill (not) + the reassurance line → your team stands out and Save/backup is signposted.
- **The demo:** a muted, dashed **"👀 You're viewing the demo squad"** prompt (with the mark) → the default never
  looks like your team.
- The **⚙ Your team panel** now **auto-expands when it isn't your team** (demo/none → import is immediate) and
  collapses once you have a synced team; its duplicate sync-status line is removed (the card owns it).
- Owner-approved via an Artifact mock before building.

**US-387 — copy + filename.**
- Upload label → **"…or restore your team from a backup file"** (was "…upload a squad.json backup").
- **Download named after the team** — `_safe_filename("TS") → "TS.json"`, so a backup is identifiable and the
  browser stops de-duping a generic `squad.json` into `squad-13.json`.

---

### ✅ Definition of Done

1. **Tests (+4 → 998, ruff clean):** the card names your team (State A) · the demo prompt when it isn't yours
   (State B) · the synced state + account team name when signed in · `_safe_filename` slugging. Panel/label tests
   updated for the new expander title + upload copy.
2. **Manual smoke** (owner, post-deploy): on My Squad the brand card names your team + shows Synced; the demo shows
   the "make it yours" prompt; download a backup → it's named after the team; the upload label reads clearly.
3. **Docs:** this sprint + lessons; PROJECT_STATUS; Feedback_Log (smoke-test batch resolved); memory.

---

### 📋 Sprint Review

Display-only polish that closed the visibility gap the persistence fix exposed — the architecture was right
(Sprint 158), it just wasn't *legible*. A brand card at the top makes the team obvious and signposts backup; two
copy/filename nits fixed alongside. The tester's headline (cross-device sync) was already working — this is the
finish.

### 🧠 Lessons

- **"Works" and "obvious it works" are different deliverables.** Sprint 158 made persistence correct; the tester
  still couldn't *see* their team or the save controls. A visible, branded status card — not more logic — was the
  fix. Watch for the gap between a correct model and a legible one.
- **A status card doubles as a signpost.** Putting the sync state in a prominent card let the panel below shed its
  own status line and stay tidy — one source of truth for "where's my team", and the controls one glance beneath.
- **Name user files after the user's thing.** A hard-coded `squad.json` looks tidy in code but the browser turns
  repeated downloads into `squad-13.json`; naming the file after the team makes each backup identifiable.
- **Small copy matters.** "upload a squad.json backup" (jargon) → "restore your team from a backup file" (intent) —
  a one-line change that makes the control self-explanatory.
