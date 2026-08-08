# Sprint 111: Ask tab polish — readable rules, reliable scroll, an explained "worth"

**Dates:** 2026-08-12 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (Ask presentation + explainability — no analytics change)
**Carried Over:** none

> **Direction (tester feedback — three Ask-tab items):**
> 1. *Rules answers are a dense paragraph — a multi-item fact (chips) should read as **bullets**.*
> 2. *Clicking an **example question** doesn't auto-scroll to the answer (typing your own does).*
> 3. *"is X worth the money?" should explain **why** — like the captain/transfer answers do.*

---

### 🔎 Verified at planning (on real data)

- **Item 1 — a list fact renders as one long bullet.** `render_rules` prints `• <fact>` per matched fact; the
  **chips** fact is a single string listing four chips, so it's one dense bullet. The `fact` string is also the
  **verifier's** source of truth + the LLM's input, so reformatting it with embedded bullet lines (same tokens)
  improves the display **and** keeps grounding intact.
- **Item 2 — the scroll nudge doesn't re-fire.** The US-275 nudge is a **static** `st.iframe` string; Streamlit
  re-renders a component only when its inputs change, so on a later turn the identical iframe's `setTimeout`
  scroll **doesn't run again**. Typing uses `st.chat_input` (native focus/scroll to the bottom), which is why
  only the **example-button** path fails. The fix: make the nudge **unique per turn** (embed the turn count) so
  it re-renders + re-runs each time.
- **Item 3 — `worth` gives facts but no "why".** `_decide_worth` computes value (xP/£m), the rank among
  position peers, the median, and a tiered verdict — but no `detail`, so without Ollama the answer is just the
  raw **Facts:** block. The target row carries everything a grounded Why needs (`penalties_order`,
  `freekicks_order`/`corners_order`, `selected_by`, `form`, `price`) — e.g. Haaland: pens=1, 74.6% owned — so
  an `explain_worth` can build a ✓ Why / ⚠ Risk / Confidence like the rest of the explainability family
  (ADR-089).

---

### 🎯 Sprint Goal

**Objective:** the Ask tab reads well and explains itself — a multi-item rules answer is **bulleted**, clicking
an example **scrolls to the answer**, and *"is X worth it?"* shows a grounded **Why · Risk · Confidence** (not
just numbers). Presentation + explainability only; the analytics/grounding untouched, every number still ✓.

#### Success Criteria
- [ ] **US-283 (readable rules + reliable scroll)** — (a) the multi-item rules facts (chips, scoring, clean
      sheets, leagues …) render as **bullets** (a lead line + `• item` lines + any trailing note), in the web +
      CLI, with the grounding still verifying (the fact keeps the same numbers/names); (b) the example-question
      **auto-scroll** fires every time — the nudge is made **unique per turn** so Streamlit re-runs it.
- [ ] **US-284 (an explained "worth")** — `explain_worth(...)` builds a grounded **Confidence · Why (✓) · Risk
      (⚠)** for a value verdict (✓ top-tier value / strong xP over the horizon / on penalties / set-pieces /
      template; ⚠ premium price / below-median value / mid-pack rank / big differential), computed **from the
      data** (never the LLM). `_decide_worth` renders it as the `detail` (so it explains **without** Ollama) and
      puts confidence/why/risk in `facts` so a narrated number **verifies (✓)**; closed by the shared
      **Model note**.
