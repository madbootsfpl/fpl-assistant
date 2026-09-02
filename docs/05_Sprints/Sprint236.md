# Sprint 236: Value above the fold (ADR-175)

**Dates:** 2026-09-02
**Status:** ✅ Complete — ADR-175. **1696 → 1702 tests, ruff clean.**

> **Owner:** *"Our golden page has a lot of real estate used up before we get to the value of the page."*

Ten blocks preceded the first useful thing. On a phone the entire first viewport was chrome.

---

### 🔧 What shipped — four changes, one pass

| | |
|---|---|
| **Cut the stale and the duplicated** | the page caption still said *"…chips · **health**"*, a name ADR-166 retired six days earlier, and explained the page to someone already on it. The **Squad** picker read *"RoboTS (yours)"* four lines above a banner reading *"YOUR TEAM · RoboTS"* — **with one squad there is now no picker at all** |
| **Horizon → `GW1 · GW1–3`** | on the pitch. US-374 had already defaulted these tools to 1 against the Lab's 5; offering **10** on an active squad offered a window nobody chose. Scoped: the Lab keeps its long range, DNA/Leagues keep 1–5 |
| **Backup / import → the sidebar** | but only once you have a team. ADR-113 put it on the page so a new user could find it — a real reason that expires the moment they have something to find |
| **One answer at a time** | `This week · Captain · Transfer · Chips` as a selector under the pitch. Top nav **5 → 4** |

---

### 💡 The lesson

> **A measurement about cost is not a decision about layout.**

This reverses ADR-171 §3, six days old. That ADR's finding was that the answer *could* render on the page —
**123 ms, against a supposed 4.4 s** — and that finding still stands. Answer-first was a judgement laid on
top of it, and the owner has now lived with it. Use beats argument, and nothing measured was contradicted.

It also supersedes **ADR-174**, written that morning, which declined to bring the Transfer tab in because
~10 widgets would *stack* onto a 41-block page. Behind a selector they exist only when chosen, so the
objection dissolves rather than being overruled. ADR-174's apply button survives inside *This week*.

**On churn, the owner's steer is recorded as a decision:** this page changed three times in six days, and for
a small engaged tester group, arriving at the right layout beats holding a settled one. That trade would not
hold for a public release.

---

### ⚠️ Two of my own guards failed, and both were right to

**I wrote the ADR saying the switcher folds into the banner, then did not do it.** The test caught the gap
between the record and the code — which is the *point* of writing the record first, and the first time this
week it has caught me rather than the codebase.

**A test asserted the backup panel had left the page while injecting no squad** — the exact state where it
should stay. It was testing the opposite of its own name. And the assertion was unscoped: `at.get("expander")`
spans the sidebar, so *"still on the page"* came back true for a panel that had correctly moved off it.
`at.main` is the scope that answers the question being asked.

---

### 🧭 The nav guard was wrong, and that is worth separating

Nineteen tests broke. One was **`test_navigation_copy`**, flagging that Home and Help point at
*"My Squad ▸ Transfer"*.

**That pointer is still true** — Transfer is on My Squad, one control lower. The guard read only the tool
switch, so its model of "a place you can be sent" was too narrow. It now reads **both** switches.

Four times this week that guard was right and the copy was stale. This time the copy was right and the guard
was stale. **A guard that has only ever been right is a guard nobody has audited** — the failure mode of a
tripwire is not that it stops firing, it is that it keeps firing at the wrong thing and gets believed.

Separately, **Help described the *structure*, not just the names** — *"top to bottom"*, *"at the bottom,
behind a button"* — so it went stale while every tab name in it stayed valid. A guard that checks names
cannot catch that.

---

### 🧪 Tests

**+6** (1696 → 1702), each mutation-checked: restoring the caption fails · putting 10 back on the pitch fails ·
keeping backup/import on the page always fails · dropping Transfer out of the selector fails.
