# ADR-279 — The app asks whose team this is

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner, after installing on a tablet — *"the emulator, the iPhone app & the tablet app are
all using the same FPL ID, mine, that will need to be addressed too I suspect. Also the madboots icon on
the tablet is the default logo"*

---

## 1. Every install opened on one person's squad

`const int kDefaultManagerId = 2885974` — the author's team, compiled into the app.

⚠️⚠️ **And it was never saved.** The app persisted drafts, seen signals, the feedback address and the
server URL — and not the one value that says *whose team this is*. So a tester would correct it in
Settings, close the app, reopen it, and be looking at a stranger's team again.

⭐ **The most personal setting in the app was the only one that did not stick.**

**Now:** `ManagerStore` persists it, and a first run has **no default at all** — ⭐ *a default here is a
guess about whose team you are looking at, and the app cannot tell a guess from an answer once it has
written one down.* `WelcomeView` asks.

📌 **Not an account** (ADR-259 is still open). An FPL manager id is public, needs no password, and is the
only thing the API takes — ⭐ *asking for the minimum that works beats asking for the maximum that might
be useful later.* It says so on the screen, along with *"nothing here can change your real team"*.

## 2. ⚠️⚠️ The icon check could not have caught the icon being wrong

The tablet showed Flutter's blue logo. The icons had been "generated" by a shell loop that silently did
nothing — and the verification was *"is xxxhdpi 192 pixels?"*, which **Flutter's default already is.**

⭐⭐ **A check that the right answer and the wrong answer both satisfy is not a check.** The same shape as
the `greaterThan(0)` that accepted a fabricated `99` (ADR-267), one day apart.

Regenerated, verified by **bytes changing** rather than by dimensions, and guarded: each density must be
a resize of the same 1024px master iOS uses, so a new logo cannot land on one platform and not the other.

## 3. Two bugs the first shell test found

**Nothing had ever pumped `MyTeamScreen`** — the screen that owns first run, the manager id and every
draft could only talk to a real network, so no test could reach it. It now takes an optional client.

The first test to run it immediately failed on a **pre-existing** assertion:
`setState(() => _team = _load(id))` **returns** the Future it assigns, and Flutter asserts on that. ⚠️ *It
only fires in debug, on a screen no test had ever pumped* — so it was invisible on a release build in a
pocket.

## ⚠️ And two mutations survived, both for the same reason

**Two guards that hid each other.** `save` and `load` both reject a junk manager id, so a test going
through `load()` passes whichever one is deleted. ⭐ *Two defences that hide each other are one defence
and one thing nobody will notice breaking.* The test now reads the raw preference, and a second test
keeps `load`'s guard honest for a preference file edited by something that never went through `save`.

**And the Settings persistence had no test at all** — the exact path a tester walks. Closed by the shell
test above.

## Verification

* **13 Dart tests**: the store, the welcome screen, the shell's Settings round trip, and a sweep proving
  **no manager id is baked into `lib/`** — ⭐ counting only code, and the example in the hint was changed
  to an obviously illustrative number so the guard needs no exception: *an example that is also a working
  value is one somebody will submit.*
* **7 Python tests** on the Android icon, comparing **content** against the master.
* **4/4 mutations killed**, two only after the tests were rewritten to observe what they claimed to.
* 2,587 Python · 267 Dart.
