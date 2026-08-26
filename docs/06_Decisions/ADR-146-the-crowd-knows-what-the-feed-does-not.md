# Architectural Decision Record: The crowd knows what the feed does not

**Decision ID:** ADR-146
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 200, 2026-08-26). **1407 → 1415 tests, ruff clean.**
**Superseded By / Replaces:** Extends the crowd signals (ADR-057) into the Risk Monitor (ADR-130) and the
gameweek flags (ADR-023/070). No `decision_xp` change — this flags, it does not reprice.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on the live app:

> Watkins is currently looking at a team move to Saudi. There is no warning or pickup on that from AI tips or
> Health — **despite a lot of people transferring him out**.

The second half of that sentence is the whole ADR. **ADR-138 had already looked at this case and concluded
there was nothing to build**, on the grounds that FPL's feed says nothing about a Saudi transfer — his
`status` is `a`, his `news` is empty. That was true and it was the wrong conclusion, because it treated the
feed as the only thing the app knows.

**The app had the signal the entire time:**

```
Watkins · AVL · £8.0 · status 'a' · news '' · minutes 0
   transfers_in_event      7,583
   transfers_out_event   103,678      →  net −96,095
   crowd_flags           ['⭐ popular', '❄️ out']
```

`crowd_flags` was *already returning* ❄️ out. It renders in the Pool's Trends column and on the pitch — and
**neither the Risk Monitor nor the gameweek flags ever looked at it.** `squad_risk.py` contained no reference
to transfers at all; `gameweek_plan` built its flags purely from `status`, so a player FPL calls fit was
invisible no matter how hard the crowd was selling him.

### 🔬 The measurement that turned it into a feature

A raw exodus is not enough — the crowd dumps underperformers every week. Across the **199 players owned by
≥1% of managers**, the eight largest sell-offs split cleanly:

| player | net | our data says |
|---|---:|---|
| Pedro Porro | −227,771 | *"Lack of match fitness — 75%"* — **explained** |
| **Gyökeres** | −115,127 | status `a`, no news — **nothing** |
| **Konsa** | −106,963 | status `a`, no news — **nothing** |
| Gibbs-White | −96,288 | *"Knee injury — 75%"* — **explained** |
| **Watkins** | −96,095 | status `a`, no news — **nothing** |
| Van de Ven / Sarr | −92,570 / −86,245 | injury news — **explained** |

**Five explained, three not.** The signal is not the exodus — it is the **discrepancy**. And the three
unexplained ones are exactly the players a manager would want flagged, and precisely the ones the app was
silent about.

---

### ✅ Decision

**1. `crowd_exodus(player)` fires only when the sell-off is heavy _and_ our own fields cannot account for it.**
If `status` is anything but `a`, or `news` is non-empty, it returns `None` — that case is already surfaced,
and duplicating it would bury the three players nobody could explain under five who were already covered.

**2. Scale is `price_pressure` — net transfers per 1% of ownership** (ADR-092), so a template player is not
flagged merely for having big absolute numbers. **Threshold `EXODUS_PRESSURE = −8,000` is the measured p10**:
across those 199 players, pressure runs p10 −7,996 · median −969 · p90 +11,104. Same
calibrate-against-your-own-distribution idiom as ADR-144 and ADR-145.

**3. It reaches both surfaces the owner named**, at the layer they share:
- **`gameweek_plan` flags** → so `ask`, the CLI and the web AI-tips block all inherit it. Ordered **after**
  `status` in the `elif`, so if FPL says he is injured we say *that*, not *"the crowd is nervous"*. The
  inference is a fallback for when the feed is silent, never a replacement for what it tells us.
- **The Risk Monitor** → an `exodus` field and a `Crowd` driver. It does **not** enter the `attention` score
  — it is not a probability, and averaging it with one would be the units mistake ADR-143 made — but it
  **sorts to the top**, because it is the one signal the app cannot derive for itself.

**4. It never claims to know _what_ the news is.** The note says the crowd is acting on something we cannot
see, lists what was ruled out, and stops:

> *"96,095 managers sold Watkins this gameweek and nothing in the data explains it — no injury, no suspension,
> no news. The crowd may be reacting to something we can't see; worth a look before you keep him."*

Saying *"he may be moving to Saudi Arabia"* would be inventing a cause to sound confident. A test asserts the
note contains no such claim.

**5. `TRENDING_NET` was calibrated while here.** It carried a *"calibrate at GW1"* note since ADR-057. Net
transfers run p10 −35,221 · median −2,946 · p90 +46,808, so the placeholder 50,000 sits just outside each
tail — **right as guessed, and now recorded as measured** so nobody re-derives it.

### ⚠️ Risks

- **The crowd is often wrong.** It panics, it follows bad advice, it over-reacts to a single blank. This flags
  *that people are selling*, not *that they are right* — the copy says "worth a look", not "sell him".
- **Herding.** A flag that says "everyone is selling" may make people sell. Mitigated by naming it as a
  prompt to check rather than an instruction, and by requiring the discrepancy — we are not amplifying a
  sell-off we can already explain.
- **The threshold is one gameweek old.** Transfer volumes will grow through the season; p10 today may be
  ordinary in October. Named constant beside its measurement, same as ADR-144/145 — re-derive at GW4-6.

### 🧪 Definition of Done

1. **Tests: +8.** The Watkins case with its real numbers; an explained exodus (Pedro Porro, the largest of
   all) *not* flagged; per-1%-ownership scaling so a template player is not caught for being popular; buys
   are not an exodus; **the note asserts no cause it cannot know**; the threshold pinned as the measured p10;
   plus gameweek-flag tests that it reaches the plan and that a real `status` always wins.
2. **Manual smoke** — a squad holding Watkins through the Health view and the `ask` gameweek block.
3. **Docs** — this ADR, ADR-138 corrected, PROJECT_STATUS, the Feedback_Log row, a sprint retro.
