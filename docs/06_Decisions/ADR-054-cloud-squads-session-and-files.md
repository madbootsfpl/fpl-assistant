# Architectural Decision Record: Cloud squads — a session "active squad" + downloadable files

**Decision ID:** ADR-054
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Extends the Streamlit edge (ADR-050/051/052) with user squad state; the web
equivalent of the CLI's saved squads (ADR-024), adapted for a public, multi-user, ephemeral cloud host.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The deployed app (ADR-053) has **no saved squads and can't make one**: the CLI's `data/squads.json` is
gitignored (so it isn't in the repo/cloud), the web is read-only by design, and Streamlit Community
Cloud's disk is **ephemeral** and **shared across all users** — so writing a squad file server-side would
neither persist nor be per-user. The owner wants each tester to **build a squad, save it, and manage
transfers**, with **no per-user firewall needed** yet.

#### A planning probe confirmed the mechanism (Path 1)
- The saved-squad JSON is `{player_ids, player_names, bench_ids, cost}` — the CLI's `SquadStore` format,
  so a downloaded squad is **CLI-interoperable**.
- `select_squad` yields the structured 15 (+ `best_legal_xi` for the bench) → a downloadable `squad.json`.
- `Transfer` already builds `owned` from `squad["player_ids"]`, so a session/uploaded squad just works.

#### Decision Drivers
- **Per-user squads, no accounts/firewall** (the owner's ask).
- **Persistence on an ephemeral, multi-user host** — impossible server-side without a DB.
- **Keep the architecture** — no server writes; the DB/squads stay read-only.

---

### ✅ Decision

**1. A session "active squad" + downloadable files (Path 1).** The web holds an **active squad** — a
SquadStore-compatible dict — in `st.session_state["squad"]`. It's set by **building** one (Build → "use
this squad") or **uploading** a `squad.json`. Persistence is the **user's own file**:
`st.download_button` (save) + `st.file_uploader` (load). This gives every tester their own persistent
squad with **zero server infrastructure, no accounts, and no server-side writes**.

**2. A unified `web_squads` helper (edge).** Lists the **available squads** — the committed **demo**
squads (read-only) + the **session** active squad — and resolves the chosen one to a squad dict for the
pages. The web **never** calls `SquadStore.save` (a test asserts it); the DB/`SquadStore` are read-only on
the cloud.

**3. A committed demo seed.** `data/seed_squads.json` (one demo squad) is committed, and `config.SQUADS_PATH`
**falls back** to it when `squads.json` is absent (mirroring the `seed.db` fallback, ADR-053) — so the
cloud pages populate on first visit. The local dev `squads.json` stays gitignored.

**4. The format — SquadStore-compatible.** The download/upload JSON is the `SquadStore` squad dict
(`player_ids` · `player_names` · `bench_ids` · `cost`), so a web-built squad drops straight into the CLI
and vice-versa. Uploads are **validated** (keys present; ids exist in the DB) with a clear error, no crash.

**5. Consumers — Transfer, Analyse, Captain.** All three run the engine on the active squad's **dict**
(not `ask`-by-name, so an uploaded squad works): `Transfer` (`suggest_transfers`), `Analyse`
(`analyse_squad` on the owned players), and a **new Captain page** (`captain_picks`). A page offers the
active session squad and the demo squad(s) via the helper.

**6. Upload UI — the sidebar (owner's call).** A `file_uploader` + the active-squad name live in the
**sidebar**, visible on every page — upload once, and Transfer/Analyse/Captain see it immediately. Build
carries the **Download** button.

---

### 🔀 Alternatives Considered

- **A server-side store (external DB, "save as `<name>`").** Seamless + persistent across devices, but
  needs an external DB account, a secret, a persistence adapter, and the first server-side writes.
  Deferred to the Backlog (Path 2) — revisit once download/upload friction proves it worth it.
- **Session-only (no download).** Simplest, but a squad is lost on refresh — fails "save it somewhere."
- **Per-user auth/isolation.** The owner explicitly doesn't need a firewall yet — skipped.
- **Analyse via `ask`-by-name.** Only works for named `SquadStore` squads; an uploaded squad isn't one —
  so Analyse runs the engine on the dict directly.

---

### 🧭 Consequences

**Positive**
- Every tester gets their own **persistent** squad (their file), with no accounts, no DB, no firewall —
  exactly the ask; unblocks real feedback.
- **No server writes** — the DB/squads stay read-only; the clean architecture (and the guardrail) holds.
- The download format is **CLI-interoperable** — web and CLI share squads.

**Negative / risks (mitigations)**
- **Manual save/load** (download a file, re-upload next session) → clear UI (Download = your save); Path 2
  (a server DB) is the later seamless upgrade.
- **A bad uploaded file** → validate on upload; a clear message, no crash.
- **Accidental server write** → the web never calls `SquadStore.save`; a test asserts it.
- **Analyse for a dict** → run `analyse_squad` on the owned players directly.

---

### 📊 Validation

Prototyped on the live DB: the format round-trips (`SquadStore` dict); `select_squad` → a downloadable 15;
`Transfer` consumes `squad["player_ids"]`. Acceptance for the sprint: build → download a `squad.json`;
upload it → Transfer/Analyse/Captain run on it; a committed demo squad populates the pages; the web makes
**no** server writes; the existing 442 tests stay green.
