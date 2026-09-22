# ADR-239 — A phone's localhost is the phone

**Date:** 2026-09-22
**Status:** Accepted
**Opens:** Phase 4's device path — the app on real hardware, before any hosting decision
**Builds on:** ADR-219 (one contract, two transports), ADR-238 (Settings became a screen)

---

## Context

Feature work stopped, at the owner's call: *"I agree that we should hold on the feature adds until we get
the app up and running."*

⚠️ **Everything from ADR-228 to ADR-238 runs on one Mac and nowhere else.** The competitor-review pass
exists to get ahead of tester feedback, and no tester can open any of it. That is the gate, not the polish.

The plan the owner set is staged deliberately: **his own phone first, free**, then a poll of what the
testers actually carry, and only then a choice between the £79/yr Apple programme and doing the Android
work. ⭐ *The £79 buys distribution, and distribution is worth buying once you know the app is worth
distributing — not before.*

### What was actually in the way

Not the signing. `mobile/lib/main.dart:27` was:

```dart
const String kBaseUrl = 'http://localhost:8078';
```

⭐⭐ **A `const` is what kept the app on this machine.** `localhost` reaches the dev server from macOS, the
iOS simulator and Chrome because all three share the host's network. A phone does not — and a phone's
`localhost` is the phone.

## Decision

### 1. The address becomes runtime state with a compile-time default

Baking a LAN address in instead would only move the problem: wrong on someone else's Wi-Fi, wrong when the
router hands out a new lease, wrong again when the API is hosted — **three rebuilds for three answers to
the same question.**

So: `Server.load()` reads it from the device, falling back to
`String.fromEnvironment('MADBOOTS_API', defaultValue: 'http://localhost:8078')`. A hosted build ships its
own default via `--dart-define` and nobody types anything; until then, **More ▸ Settings ▸ Server** takes
it.

⚠️⚠️ **This field points the app wherever someone types.** Harmless on the owner's own phone, and *not*
something to hand a tester — it belongs behind a build flag before any wider build. Recorded here rather
than rediscovered later.

### 2. The check is the feature, not the text box

⭐⭐⭐ **Five different problems produce one symptom on a phone**: a sleeping Mac, a server bound to
loopback, a handset on 4G instead of the Wi-Fi, a typo, and a router admin page answering 200. Anyone can
store a string; what a person needs is to be told *which* of those they are looking at, because two of them
are not the app's fault at all.

So `reach()` returns four outcomes, not two:

* **`badAddress`** — answered **without touching the network**. *"That is not an address"* beats *"the
  server did not answer"* when the fault is the address, and a request never sent cannot be answered by the
  wrong machine either.
* **`wrongService`** — ⭐⭐ the outcome that earns the type. `/api/v1/health` now returns
  `{"ok", "service", "version"}`; a bare `{"ok": true}` could not tell this API from a captive portal, and
  reporting that as healthy is **worse than reporting a failure**, because every later error then gets
  blamed on the app.
* **`refused`** — and the message **names all three causes**, since they are indistinguishable from the
  app's side. A bare *"connection refused"* sends someone hunting through the code for a sleeping laptop.
* **`ok`** — which also **saves**. ⚠️ Storing an unverified address would leave the app broken on its next
  launch with no way back but reinstalling: *a setting that can brick the screen it is set from has to
  prove itself first.* "Use it anyway" exists for a server that is simply not up yet, and says so.

### 3. Two iOS keys that fail silently, and look like an app bug

`NSLocalNetworkUsageDescription` and `NSAppTransportSecurity.NSAllowsLocalNetworking`. Without the first,
iOS 14+ refuses local-network connections **without prompting**; without the second, ATS blocks cleartext
HTTP before the request leaves the process.

⭐ **Both produce the symptom the owner already reported once as an error in the app** — *"Connection
refused."* A setting whose absence produces a plausible bug report needs a test more than one that crashes,
so `tests/test_ios_networking.py` guards both.

⚠️⚠️ **`NSAllowsArbitraryLoads` is the wrong fix and the test rejects it by name.** It disables transport
security for every host — including the hosted API this is a stepping stone to — and it follows the app to
the App Store. `NSAllowsLocalNetworking` stops at the LAN.

### 4. The server stops refusing everything that is not this machine

`scripts/serve_api.sh` binds `--host 0.0.0.0` and **prints the Wi-Fi address to type into the phone**,
because `ipconfig getifaddr en0` is not a command anyone remembers. ⚠️ *A default that is correct for a
laptop is the bug when the client is a handset.*

## Consequences

⭐ **This gets the app in your hand, not in your pocket.** The phone reaches the Mac over Wi-Fi, so it
works at home with the laptop awake and fails everywhere else. Carrying it around is what hosting buys.

🔴 **The free certificate expires after seven days** and the app stops launching. Re-running one command
fixes it. That is the trade for not paying yet, and it is a real weekly cost — recorded in
[`iPhone_Free_Provisioning.md`](../03_Architecture/iPhone_Free_Provisioning.md) rather than discovered on
day eight.

⚠️ **The LAN address is a DHCP lease and will move.** The Settings field is how it gets fixed; a static
lease on the router removes it permanently if it becomes annoying.

✅ **Nothing here is wasted whichever way the poll goes.** The field that makes the LAN work is the field
that takes a hosted URL, and Android needs exactly the same two things — a runtime address and a reachable
server.

📌 **Held, explicitly:** Boot Battle from the Players list, the *"Add filter"* dropdown, and the pitch badge
for new signals. ⭐ The badge's round-trip cost was going to be measured on localhost — **which would have
been the same mistake as ADR-238's payload size**, measuring the wrong artefact. From a phone on 4G it is a
different number, so it waits for hosting or it is not measured at all.

## Verification

* **16 Dart tests** on the address and the reach check — one per *confusion* rather than one per function,
  because the confusions are the thing being fixed.
* **4 Python tests** on the health body and the two Info.plist keys, including one that compares the Dart
  test's hard-coded health literal against what the service actually returns. ⚠️ *A fixture nobody compares
  to the original is a fixture that is eventually wrong about it.*
* **8/8 mutations killed**: the trailing slash kept; a pasted docs URL accepted; any 200 counted as
  connected; the address validated only after the request was sent; the refusal message reduced to one
  cause; health stripped back to `{"ok": true}`; the permission prompt reduced to a placeholder; and ATS
  disabled everywhere instead of on the LAN.
* ✅ **`flutter build ios` succeeds** and both keys are present **in the built `Runner.app`**, not only in
  the source plist — ⭐ *the plist that matters is the one in the bundle.*
* ✅ The API answers on `http://192.168.1.35:8078` as well as on localhost, checked with `curl` against
  both.
