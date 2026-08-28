# Sprint 224: The player panel reruns on its own (ADR-165)

**Dates:** 2026-08-28
**Status:** ⚠️ Built; **benefit unverified** — needs a Cloud check. 1568 → 1569 tests, ruff clean.

> **Owner:** *"works, it's a little laggy but let's see what the feedback is"* → then *"do the st.fragment one"*.

---

### 🔧 What shipped

Streamlit reruns the **whole page script** on every interaction, so tapping a shirt re-executed the xP strip,
the pitch, the panel, Boot Battle and the Player DNA card — to move one selection. The pitch and player panel
are now a **fragment**, which reruns only itself.

**The boundary is the actual decision.** Everything inside reads or selects; the two things that *mutate* the
squad — Make captain, Substitute — call `st.rerun()`, which defaults to `scope="app"` and reruns the page.
That is required, not incidental: the xP strip sits above the fragment and must change when the captain does.
A test pins that `scope="fragment"` never appears.

---

### ⚠️ Why there is no number

`AppTest` does not simulate fragment-scoped reruns. A five-line probe proved it — a counter *outside* a
fragment incremented on every interaction with a widget *inside* it:

```
after load        : outer=1 inner=1
after a selection : outer=2 inner=2      ← a real fragment rerun would leave outer at 1
```

So the benchmark I ran (64 ms with the fragment, 61 ms without) **measured nothing**. It is blind to the
feature by construction, and I nearly reported it as evidence the change didn't work.

What ships is therefore honest but unproven: architecturally right, low-risk, tests green — and only the
owner's phone can say whether it feels different.

---

### 💡 The lesson

> **A harness that cannot observe the thing you changed will report success.**

The benchmark ran cleanly and produced plausible numbers to two significant figures. Nothing in the output
hinted that it was meaningless; I only checked because the two numbers were suspiciously *identical* rather
than suspiciously wrong.

Same rule as the toothless Home guard and the tap test that faked a fresh click, now stated generally:
**before trusting a measurement, prove the harness can see a difference** — break the thing on purpose and
check the number moves. If it doesn't, the measurement was never evidence.

### 🧪 Tests

**+1**, 207 web tests still green. The fragment exists, the mutating controls are inside it, and no rerun is
fragment-scoped — the edit that would silently leave the strip showing the old captain's numbers.
