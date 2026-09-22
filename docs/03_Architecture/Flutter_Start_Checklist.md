# Starting Flutter — what is ready, what is not, and what to decide first

**Written 2026-09-21, the evening before.** Audited by running the toolchain and the API, not by reading the
roadmap. Companion to [`Mobile_Platform_Audit.md`](Mobile_Platform_Audit.md), which is the plan; this is the
state.

---

## 🌙 The overnight downloads

✅ **Xcode 27.0 — installed and selected** (2026-09-21). ✅ **CocoaPods 1.17.0 — installed.**

⏳ **Still to fetch: the iOS simulator runtime.** Since Xcode 15 the runtime is a *separate* multi-gigabyte
download from Xcode itself — `xcrun simctl list runtimes` comes back empty, which is why `flutter doctor`
says *"Unable to get list of installed Simulator runtimes."*

```bash
sudo xcodebuild -downloadPlatform iOS      # or: Xcode ▸ Settings ▸ Components
```

⚠️ **`sudo gem install cocoapods` does not work on modern macOS, and this file said to run it.** The system
Ruby is **2.6.10** — frozen by Apple years ago — and CocoaPods' `ffi` dependency needs ≥ 3.0, so it fails
with a version error that reads as a CocoaPods problem rather than a Ruby one. ⭐ *The instruction was
copied from the Flutter docs without checking it against the machine it was for* — the same species as §5's
codegen plan two sections down, on the same evening.

```bash
brew install cocoapods     # ships its own Ruby, no sudo, leaves the system one alone
```

### What is actually blocked

**Nothing needed to start.** `flutter devices` reports **macOS (desktop)** and **Chrome (web)**, and the
whole Phase 4 foundation — navigation, theme, Riverpod, Drift, networking — builds and runs on either.

⭐ **Prefer macOS desktop for the first day.** It runs the *real* Flutter engine rather than the web
renderer, so widget behaviour, fonts and scrolling match iOS far more closely than Chrome does — and being
a native HTTP client it involves no CORS at all, which removes a whole class of confusing failure while the
first screens take shape. ⚠️ Keep testing Chrome too: the CORS support exists for it and only a browser run
exercises it.

The simulator runtime is what unlocks an **iPhone-shaped** window, and a physical device additionally needs
an Apple Developer account for signing.

---

## ✅ Ready, and verified this evening

| thing | state |
|---|---|
| **Flutter** | 3.47.5 stable · ✅ Xcode 27.0 · ✅ CocoaPods 1.17.0 · targets: **macOS desktop** and **Chrome** · ⏳ simulator runtime still downloading · Android not needed (the MVP is iPhone) |
| **The six API endpoints** | built, smoke-tested over a real socket (ADR-219/220) |
| **CORS** | ✅ added tonight — see below; without it every call from Chrome would have failed |
| **Real response samples** | `spikes/018-flutter-read-slice/api-samples/*.json`, one per endpoint |
| **The direct Supabase read path** | proven on the owner's network: 667 players, 162 KB, 511 ms (spike 018) |
| **The rounding question** | ✅ **settled** — zero boundary players on production at every horizon 1–8 |
| **`board.dart`** | written and verified against the live web app; carries straight into the real app |

### Run the API

```bash
venv/bin/python -m uvicorn src.service.http:app --port 8078   # interactive docs: /api/v1/docs
```

⭐ **`localhost` is enough for both Chrome and the iOS simulator** — the simulator shares the host's network.
A **physical device** cannot reach it, and that is the point at which hosting matters (§7.1 of the audit:
Fly.io or Render, £0–5/mo). ⚠️ *Do not build that until a real device needs it* — the audit's own warning
about infrastructure the timings do not justify.

### CORS was missing, and would not have looked like CORS

Added tonight. Without it, a Flutter **web** build — the only target ready before Xcode finishes — fails
every request, and the browser reports an opaque network error while the server logs an ordinary 200.
⭐ *Cheap to pin, expensive to diagnose*, so it is pinned by three tests.

🔴 **The allow-list is `*` because these endpoints serve *ids in, analysis out*** — no session, no cookie, no
user row. **That reason expires with Stage C**, the moment an answer depends on who is asking.
`test_credentials_are_never_echoed` is the tripwire.

---

## 🤔 Decide these before building — they are gates, not details

