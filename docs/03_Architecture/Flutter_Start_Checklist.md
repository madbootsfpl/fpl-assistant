# Starting Flutter — what is ready, what is not, and what to decide first

**Written 2026-09-21, the evening before.** Audited by running the toolchain and the API, not by reading the
roadmap. Companion to [`Mobile_Platform_Audit.md`](Mobile_Platform_Audit.md), which is the plan; this is the
state.

---

## 🌙 Do this tonight — it is the only thing with hours of wall-clock in it

**Start the Xcode download.** App Store → Xcode → install. It is several gigabytes and it is the one item
that cannot be hurried in the morning.

```bash
# once it has finished:
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
sudo gem install cocoapods
```

⚠️ **What it blocks is narrower than it looks.** Xcode blocks the **iOS simulator and a real device** — not
starting. `flutter doctor` reports `Chrome ✓` and two connected devices, so the whole Phase 4 foundation
(navigation, theme, Riverpod, Drift, networking) can be built and run tomorrow without it.

⭐ Which is why it is worth starting tonight rather than in the morning: nothing waits on it *until* the
first device test, and by then it will be done.

---

## ✅ Ready, and verified this evening

| thing | state |
|---|---|
| **Flutter** | 3.47.5 stable, `flutter doctor` green except iOS/Android toolchains |
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

### 1. How the Dart models get written  🔴 *the one that shapes the morning*

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

⭐ **Recommendation: the third, and revisit if it hurts.** The guard already catches a field disappearing,
changing type, or becoming non-nullable — verified by breaking it four ways. Typing six nested responses
before a single screen exists is optimising a problem nobody has measured yet, and it would install a second
definition of every answer in a codebase whose last two ADRs were both about exactly that.

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

## 📍 A suggested first hour

1. `flutter create` the app, run it on Chrome, confirm it builds.
2. Point it at `http://localhost:8078/api/v1/health` — proves networking and CORS end to end in one call.
3. Move `board.dart` across from spike 018. It is verified against the live web app and it already handles
   ⚠️ **`by_gameweek` arriving keyed by strings** — parse to `int` *before* sorting, or a prefix sum for
   "the next two gameweeks" answers for the wrong two.
4. `POST /api/v1/squad/analysis` with fifteen ids, and render the projected xP. That is the first thing the
   app does that a browser bookmark cannot.

---

## 🚫 Deliberately not done tonight, and why

- **API hosting** — nothing needs it until a physical device does.
- **Apple Developer Program (£79/yr)** — needed to ship, not to build; the simulator does not require it.
- **Android toolchain** — the audit scopes the MVP to iPhone.
- **Typed API responses** — decision 1 above; taking it tonight would have been taking it alone.
- **Stage C** — does not block Flutter, and its open question is a Streamlit problem.
- **The shared `requests.Session` for login RPCs (~2.35 s)** — a web-side cost, parked by the owner, and
  worth solving once for both clients rather than twice.
