# ADR-270 — A control you can reach by accident is enabled

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"do it"*, on the last tester-facing gap
**Closes:** the open item flagged when the field was built (ADR-239)

---

## Context

**More ▸ Settings ▸ Server** lets anyone type an API address. It was flagged as a risk on the day it
shipped and has been carried as an open item ever since.

⚠️⚠️ **A tester handed an editable API address has a way to point the app at nothing** — and ⭐ *the only
bug report that follows is "the app stopped working"*, with nothing in it to suggest a field was ever
touched. The failure looks exactly like a server outage, an expired certificate, or a bad build.

## Decision

**The field is compiled out unless a build asks for it.** `kServerFieldEnabled` is
`bool.fromEnvironment('MADBOOTS_DEV')`; developer builds pass `--dart-define=MADBOOTS_DEV=true`.

⭐⭐ **Compile-time, so the control is absent from the build rather than hidden inside it** — *a control
you can reach by accident is a control that is enabled.* A `Visibility` wrapper or a debug check would
leave the widget in the tree and the door merely closed.

⚠️ **It is not removed**, because it still has a job: pointing a handset at a laptop on the LAN, where the
address is a DHCP lease that moves. ⭐ *The field was never wrong — the audience was.*

## Consequences

📌 **Both runbooks had to change**, and both had gone false the moment this shipped: each told the reader
*"the Settings field still overrides it"*. ⭐ *A runbook that describes a capability the build no longer
has is worse than one that omits it* — the reader looks for the field, does not find it, and concludes
something is broken.

⚠️ **And a second stale paragraph turned up next door.** Settings' *"On the web"* note still named the
fixture ticker, Team DNA and Trending as things only the web carried — **all three are in this app**. The
identical claim was removed from the More tab in ADR-269; ⭐ *positioning copy outlives the positioning it
describes*, and this is the second copy of the same sentence to go in two days.

## Verification

* **3 Dart tests** — the field absent from a default build, the rest of Settings intact, and the flag
  itself a compile-time constant.
* ⭐ Asserted **by content, not by counting fields**: Settings legitimately keeps one input (the FPL
  manager id), so the test looks for an input *holding an address*. ⚠️ *Hiding a label is not removing a
  control.*
* **3/3 mutations killed**, including the subtle one — hiding only the **heading** while leaving the row.
* ✅ The flag proved to work **in both directions**: a probe test fails without `MADBOOTS_DEV` and passes
  with it, so the escape hatch is known to exist rather than assumed.
* 2,553 Python · 211 Dart.
