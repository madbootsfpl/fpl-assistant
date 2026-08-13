# Architectural Decision Record: Help revamp + Boot Battle everywhere + the MadBoots Explainer

**Decision ID:** ADR-111
**Date:** 2026-08-13
**Status:** Accepted
**Superseded By / Replaces:** **revises ADR-068** (the original Help guide) and **extends ADR-110** (the compare card).
Mostly display/content — the one behaviour change (Boot Battle on the My Squad ⚙ panel) reuses `compare_card_html`.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner drafted a full **Help-page rewrite** (2026-08-13): a cleaner intro + trust line, a **Quick start**, a "Your
squad" block, a deadline note, **8 expanders** (Build · My Squad · Health · Plan/AI-Tips · Research · Ask · Save/Import
· Feedback), and a **new 9th — "MadBoots Explainer"**: a plain-English glossary. The current Help (ADR-068) has grown
patchy and carries **stale claims** — most importantly *"per-session, no accounts, nothing saved on the server"*,
which is **wrong since Google auth + per-user persistence went live** (ADR-106).

The draft also names features by their brand terms — and treats **⚔️ Boot Battle** (the two-player compare) as a
first-class feature reachable **from a player's card on My Squad**, not just the Players Card view. Today compare is
"🔍 Compare with" on the **Players Card view only** (ADR-110). So the copy would over-promise unless the feature
matches it.

#### Decision Drivers
- **Honest, not aspirational** — every Help claim must match the live app (fix the stale no-accounts copy).
- **Consistent brand** — "⚔️ Boot Battle" is the compare feature's name (the result card already wears the band); make
  it a real, reachable feature so the copy is true.
- **A findable glossary** — a reference people *look things up* in; findability beats compactness.
- **Keep the app's icons** — the established (standard-set) icons win over the draft's suggestions on any conflict.
- **Low risk** — Help is static content; the one behaviour add reuses the existing compare renderer.

---

### ✅ Decision

**1. Boot Battle everywhere (make the copy real).** Rebrand the compare control **⚔️ Boot Battle** and add it to the
My Squad **⚙ Player-actions panel**: with a player selected, a **"⚔️ Boot Battle — compare with…"** picker (typeable,
scoped to your **same-position squad players**) → renders the compare card (`render_player_compare`, ADR-110) in place
of the single card; the 👑/🔁 controls still act on the primary player. The **Players Card view** control is also
rebranded **⚔️ Boot Battle**. Reuses `compare_card_html` + the already-built `fixtures_by_id`/`xp_by_id` (owned
players have both) — no analytics change.

**2. The Help rewrite (8 sections).** Apply the owner's copy — intro + trust line + **Quick start** + "Your squad" +
a deadline note + the 8 expanders — **reconciled against the live app**: the Save/Import section is rewritten for
**auth-live** (saved to your account · auto-synced across devices · Download backup · Upload · import by Manager-ID
from GW1); the stale *"no accounts / nothing saved server-side"* line is removed; Boot Battle · Radar · Edge/Risk ·
the per-GW card are described as they actually work. **The app's established icons override the draft's** on any
conflict (e.g. keep 🎯 = Radar/free-kicks and 🔁 = Substitute; ⚔️ Boot Battle + 🪪 Player Card are new, kept).

**3. The MadBoots Explainer (the 9th expander) — one expander, category subheaders.** The glossary renders in a single
expander with **category subheaders** (⚽ FPL basics · 📊 Stats & analytics · 🎯 Ratings · 🔄 Squad decisions · 🧪 Squad
Lab · 🤖 AI & trust), everything visible so **Ctrl-F finds any term** (Streamlit expanders can't nest; a hidden-tab
switcher would defeat lookup). Terms are reconciled to the app's real meanings.

**4. What this is *not*.** Not an analytics/engine change. Not a new page (it stays the Help tab). Not a change to
the compare *renderer* (reused). Not a change to the other tabs.

---

### 🔀 Alternatives Considered

- **Help copy to current reality (compare on Players only).** Rejected — the owner wants Boot Battle from the card;
  building it (small) is better than watering the copy down.
- **Glossary as a segmented-control switcher.** Rejected as the primary — more compact, but a hidden category isn't
  Ctrl-F-able, which defeats a lookup reference.
- **The draft's icons as-is.** Rejected per owner — keep the app's standard set; override draft icons on conflict.

---

### 🧭 Consequences

**Positive**
- The Help is **honest** (auth-live save flow; real feature names) and easier to navigate (Quick start + glossary).
- **Boot Battle** becomes a real, consistent feature (Players *and* My Squad), reusing the compare renderer.
- A **findable** glossary — new users get the vocabulary in one place.

**Negative / risks (mitigations)**
- **A lot of prose** — the biggest risk is drift/inaccuracy. *Mitigation:* reconcile every claim against the code
  while building; a **content preview** for owner sign-off; a test asserts key sections + that the stale
  no-accounts line is gone.
- **⚙-panel compare pool is the owned 15** (not all players). *Mitigation:* that's the useful My-Squad case
  (captain/bench calls); full-pool compare stays on the Players page.
- **Glossary length** — long. *Mitigation:* clear category subheaders + Ctrl-F; it's reference, opened on demand.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (Sprint 154): **US-377** Boot Battle — the ⚙-panel compare + rebrand both controls; **US-378**
  the Help rewrite (8 sections, reconciled, app icons); **US-379** the MadBoots Explainer glossary (one expander,
  category subheaders). A content preview for sign-off. Docs: PROJECT_STATUS; Architecture; memory.
- **Not this ADR:** the cloud-LLM narration decision (parked, P2 strategic); the admin usage/logins graphs (P2).
