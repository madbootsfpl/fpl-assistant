# Getting MADBOOTS onto your own iPhone — without the developer programme

**What this is:** the app running on **your** phone, free, using a personal Apple ID. **Not** TestFlight,
**not** testers — that is the decision this defers (ADR-239).

**Time:** about twenty minutes the first time, two minutes after that.
**Cost:** £0.

---

## ⚠️ Read this first: what free provisioning does and does not give you

| | free (personal Apple ID) | paid (£79/yr) |
|---|---|---|
| Your own phone | ✅ | ✅ |
| **How long it keeps working** | 🔴 **7 days**, then it will not launch | a year |
| Other people's phones | 🔴 no | ✅ TestFlight, 10,000 testers |
| Needs the Mac to re-install | every 7 days | no |

🔴 **The seven days is the whole trade.** The certificate expires, and the app stops launching with a
message about an untrusted developer. Re-running step 5 fixes it in two minutes, and you will have to do it
weekly for as long as you stay on this path.

⭐ **That is fine for what this is for** — deciding whether the app is worth paying Apple for, and finding
the UX problems that only appear on a real phone in a real hand.

---

## ⚠️⚠️ And the bigger limit: this app talks to your Mac

The API runs on your laptop. The phone reaches it **over your Wi-Fi**, so:

* ✅ Works anywhere on your home network, with the Mac awake and `scripts/serve_api.sh` running.
* 🔴 **Does not work on 4G, at work, or anywhere else.** The moment the phone leaves the Wi-Fi, every
  screen fails.

⭐ *This gets the app in your hand, not in your pocket.* Carrying it around is what hosting buys, and that
is a separate decision — see ADR-239 §Consequences.

---

## Step 1 — Start the API so the phone can see it

```bash
scripts/serve_api.sh
```

It prints the address to type into the phone. ⚠️ **Not `localhost`** — a phone's localhost is the phone.

⭐ **If it says `✅ Already running`, that is success**, not a problem — you (or a previous session) already
started it. Leave it and move on.

```
  This machine on the Wi-Fi:  http://192.168.1.35:8078
```

⚠️ **macOS will ask once whether to allow incoming connections. Answer Allow.** A Deny is remembered, and
the symptom afterwards is a connection refused with nothing on screen to explain it.

⚠️ **That address can change.** It is a DHCP lease; a router reboot or a few days away can move it. If the
app stops connecting, run the script again and read the new one. (A static lease on the router removes
this permanently, if it becomes annoying.)

---

## Step 2 — Plug the phone in and trust the Mac

Cable, unlock the phone, **Trust This Computer** → **Trust**, enter the passcode.

```bash
(cd mobile && flutter devices)
```

⚠️ **The brackets matter.** Every command in this document runs from the repo root and leaves you there —
a bare `cd mobile` would leave your shell inside `mobile/`, and the next step's path would then resolve to
`mobile/mobile/ios/…` and fail. *(That is not hypothetical: it is why this note exists.)*

The iPhone should be listed. If it is not, the usual cause is the phone being locked.

---

## Step 3 — Sign in to Xcode with your Apple ID

```bash
open mobile/ios/Runner.xcworkspace     # from the repo root
```

⚠️ **`Runner.xcworkspace`, not `Runner.xcodeproj`** — the project on its own does not know about the
CocoaPods dependencies and will fail to build.

1. **Xcode ▸ Settings ▸ Accounts ▸ +** → Apple ID → sign in with your ordinary Apple ID. No enrolment, no
   payment.
2. In the left sidebar pick **Runner**, then the **Signing & Capabilities** tab.
3. ✅ **Automatically manage signing**.
4. **Team** → your name **(Personal Team)**.

Xcode will register `com.madboots.fpl` to your personal team and create a provisioning profile.

⚠️ **If it complains the bundle identifier is unavailable**, someone else has registered it. Change it —
`com.madboots.fpl.<yourinitials>` is enough — and note that this is cosmetic for a personal build.

---

## Step 4 — Trust the developer on the phone

The first install will fail to launch with *"Untrusted Developer"*. That is expected and is a one-time
thing per certificate.

**On the phone:** Settings ▸ General ▸ VPN & Device Management ▸ your Apple ID ▸ **Trust**.

---

## Step 5 — Install it

```bash
(cd mobile && flutter run --release -d <device-id>)
```

⭐ Your device id is the long string `flutter devices` printed next to the iPhone — for this Mac's phone,
`00008150-000C30122178401C`.

⭐ **`--release`, not debug.** A debug build is materially slower on a phone, and judging the app's feel
from one would be judging the wrong thing — the same species of error as measuring a payload from a
pretty-printed file (ADR-239).

⚠️ `--release` disconnects when you unplug, which is fine: the app stays installed. **This is the command
you re-run every seven days.**

### Optional: bake the address in

```bash
(cd mobile && flutter run --release \
  --dart-define=MADBOOTS_API=http://192.168.1.35:8078 -d <device-id>)
```

⭐ Saves typing it on the phone the first time. The Settings field still overrides it, and still has to be
used whenever the lease changes.

---

## Step 6 — Point the app at your Mac and prove it

**More ▸ Settings ▸ Server.** Type the address the script printed, press **Check and use**.

| what it says | what it means |
|---|---|
| **Connected — MADBOOTS 0.0.1** | ✅ done |
| *Nothing answered at …* | the script is not running, the Mac is asleep, the firewall was denied, or the phone is on 4G |
| *Something is running at …, but it is not MADBOOTS* | right address, wrong port — something else owns it |
| *That is not an address* | a typo, and the app never sent the request |

⚠️ **iOS will ask for permission to find devices on the local network the first time. Allow it.** A Deny is
remembered, and afterwards the failure is indistinguishable from the server being down — which is exactly
why `NSLocalNetworkUsageDescription` exists and why `tests/test_ios_networking.py` guards it.

---

## When it stops working

| symptom | cause | fix |
|---|---|---|
| Will not launch, *"untrusted"* or nothing at all | 🔴 **the 7-day certificate expired** | re-run step 5 |
| Every screen says nothing answered | Mac asleep, script not running, or phone off the Wi-Fi | start the script; check the phone's Wi-Fi |
| Worked yesterday, refuses today, Mac is on | ⚠️ **the DHCP lease moved** | re-run the script, retype the new address |
| Connected, but the squad will not load | the API is up and something else is wrong | read the message — it names the endpoint |

---

## What this is a stepping stone to

**Two decisions, and the poll decides which:**

* **Apple, £79/yr** → TestFlight, 10,000 testers, no 7-day expiry.
* **Android** → no annual fee to sideload, and an `.apk` can simply be sent to someone.

⭐ **Both need the API hosted first**, because both put the app on a phone that is not on your Wi-Fi.
Nothing in this document is wasted either way: the Settings field that makes the LAN work is the same field
that will take a hosted URL.
