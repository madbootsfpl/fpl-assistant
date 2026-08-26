# Architectural Decision Record: One Signals page, ordered by what the source actually knows

**Decision ID:** ADR-150
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 205, 2026-08-26). **1431 → 1435 tests, ruff clean.**
**Superseded By / Replaces:** Merges the News page (ADR-058 + ADR-093 headlines) with Trending's Reddit tabs
(ADR-059) and gives ADR-146's crowd exodus its first browse surface. Trending keeps its leaderboards.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner asked it as a question: *"'Talked about' and News — should that be consolidated?"*

Logged as a question rather than a task, because they are **different in kind**: News is FPL's official `news`
field (a fact that drives `status`, and therefore every xP), while *Talked about* is a Reddit mention count
(chatter). Merging them naively risks presenting a rumour beside a confirmed injury at equal weight.

**Reading both pages made the case stronger than the question implied.** There were not two signal lenses —
there were **four**, split across two pages with no relationship between the halves:

| page | held |
|---|---|
| **News** | official FPL news · media headlines (Fantasy Football Scout, BBC) |
| **Trending** | four ownership/transfer/form leaderboards · Reddit top discussions · Reddit mention counts |

So *News was already a signals page* — official plus media — and the Reddit halves were the ones on the wrong
page, sitting beside ownership percentages. And ADR-146 had just added a fifth signal, the unexplained
transfer exodus, with **no browse surface at all**: it warned you about players you already owned, and could
not answer the question you ask *before* buying.

The split that actually exists is not news-vs-chatter. It is:

> **Trending: what the crowd is *doing*, in numbers. Signals: what is being *said*, in words.**

---

### ✅ Decision

**1. `7_News.py` becomes `7_Signals.py` — 📡 Signals** — holding all four lenses. Trending keeps the four
leaderboards and loses the Reddit tabs. No other page moves, so nothing else renumbers.

**2. The page descends by evidentiary strength, and that ordering _is_ the answer to the risk.** Each section
says what its source is worth:

| | source | what it is |
|---|---|---|
| 1 | **Official FPL news** | a **fact**; the only source here that moves xP |
| 2 | **An exodus we can't explain** | our inference — *not a fact about the player*, a fact about what other managers are doing |
| 3 | **Headlines** | reported by named outlets |
| 4 | **Community chatter** | a **mention count** — never sentiment, never a prediction |

A merged page has to label its sources, or the merge itself becomes the misinformation. A test pins the order
and the labels.

**3. The exodus list gets an ownership floor — and finding out why is the sharpest thing in this ADR.**
`EXODUS_PRESSURE` is net transfers **per 1% owned**, which is the right scale for comparing a template player
with a niche one. But it divides by a small number: a 0.1%-owned player shedding a few thousand reads as a
stampede. On ADR-146's per-squad warning that never mattered — you only ever see players you own. On a
**browse** list it did:

```
no floor      17 players   (incl. Martinelli, 0.2% owned, −3,369 net)
≥1% owned      8 players   (Gyökeres, Konsa, Watkins, Eze, Hincapie, Welbeck, Dorgu, Zubimendi)
```

`EXODUS_OWNERSHIP_FLOOR = 1.0` is **not a taste — it is the population the p10 threshold was measured on**
(ADR-146 calibrated against players owned by ≥1%). *Applying a threshold to a different distribution than the
one it was calibrated against is how a good number turns into noise.*

**4. Help is updated in the same commit**, because a navigation guide describing a page that no longer exists
is worse than no guide.

### ⚠️ Risks

- **`/News` becomes `/Signals`.** Streamlit derives the URL from the filename, so any bookmark breaks. Judged
  acceptable in a private beta; noted rather than mitigated.
- **Four sections is a long page.** Each is collapsible or button-gated, and the two Reddit ones fetch nothing
  until asked — the page costs no more to open than News did.

### 🧪 Definition of Done

1. **Tests: +4, several retargeted.** The section order and the labels are pinned; Trending is asserted to be
   leaderboards-only *and* to point at where the chatter went; the exodus floor is pinned with the reasoning
   in the docstring. The tests that drove the Reddit sections now drive Signals.
2. **Manual smoke** — both pages render; Signals shows four ordered sections, Trending four leaderboard tabs.
3. **Docs** — this ADR, the Roadmap entry, the Feedback_Log question answered, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**The owner asked whether two things should be merged. The useful answer came from counting them properly —
there were four, and one of them was on the wrong page for a reason nobody had noticed.** "Should A and B be
consolidated?" is worth answering as "what is the actual set, and what is the axis?" The axis here was not
*official vs unofficial*; it was **doing vs saying**, and once named it sorted all five signals without a
judgement call.

Second: **a threshold carries its population with it.** ADR-146's number was correct and became noise the
moment it met a different set of players. Any constant derived from a measurement should record which
distribution it came from — and this codebase now has four such constants, all from GW1, all due a re-check
at GW4-6.
