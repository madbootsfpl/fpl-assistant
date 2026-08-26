# Sprint 205: One Signals page, ordered by what the source knows (ADR-150)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-150. 1431 → 1435 tests, ruff clean.

> **Owner:** *"'Talked about' and News — should that be consolidated?"*

---

### 🔍 Counting them properly changed the answer

It was logged as a question, not a task, because the two are different in kind: News is FPL's official `news`
field — a fact that drives `status` and therefore every xP — while *Talked about* is a Reddit mention count.
Merging naively risks a rumour sitting beside a confirmed injury at equal weight.

**Reading both pages found four lenses, not two:**

| page | held |
|---|---|
| News | official FPL news · media headlines |
| Trending | four leaderboards · Reddit top discussions · Reddit mention counts |

So **News was already a signals page**, and the *Reddit halves were the ones on the wrong page* — sitting
beside ownership percentages. ADR-146 had then added a fifth signal with **no browse surface at all**: the
unexplained exodus warned you about players you already owned, and could not answer the question you ask
before buying.

The real axis was never *official vs unofficial*:

> **Trending: what the crowd is *doing*, in numbers. Signals: what is being *said*, in words.**

Once named, it sorted all five without a judgement call.

### 🔧 What shipped

📡 **Signals** (a rename of News) holds all four lenses, **descending by evidentiary strength**, each labelled
with what it is worth: official news (a fact) → an unexplained exodus (a fact about *other managers*, not the
player) → headlines (named outlets) → chatter (a count, never sentiment). That ordering **is** the answer to
the merge risk; a merged page has to label its sources or the merge becomes the misinformation. Trending keeps
the leaderboards and points at where the chatter went. Help updated in the same commit.

### 🐛 The find: a threshold carries its population with it

Giving the exodus a browse surface exposed a flaw in reusing ADR-146's number. `EXODUS_PRESSURE` is net
transfers **per 1% owned** — right for comparing a template player with a niche one, but it divides by a small
number, so a 0.1%-owned player shedding a few thousand reads as a stampede.

On a per-squad warning that never mattered: you only ever see players you own. On a browse list:

```
no floor    17 players   (incl. Martinelli, 0.2% owned, −3,369 net)
≥1% owned    8 players   (Gyökeres, Konsa, Watkins, Eze, Hincapie, Welbeck, Dorgu, Zubimendi)
```

`EXODUS_OWNERSHIP_FLOOR = 1.0` is not a taste — **it is the population ADR-146 measured the p10 against.**

---

### 💡 The lesson

> **"Should A and B be merged?" is best answered by counting the actual set and naming the axis.**

The question named two things. There were four, plus a fifth with nowhere to live, and the useful move was not
deciding *whether* to merge but working out **what the sorting principle was**. *Doing vs saying* did the whole
job; *official vs unofficial* would have left the leaderboards and the chatter still tangled.

And the sharper one, which generalises past this page: **a threshold carries its population with it.**
ADR-146's number was correct and became noise the instant it met a different set of players. Any constant
derived from a measurement should record the distribution it came from — this codebase now has four such
constants, all measured at GW1, all due a re-check at GW4-6.

### 🧪 Tests

**+4, several retargeted.** The section order and the source labels are pinned, so a future edit cannot
quietly promote chatter above an injury; Trending is asserted to be leaderboards-only *and* to point at where
the chatter went; the exodus floor is pinned with its reasoning in the docstring. The tests that drove the
Reddit sections now drive Signals.
