# Architectural Decision Record: MADBOOTS vocabulary — a brand lexicon for the tool labels

**Decision ID:** ADR-107
**Date:** 2026-08-12
**Status:** Accepted
**Superseded By / Replaces:** **extends ADR-103** (the MADBOOTS brand identity) and picks up the follow-on that
**ADR-105 explicitly deferred** ("the MADBOOTS vocabulary — *Pick/Edge/Risk/Radar* inside the cards — is a separate
later item"). Display-label only — **no** change to analytics, `decision_xp`, code identifiers, or any view's
behaviour.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The MADBOOTS rebrand (ADR-103) put the name, wordmark, badge, and palette on every surface — but the **tool labels
themselves are still generic analytics wording**: *"Why"*, *"Risk"*, *"Target by fixtures"*, *"AI Tips"*. The
backlog (branding-E) proposed turning these into a small set of **brand terms** so the product *reads* like MADBOOTS,
not like a spreadsheet — **MadBoots Pick** (the recommendation), **Edge** (the advantage / the "why"), **Risk**,
**Captain**, **Radar** (players to watch).

**The governing constraint — the owner's standing design principle (2026-08-12):** *MADBOOTS' branding and UX must
stay **clean, modern, and easy to navigate**; keep the brand vocabulary tasteful, **not gimmicky**.* The failure mode
to avoid is gluing "MadBoots" onto every label, or renaming clear words into cute-but-vaguer ones — that trades
clarity for branding, the opposite of the principle.

#### Decision Drivers
- **Read like the brand** — a distinctive vocabulary is part of a product's identity; "Why/Risk/Target" is anonymous.
- **Clarity first** — a rename must be *at least as clear* as the word it replaces, never just more branded.
- **A small, coherent lexicon** — a few real words that hang together beat many sprinkled brand tags.
- **Display-only, zero risk** — labels only; the analytics, `decision_xp`, and every code identifier are untouched.
- **Reversible + incremental** — adopt the terms that clearly earn their place now; defer the marginal ones.

---

### ✅ Decision

**Adopt a small MADBOOTS lexicon for the tool labels, applied where it improves (or holds) clarity — brand as a light
signature, never glued onto every label.** The reference lexicon and its verdicts:

| Brand term | Concept | Maps to (surface) | This sprint |
|---|---|---|---|
| **Radar** | Players to watch | `🎯 Target by fixtures` (Fixtures subheader) | ✅ **Adopt** — rename to `🎯 Radar` |
| **Edge** | The advantage / the "why" | the `explain` **"Why"** heading (build explanation + captain card) | ✅ **Adopt** — `Why` → `Edge` |
| **Risk** | The downside | the `explain` **"Risk"** heading | ✅ **Keep** + fix the `Risks`/`Risk` inconsistency |
| **Captain** | The captain pick | captain card / sub-tab (already `Captain` / `Captain Pick`) | ✅ **Keep** — already on-brand |
| **Pick** | The recommendation | the **"AI Tips"** sub-tab (a whole-week plan) | ⏸️ **Defer** — see below |

**1. Radar (adopt).** `🎯 Target by fixtures` → **`🎯 Radar`** — "players on your radar", the best value from the
easiest-run teams. The strongest, most evocative term, and a clean one-word header. The caption stays descriptive so
the meaning is never in doubt. (The `analytics.target_by_fixtures` function and the `target_*` session keys are
**unchanged** — display label only.)

**2. Edge (adopt).** The `explain` output's **"Why"** heading → **"Edge"**, giving the coherent **Edge · Risk**
pairing (why a pick has an advantage, and what could go wrong). "Edge" is punchy, reads as *your* advantage, and
stays clear in context (a short bullet list of reasons underneath).

**3. Risk (keep + reconcile).** Already on-brand and clear. But it renders **inconsistently** today — `"Risk"`
(singular) in the build explanation vs `"Risks"` (plural) in the captain card. Standardise on **"Risk"** (matches the
Help copy and the Edge/Risk pairing).

**4. Captain (keep).** Already `Captain` / `Captain Pick` throughout — no change.

**5. Pick (defer — owner's call, 2026-08-12).** The obvious home for "MadBoots **Pick**" is the **"AI Tips"** sub-tab,
but that tab renders a **whole-week plan** (captain + lineup + a transfer + flags), so "Pick" would *mis-size* it (it
reads as a single recommendation). **AI Tips stays for now**; revisit if a genuinely single-recommendation surface
appears, or with a better-fitting name.

**6. Display-only — what this is *not*.** **No** analytics/engine change. **No** rename of any code identifier
(`render_ai_tips`, `target_by_fixtures`, the `target_*` session keys, the `elif view == "..."` branch strings that
are simultaneously logic — all kept). **No** nav-label churn (top-level tabs stay functional per ADR-105). The
mascot/brand-in-tools polish (UX A4) is a separate item.

---

### 🔀 Alternatives Considered

- **The full "MadBoots X" treatment on every label** (MadBoots Pick / MadBoots Edge / MadBoots Radar …). Rejected —
  gimmicky, and it hurts scannability. The principle says a *light* signature; one or two brand words that hang
  together do more than a prefix everywhere.
- **Rename "AI Tips" → "MadBoots Pick" now.** Deferred (owner) — it mis-sizes a whole-week plan as one pick, and
  "AI Tips" is honestly clear. Keep it until there's a right-sized surface or name.
- **Keep "Why" (don't adopt "Edge").** Considered — "Why" is already clean. Chosen against because "Edge" is *also*
  clear here **and** gives the coherent Edge/Risk pairing that carries the brand voice; the clarity bar is met.
- **Leave "Target by fixtures".** Rejected — "Radar" is the clearest win in the set: shorter, more evocative, and the
  descriptive caption keeps the meaning explicit.

---

### 🧭 Consequences

**Positive**
- **Reads more like MADBOOTS** — a small, coherent lexicon (Radar; Edge/Risk) instead of anonymous analytics wording.
- **Zero engine risk** — display strings only; `decision_xp`, the analytics, and every code identifier are unchanged.
- **Fixes a real inconsistency** — Risk/Risks reconciled to one word.
- **Incremental + reversible** — adopts what clearly earns it; "Pick" stays parked until it fits.

**Negative / risks (mitigations)**
- **A label appears in several places** — "Why"/"Risk" render in *two* paths (build explanation + captain card);
  "Target by fixtures" in the Fixtures subheader **and** Help. *Mitigation:* the planning map lists every surface;
  the sprint sweeps all of them, tests assert the new wording.
- **Muscle-memory nudge** for testers who knew "Why"/"Target". *Mitigation:* small, and the captions/tooltips keep
  the meaning obvious.
- **Brand-word creep** later. *Mitigation:* this ADR is the reference — new terms are measured against the *clean,
  not gimmicky* bar, and "Pick"'s deferral is the worked example.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (a small, gated sprint — Sprint 148): **`Why` → `Edge`** and **`Risks` → `Risk`** in the
  `explain` output + captain card (US-363); **`🎯 Target by fixtures` → `🎯 Radar`** on the Fixtures page + Help
  (US-364). Display-only; existing tests stay green (assertions updated to the new wording); docs (PROJECT_STATUS,
  Architecture, Backlog, memory).
- **Deferred by this ADR:** **"Pick"** for the recommendation (AI Tips stays until a right-sized surface/name).
- **Separate items (unchanged):** mascot/brand-in-tools (UX A4); per-GW xP display (A5); player-actions
  consolidation (A6). All in the 2026-08-12 intake (`docs/Backlog.md`).
