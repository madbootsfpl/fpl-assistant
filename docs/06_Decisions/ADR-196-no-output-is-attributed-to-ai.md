# Architectural Decision Record: No output is attributed to AI

**Decision ID:** ADR-196
**Date:** 2026-09-16
**Status:** ✅ **Accepted — built** (2026-09-16). **1797 → 1798 tests, ruff clean.**
**Superseded By / Replaces:** Completes [ADR-168](./ADR-168-retire-ask-and-the-promise-with-it.md)'s removal of AI claims, 20 days
late, on the two surfaces [ADR-184](./ADR-184-sweep-for-the-claim.md)'s sweep missed. Renames two
cards from [ADR-118](./ADR-118-player-dna-page.md). **No behaviour change** — only what the app claims produced it.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> **Owner:** *"Note that Player DNA has both AI Verdict & AI Insights which should be just Verdict and
> Insights OR MadBoots Verdict and MadBoots Insights."*

He is right, and it is worse than a naming preference. **ADR-168 removed every AI claim from the product**
because there is no model on the deployed app — Ollama is local-only and Ask is behind an admin key, so *no
tester has ever seen AI output*. The mantra was rewritten twice over it.

And yet the Player DNA page was rendering:

```
✦ AI Verdict        ← a headline label, on the app's most screenshot-shared card
✦ AI Insights
```

Both are produced by `explain.py` and `player_dna.py` — **plain rule-based Python**, identical on Cloud and on
a dev box. The app was crediting a model it does not have, on the two cards most likely to be shared.

#### ⚠️ ADR-184 swept for this and missed it

That ADR exists because a retired claim survived 14 days on six surfaces, and its lesson was: **a guard
against a claim must sweep for the claim, not check the places you thought of.** It then swept for *the
mantra* — the specific sentence — and these two labels are a different wording of the same claim. ⭐ **The
sweep inherited the shape of the thing that prompted it.**

---

### ✅ Decision

**1. `MADBOOTS Verdict` and `MADBOOTS Insights`**, not bare *Verdict*/*Insights*. Both are accurate — the
analytics do produce them — and neither card carried any branding, so this adds a brand moment to the two most
shareable surfaces rather than repeating one.

**2. A sweep for the claim, and deliberately a narrow one.** The rule is **`AI` followed by a Capitalised
word** — an attribution label. It flags exactly the two cards, and it does **not** flag Help's

> *"the answer is based on MADBOOTS' data, **not an AI guess**"* … *"**Local AI** — MADBOOTS can use a *local*
> Ollama model to narrate… The hosted app runs **data-only**."*

which is **true, useful, and the opposite of the problem.**

⭐ **A guard that would delete an honest explanation to satisfy a pattern is worse than the bug it is
chasing.** A blanket ban on the token would have forced exactly that — the same trap `_visible_strings` was
written to avoid, where flagging a docstring about history would push someone to delete the history.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the last two user-visible AI claims are gone, 20 days after the decision that removed
  them; the guard now sweeps for *attribution* rather than for one sentence; and the brand appears on the two
  cards people actually screenshot.
* **Negative Impact / Trade-offs:** four tests pinned the old strings and had to change — which is the rename
  working, and worth the noise. `ADR-118`'s composition order now reads with different names in its docstring.
* **Risks & Mitigations:**
  - **Risk:** the narrow rule misses a future phrasing (*"powered by machine learning"*, *"our model says"*).
    **Mitigation:** honestly, it would. The rule catches the **shape this product actually produced twice**;
    a wider one gets deleted the first time it flags something true. ⭐ *Prefer a guard that fires correctly
    over one that fires comprehensively and is then disabled.*
  - **Risk:** *"MADBOOTS Verdict"* reads as self-promotion. **Mitigation:** it is also the accurate
    attribution, which is the point — the alternative was crediting something that does not exist.

---

### 🛠 Implementation & Migration
* **Components Affected:** `web_streamlit/verdict_card.py`, `insights_card.py`, `player_dna_view.py`,
  `views/players.py`, `analytics/player_dna.py`, `analytics/explain.py` (comments), five test files
* **Action Items:**
  - [x] Rename both labels and every comment that names the cards
  - [x] `test_no_output_is_attributed_to_ai` — sweeps all user-visible copy for the attribution shape
  - [x] Mutation-test it: both labels restored, plus a **new** phrasing (*"AI Powered Verdict"*) it had never
        seen — all three caught
  - [x] Update the four tests that pinned the old strings

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A sweep written to catch one claim will have the shape of that claim.**

ADR-184's finding was correct and its remedy was too specific. It searched for the retired *mantra*, so a
retired *attribution* wearing different words walked straight past it — and sat on the product's most
shareable card for three more weeks, under a page the owner looks at constantly.

The generalisable form: **when you retire a claim, write down the claim, not the sentence.** *"The app must
not credit a model for output it computes"* would have caught both labels on day one. *"The string 'The AI
explains' must not appear"* could only ever catch itself.

---

### 🔗 References & Related Artifacts
- **The claim that was retired:** [ADR-168](./ADR-168-retire-ask-and-the-promise-with-it.md) — no model on Cloud
- **The sweep that missed it, and why:** [ADR-184](./ADR-184-sweep-for-the-claim.md)
- **The cards:** [ADR-118](./ADR-118-player-dna-page.md) (Sprint 169–171)
- **Found by:** the owner, reading his own Player DNA page
