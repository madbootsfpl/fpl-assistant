# Lessons Learned

**Sprint:** Sprint 145 — P0 quick-wins (tester feedback, 2026-08-12)

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Ship the first P0 items from the 2026-08-12 intake: **transfer filters** (team + price), **captain-persists-on-load**,
and — gated separately because it changes the core metric — the **cold-start data floor** (new/promoted players at 0).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Root-cause on real data before "fixing".** Two of the three items turned out different from the surface report
  once grounded — the captain "bug" was a UX gap, and the data "we're too low" was mostly FFH being high.
- **Gate what changes the metric.** The cold-start floor changes `decision_xp` (ADR-041) → an ADR, not a quiet build.

### New Skills Acquired

- **The captain "didn't persist" was set-after-save, not a store bug.** `cloud_store` already stores the whole squad
  dict (incl `captain_id`); the gap was there's no *sync* after an edit. The fix — **auto-sync a cloud-linked squad**
  (mirror edits to the cloud once Saved/Loaded under a handle) — is a small down-payment on the bigger persistence
  review, and directly closes the complaint.
- **Reframe an accuracy complaint with the data, don't chase the competitor.** The tester saw "O'Shea 1.6 vs FFH 4.7"
  and inferred we were too low. On the real data, **FPL's own `ep_next` for O'Shea is 1.0 — we're *higher* than FPL**,
  so FFH is the outlier. The *genuine* defect was narrow: **69 no-history players at exactly 0** (preseason `ppg` 0 →
  rate 0). Fixing *that* (with FPL's own `ep_next`) is honest; chasing FFH's paid-data numbers would not be.
- **Floor with a number you already hold, sourced honestly.** `ep_next` was on every row, unused. Using it as a
  *floor* on the last rate tier (and labelling it `rate_source="ep_next"`) fixes the credibility problem without new
  data, without touching established players, and stays truthful in grounding.
- **`ep_next` already prices minutes** — so don't re-apply the xMins weight to it (double-discount). A one-line guard.

---

# What Went Well ✅

- **Grounding paid off twice** — the captain "bug" and the data "gap" were both reframed by reading the real data,
  producing smaller, more honest fixes than the surface reports implied.
- **The metric change was well-targeted** — only **one** invariance test broke (exactly as ADR-104 predicted);
  established players stayed byte-identical.
- **Auto-sync** turns a cloud-linked squad genuinely live across devices — a real robustness win.
- 962 → 964 tests; the transfer filters +1 (959→960); ruff + CI green throughout.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Captain "doesn't persist" | no *sync* after an edit (set-after-save) — the store round-trips fine | Auto-sync a cloud-linked squad on every edit (best-effort) |
| "We're too low vs FFH" | FFH is bullish on players *with* history; the real defect was the 0s | Reframe with FPL's own `ep_next`; fix only the no-history 0s |
| Changing the one-xP metric | the cold-start floor alters `decision_xp` for a cohort | Gate it (ADR-104); update the one invariance test it breaks |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Debug the report, then the data | Both "bugs" were narrower/different once grounded — read the data first |
| Persistence sync | The store round-tripping ≠ the app syncing; auto-sync a linked squad closes the gap |
| Honest floors | Floor a cold-start with a number you already have (FPL `ep_next`), sourced transparently |
| Metric changes | A change to `decision_xp` gets an ADR + the invariance tests updated, not a silent edit |

---

# Development Lessons 💻

- Reproduce a data complaint on the real rows before designing a fix — the fix often shrinks (or moves).
- When a competitor's number differs, check a *neutral* third source (FPL's own `ep_next`) before assuming you're wrong.
- A change to the core metric is an ADR + a test update, by definition.

---

# AI Collaboration Lessons 🤖

- The cold-start floor keeps the analytics **honest**: it uses FPL's own published estimate (not an invented number),
  labels it (`rate_source="ep_next"`) so grounding (ADR-037) tells the truth, and is *targeted* so the documented
  baseline/fallback tiers are unchanged. The auto-sync is the sanctioned squad-save write (ADR-094), done on a linked
  edit — the opt-in server-write invariant holds (no handle → no write).

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-104 — a cold-start xP floor from FPL's `ep_next`.** In `player_xp`'s last rate tier,
`rate = max(points_per_game, ep_next)` (a new `rate_source="ep_next"`, not minutes-re-weighted) so no-history players
aren't projected at 0; the baseline/fallback tiers (ADR-028/040) are untouched. US-356 (transfer team+price filters)
and US-357 (auto-sync a cloud-linked squad) were no-ADR quick fixes.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (browser smoke):** Transfer → team/price narrow the list; save+captain on one device → load on another →
  the captain's there (+ the "🔄 Auto-syncing" line); new/promoted players now show a small non-zero xP; established
  players unchanged.
- **Still on the P1 list (2026-08-12 intake, `docs/Backlog.md`):** the **IA restructure** (A1/A2 — pull Build out,
  My Squad as its own tab); the **persistence + Google-auth** review (C2/C3/C4 — mobile session-wipe, `st.login`);
  per-GW xP display (A5); the player-actions consolidation (A6); the MADBOOTS vocabulary (E).
- **GW1 (2026-08-21):** the dormant-weight calibration remains the data-gated thread (ADR-101).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep reproducing tester data-complaints on the real rows first — it reframes the fix honestly and keeps it small.

---

# Key Commands Learned

```text
python -m pytest tests/test_xp.py tests/test_cloud_store.py -q   # the cold-start floor + the captain round-trip
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Cold-start floor | `max(ppg, ep_next)` for a no-history player — a sane, FPL-sourced floor, not 0 |
| `rate_source="ep_next"` | The rate came from FPL's expected-points-next-GW (the player has no history yet) |
| Auto-sync (cloud-linked) | Mirror every edit to the cloud once a squad is Saved/Loaded under a handle |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-104-cold-start-xp-floor.md` | The floor decision + the FFH reframe |
| `src/analytics/xp.py` (`player_xp` rate tiers) | Where the floor lives (last tier only) |
| `src/web_streamlit/squads.py` (`_autosync`) | The cloud-linked auto-sync |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-356 Transfer filters (team + max-price on the bring-in list)
- US-357 Captain persists on load — auto-sync a cloud-linked squad
- ADR-104 The cold-start xP floor (the gate)
- US-358 Build the cold-start floor (`max(ppg, ep_next)` + `rate_source="ep_next"`)

**Stories Carried Forward:**

- None. (The P1 items — IA restructure, persistence+auth, per-GW display, player-actions, vocabulary — remain in the
  2026-08-12 intake.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