- [ ] **No drift** — display/explainability only; `decision_xp`/`match_rules`/the analytics unchanged; existing
      **726** stay green (+ new rules-format / scroll / worth-explain tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (extends **ADR-085** (rules display),
      **ADR-052** (Ask scroll) and **ADR-089** (worth explainability) — noted; no new ADR).

---

### 🧭 Design sketch

**US-283a — bulleted rules.** Author the **multi-item** facts with embedded bullet lines (a lead + `• item`
lines + a trailing note), e.g. *"Chips (one use per half; a fresh set unlocks ~GW20): • Wildcard — … • Free
Hit — … • Bench Boost — … • Triple Captain — …"*. `render_rules` prints a multi-line fact **verbatim**
(indented) and single-line facts as `• fact`. `match_rules` is unchanged (still `(topic, fact)`); the facts
dict + verifier see the same tokens. Bulletise the clearly-enumerable topics (chips · scoring · clean sheets ·
leagues, plus bonus/DefCon where it reads as a list); leave single-concept facts as one bullet.

**US-283b — reliable scroll.** In `4_Ask.py`, make the scroll nudge's script **unique per turn** (embed
`len(history)` as a no-op token/var) so Streamlit re-renders it and the `setTimeout(scrollTo bottom)` runs on
every answer — including the example-button path. (A test asserts the emitted iframe src carries the turn
count.)

**US-284 — explained worth.** New `analytics/explain.py::explain_worth(target, *, value, median, rank, n_peers,
xp, horizon, row)` → `Explanation` (reasons/risks + a `worth_confidence` from the value-vs-median ratio, the
rank percentile and the horizon xP). `_decide_worth` builds it, sets `detail = render_explanation(ex) + MODEL_
NOTE` above the headline, and adds confidence/why/risk to `facts`. Same pattern as captain/transfer (ADR-089),
so the web Ask + CLI inherit it; the verdict/verifier are unchanged.

**Deferred:** switching rules answers to full web **markdown** (mono bullets read well + keep parity with the
other answers); a web-native worth card.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-283 | **Readable rules + reliable scroll** — bullet the multi-item rules facts; make the example-click auto-scroll fire every turn. | High | ⬜ To do | ~½ session |
| US-284 | **An explained "worth"** — a grounded Why · Risk · Confidence for "is X worth it?" (+ Model note), verified. | High | ⬜ To do | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — a bulleted rules fact renders as a lead + `•` item lines (chips shows four items on their
   own lines) and the `rules` answer still verifies ✓; the Ask scroll nudge's content differs between turns
   (so it re-fires); `explain_worth` returns grounded ✓/⚠ + a bounded confidence for a good-value and a
   poor-value player; the `worth` answer's `detail` carries Confidence · Why · Risk + the Model note and its
   facts include them (narration verifies). Existing **726** stay green. No `.save(` / no analytics change.
2. **Manual smoke** — `ask "how does bench boost work?"` lists the chips as bullets; on the web, clicking an
   example scrolls to the answer; `ask "is Haaland worth the money?"` explains **why** (Confidence · Why ·
   Risk) even without Ollama.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log.

---

### 📝 Session Progress Log

**US-283 — readable rules + reliable scroll.** ✅ Done.
- **Bulleted rules (item 1):** the four clearly-enumerable facts — **chips · scoring · clean sheets · leagues**
  — are now authored with embedded bullet lines (a lead + `• item` lines + a trailing note). `render_rules`
  prints a multi-line fact **verbatim** and a single-concept fact as one `• bullet`, with a blank line between
  facts. The `fact` keeps the same numbers/names, so `match_rules` + the verifier are unchanged and the answer
  still verifies ✓. *"how does bench boost work?"* now lists the four chips one-per-line.
- **Reliable scroll (item 2):** found the cause — the US-275 nudge was a **static** `st.iframe`, and Streamlit
  only re-runs a component when its inputs change, so on a later turn the identical scroll script didn't re-run
  (typing worked only because `st.chat_input` scrolls natively). The nudge now embeds a **`/*turn N*/`** token
  (`len(history)`), so it re-renders and the `scrollTo(bottom)` runs on **every** answer — including the
  example-button path.
- **Tests (+2):** a `render_rules` test (chips → four `•` item lines; a single fact → one bullet); an AppTest
  that the scroll nudge's `srcdoc` differs between turns (`/*turn 1*/` → `/*turn 2*/`). **728** green, ruff
  clean.
- **Manual smoke:** the bench-boost answer reads as bullets; two Ask turns emit distinct scroll scripts.

_(US-284 next — "start US-284".)_

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