### 1. ~~How the Dart models get written~~ ✅ **DECIDED 2026-09-21 — [ADR-221](../06_Decisions/ADR-221-hand-written-models-guarded-from-both-ends.md), and built**

The audit §5 says: *"generate from the OpenAPI schema FastAPI already emits — one contract, no hand-written
duplicates."* **That does not work today.** Every route is typed `-> dict`, so the schema advertises each
response as an untyped object; a generator would produce request models and `Map<String, dynamic>` for every
response, and the client would hand-write them anyway — the duplicates the plan set out to avoid.

Three ways out:

| option | cost | what it buys |
|---|---|---|
| **Type the responses** with Pydantic models | a day, and ⚠️ **two definitions of every answer** — the dict the engine builds and the model describing it, which is ADRs 123/127/181 again | real codegen |
| **Hand-write Dart models** from the samples | hours | ⚠️ nothing keeps them in step but the shape test |
| **Hand-write, guarded** ← *what is set up* | done tonight | `tests/test_api_contract.py` fails when a response's **shape** moves, so a stale Dart model is caught in CI rather than on a phone |

✅ **Taken: the third, and the models are written.** `spikes/018-flutter-read-slice/app/lib/api/` holds
`models.dart` and `client.dart` — `dart analyze` clean, **14 Dart tests green against the real committed
responses**. Move them across with `board.dart` in step 3 below.

⚠️ **The Dart half runs locally, not in CI** (Flutter is not installed there). ⭐ *A test nobody runs is
not a guard* — wiring `flutter test` into the workflow belongs with creating the real app, and until then
`tests/test_api_contract.py` is the half that actually gates a commit.

### 1b. ~~Normalise the four player shapes~~ ✅ **DONE 2026-09-22 — [ADR-227](../06_Decisions/ADR-227-one-shape-for-a-player.md)**

⚠️ There were **five**, not four — the sweep found `captain.picks`, which no inventory had listed. `build` went 16.3 → 4.7 KB, `route` 5.9 → 1.9 KB, and the Dart client lost a whole class.


Writing the models found the API returns **four different player shapes**:

| where | keys |
|---|---|
| `analysis` — xi · bench · issues · weakest · top_pick | **11**, curated |
| `transfers.moves[].in` / `.out` | **5–6** |
| `route.target` | **6** |
| `route.blocked[].out`, `build.selected[]` | **42–45 raw database columns** |

⚠️ **`build` ships 45 columns per player to a phone** — `cbi`, `corners_order`, `cost_change_event` —
a 16.3 KB response where a curated one is ~3 KB, on the client whose architecture was justified by
measuring payload. And it **makes the database schema part of the API contract**: rename a column and
the mobile response changes, with nothing in between to notice.

⭐ **Recommendation: normalise every endpoint on the curated summary** — a ~20-minute change to three
endpoints, their samples and the models. Deliberately left for the morning: it is a contract change, and
it deserves its own agreement rather than being folded into a models task at the end of a session.

### 2. Whether the first screens need auth at all

**No — and spike 018 already proved the separation.** The board, fixtures, players and any squad the user
types in are all answerable with no identity: the read path uses the publishable key, and the six endpoints
take player ids. ⏳ **Stage C (Supabase Auth) is what remains of Phase 3**, and what it unlocks is a *saved*
squad, preferences, and the watchlist.

⭐ **Recommendation: build the decide-layer first, auth second.** That is the same cut spike 018 made — *the
read surface and the identity surface are separable, so separate them and learn from the cheaper one first.*

⚠️ **And the open question in Stage C does not touch Flutter.** What is unresolved is how *Streamlit* bridges
to a Supabase identity, because Streamlit cannot write a cookie from Python. Flutter gets real Supabase Auth
natively — no bridge, no minting. The database half the mobile client needs was proven in spike 016.

### 3. What the first release contains

The audit §6 already answers it — **This week · My squad · Transfers · Players** — with DNA radars, Scout,
Leagues and H2H as a second release. ⭐ *The mobile app is the decision layer; the web app stays the
exploration layer.* Worth re-reading rather than re-deciding.

---

## ✅ Done — the first hour, 2026-09-22

The app exists: **`mobile/`**, Dart package `madboots`, bundle `com.madboots.fpl`, targets macOS · iOS · web.
It runs on macOS desktop and renders a real squad analysis from the live service.

Two corrections the Flutter template needed, both worth knowing before the next `flutter create`:

