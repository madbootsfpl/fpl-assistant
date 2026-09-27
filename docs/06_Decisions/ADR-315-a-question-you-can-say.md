# ADR-315 — A question you can say

**Date:** 2026-09-27
**Status:** ✅ **Built.** ADR-309's item 1, and the only one of its seven that needed no AI decision.
**From:** the owner — *"Can we add a microphone to speak a question into Ask?"*

---

## The decision

**The platform's own recogniser, on the device** — iOS Speech, Android SpeechRecognizer, the Web Speech API
in a browser. No Whisper, no hosted transcriber, no server, no key to manage. ⭐ *A hosted transcriber would
have been the expensive way to do the cheapest item on the list.*

## 🔴 The real work was never the microphone

ADR-309 said so and it was right: the plugin is an afternoon. **The work is that a recogniser has never
heard of Semenyo, Ndiaye or Cunha**, and returns the nearest thing in its own vocabulary — *"semenio"*,
*"n diaye"*, *"koonya"*. The question that reaches the engine names a player who does not exist, and
ADR-308's comparison lens then cannot place him.

### ⚠️⚠️⚠️ A similarity threshold cannot do this, and measuring is what said so

Of **647** web names, **87 pairs are already ≥0.80 similar to each other**:

```
0.95  Fernandes ↔ B.Fernandes        0.94  Fletcher ↔ J.Fletcher
0.94  Richards  ↔ O.Richards         0.92  Timber   ↔ J.Timber
0.92  McAteer   ↔ McAtee     ← two different players
```

⭐⭐ **Any cutoff loose enough to catch a mangled name sits inside the range where real players are
confusable.** A threshold was the obvious design and the measurement killed it.

### ⭐⭐⭐ So the rule is a threshold **and a margin**

The best candidate must clear `MIN_RATIO`, *and* beat the runner-up by `MIN_MARGIN`. Measured against
sixteen realistic manglings and fifteen ordinary question words:

| | |
|---|---|
| noise words peak at | **0.71** (*"better"* → Zetterer) — every one rejected |
| clean manglings cluster at | **≥0.86**, margins **≥0.16** — every one accepted |
| 🔴 the dangerous case | *"sala"* → **Salia at 0.89** — a **wrong** player with a high ratio, rejected **only** by its 0.09 margin |

At **0.85 / 0.15**: **7 of 7 accepted correctly, 0 wrong, 7 dropped.** ⭐ That is the right direction to be
wrong in (ADR-154) — *a dropped name costs a question; a wrong one answers about somebody else.* And when
it does drop one, ADR-308's refusal already says so in place rather than guessing.

⚠️ **Deliberately not folded into `find_mentions`.** That same index feeds the buzz counter over thousands
of Reddit sentences, where a fuzzy pass would credit players to ordinary words at scale. ⭐ *Fuzziness is a
property of how this text arrived, not of the index* — so exact matching runs first and unchanged, and only
the leftovers are guessed at.

## The control

⭐ **Tap to talk, tap to stop** — not press-and-hold: a question takes seconds to say and a held finger
covers the field it is filling. ⚠️ *A control that hides its own output is a control people use once.*

- **Partial results on**, so the field fills as you speak — ⭐ *a name coming out wrong is visible before
  the question is sent, rather than after the answer is about somebody else.*
- **Orange while listening**, not purple: purple is this app's ordinary *"yours"*, and listening is not
  ordinary. ⚠️⚠️ *A microphone that is on and does not look on is the one thing a person will not forgive.*
- **Hidden entirely where there is no recogniser**, not shown disabled — ⭐ *a control that cannot work is
  worse than no control: it invites a tap and answers with nothing.*
- **Stopped on dispose.** ⚠️ A microphone left listening after the screen is gone is the failure nobody
  reports and everybody minds.

## 🔴 The privacy decision ADR-309 flagged

It warned that *a plugin default is not a decision*. iOS will otherwise send audio to Apple for
recognition, so the listen options ask for **`onDevice: true`** — a person's voice stays on their phone —
and degrade rather than fail where the platform cannot honour it. ⚠️ `debugLogging` is off for the same
reason: the plugin logs the partial transcript, and *a person's words are not debug output.*

⭐ The permission strings say what is recorded, what it becomes, and that it stops when you stop talking —
*a vague reason is a denied permission.* Asked at the first tap, never at launch: **a permission asked
before it is needed is a permission denied.**

## Consequences

- ⭐ **One new dependency** (`speech_to_text`), the app's fifth, and it earns itself the way ADR-309 said
  it would: on-device, free, no server.
- 📌 Android also needed a `<queries>` entry for `RecognitionService` — without it the plugin reports
  *"speech not available"* on a phone that has one.
- 📌 **ADR-309's items 2-4 are still open** (surface the briefing, plumb `converse()`'s follow-ups, and the
  rest of name-resolution hardening), and items 5-7 still wait on the inference-host decision.

**2900 Python · 466 Dart.**