* ⚠️ **The bundle id came out `com.madboots.madboots`.** `flutter create` builds it from `--org` plus the
  project name, so `--project-name madboots` became the last segment rather than `fpl`. Fixed in both Xcode
  projects and the macOS xcconfig.
* ⚠️⚠️ **macOS Flutter apps are sandboxed, and the template grants `network.server` but not
  `network.client`.** The first is Flutter's own debug tooling; the second is *outgoing requests*. Without
  it every call fails as a socket error — ⭐ *so it reads as a bug in the client, not a missing
  entitlement.* Added to Debug **and** Release.

**The theme is generated, not typed.** `brand.py` is the single source of truth (ADR-103/114) and says
*"consume these, don't re-type hexes"* — so `scripts/generate_brand_dart.py` emits `mobile/lib/brand.dart`,
and `tests/test_brand_dart.py` fails when the two drift. ⭐ *A generated file with no guard is a copy with
extra steps*, so the guard is in the **Python** suite — the one CI actually runs.

⭐ **Deliberately still absent: Riverpod, Drift, navigation.** They are on Phase 4's list; adding them before
a screen asks for anything is a foundation built to a guess. `http` is the only dependency.

---

## 📍 The original first hour, for reference

1. `flutter create` the app and run it on **macOS desktop** (`flutter run -d macos`) — the real engine,
   and no CORS in the way while the first screens take shape.
2. Point it at `http://localhost:8078/api/v1/health` — one call proves networking end to end. Then run
   the same build on **Chrome** (`flutter run -d chrome`), which is what exercises CORS.
3. Move `board.dart` across from spike 018. It is verified against the live web app and it already handles
   ⚠️ **`by_gameweek` arriving keyed by strings** — parse to `int` *before* sorting, or a prefix sum for
   "the next two gameweeks" answers for the wrong two.
4. `POST /api/v1/squad/analysis` with fifteen ids, and render the projected xP. That is the first thing the
   app does that a browser bookmark cannot.

---

## ~~⏳ Under review — Signals on the phone~~ ✅ **BUILT 2026-09-22 — [ADR-232](../06_Decisions/ADR-232-signals-and-a-memory-the-web-cannot-have.md)**

⭐ The *what-changed* view turned out to need **no new data** — only the observation that the **client** is the thing with a memory of this user. Every signal carries a stable key; the device remembers which it has shown.


**Raised 2026-09-22, deferred by the owner:** *"There may be a case for Signals in the app version, we can
review that later."*

⭐⭐ **The interesting part is that Signals may be on the wrong side of the audit's split.** §6 divides the
product into a *decision layer* (phone) and an *exploration layer* (web), and ADR-228 filed Signals with the
research surfaces. On reading it again that looks wrong: Signals answers **"what should I know?"** — FPL's
own news, an unexplained transfer exodus, headlines, community chatter — which is time-sensitive and
actionable **before a deadline**. That is exactly what a phone is for, unlike Team DNA, which is occasional
research by its own description.

⚠️ **And the phone already carries Signals' conclusions without its news.** A player's `status`, `chance`
and `leaving` all reach the pitch (ADR-151→156, ADR-206) — so the app can already tell you *João Pedro is
75%*. What it cannot tell you is **what changed since you last looked**, which is the question a manager
actually opens an app to ask on a Friday night.

⭐ So the question to review is not *"port Signals"* but ***"does the phone need a what-changed view?"*** —
a different feature, smaller, and one the existing data already supports.

📅 **Trigger, so this does not sit here indefinitely:** the first time the owner or a beta tester opens the
**web app on a phone** to check news before a deadline. That is falsifiable and it is the exact moment the
gap costs something. *A decline needs a re-measure date the same as a feature needs a review date*
(ADR-185/186).

---

## 🚫 Deliberately not done tonight, and why

- **API hosting** — nothing needs it until a physical device does.
- **Apple Developer Program (£79/yr)** — needed to ship, not to build; the simulator does not require it.
- **Android toolchain** — the audit scopes the MVP to iPhone.
- **Typed API responses** — decision 1 above; taking it tonight would have been taking it alone.
- **Stage C** — does not block Flutter, and its open question is a Streamlit problem.
- **The shared `requests.Session` for login RPCs (~2.35 s)** — a web-side cost, parked by the owner, and
  worth solving once for both clients rather than twice.
