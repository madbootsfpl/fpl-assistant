# Sprint 056: Deploy & share the Streamlit app (Streamlit Community Cloud)

> **Gate outcome (US-165 / ADR-053):** the owner **relaxed the custom domain** → **Streamlit Community
> Cloud** (easiest; free; one-click from the public repo → a `*.streamlit.app` URL), a committed **seed
> DB**, **public/read-only**. This drops the PaaS + Cloudflare + `$PORT`/Docker/DNS work below — US-166/167
> are simplified accordingly.

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done) — repo deploy-ready; going live is owner-executed
**Capacity:** ~2–3 working sessions (a gate + repo prep + a deploy runbook + docs) — **collaborative**
**Carried Over:** Deploy & share (from the Sprint-54 review / Backlog)

> **Direction (owner):** host the Streamlit app publicly at **`fpl.malahide.cc`** (via Cloudflare) so
> others can help functionality-test. A **collaborative** sprint: *Claude* makes the repo deploy-ready +
> writes a runbook; *Tony* creates the host account, connects the repo, and sets the Cloudflare DNS.

---

### 🔎 Verified at planning (safe to go public; a few prep items)

- **No secrets exposed.** No API keys/tokens in the code; the FPL API is public (a User-Agent only);
  Ollama is local and simply **absent** in a deploy (the app degrades to decision + facts — fine, and
  cleaner for a demo). Going public leaks nothing sensitive — it's public football data.
- **The web is read-only.** The web edges never write (only `st.chat_message().write()` display calls);
  no auth needed for a read-only demo.
- **Two prep items:**
  1. **Bind the port/host** — the runner uses `streamlit run` (defaults to `localhost:8501`); a PaaS needs
     `--server.port $PORT --server.address 0.0.0.0`.
  2. **A data strategy** — `data/*.db` is gitignored, so a repo deploy has **no data**; ship a committed
     **seed DB** (preseason data is near-static) or refresh-on-start.
- **The custom domain drives the host choice.** Streamlit Community Cloud doesn't cleanly support custom
  domains; a PaaS (Render/Railway/Fly) supports `fpl.malahide.cc` natively (CNAME + auto-TLS). Cloudflare
  = a CNAME `fpl → <host target>` (DNS-only to start).
- Preseason (GW1 2026-08-21) — the shipped data is stable for now.

---

### 🧭 What's new — the app leaves the laptop

The Streamlit UI becomes a **shared, public, read-only** site at `fpl.malahide.cc`. The analytics don't
change; this is packaging (a data strategy + a port/host bind + a Streamlit deploy config) + a **runbook**
the owner follows to go live (host account → connect repo → custom domain → Cloudflare CNAME).

---

### 🎯 Sprint Goal

**Objective:** the repo is **deploy-ready** (binds `$PORT`/`0.0.0.0`, a shipped data strategy, a Streamlit
deploy config) and a **runbook** takes the owner from zero → `https://fpl.malahide.cc` on the chosen host,
with a light security posture (read-only, public, no secrets). Core analytics + tests unchanged.

#### Success Criteria
- [ ] Approach agreed (**ADR-053**) — the **host** (a PaaS w/ custom domains vs Streamlit Cloud); the
      **data strategy** (committed seed DB vs refresh-on-start); the **access** posture (public vs a simple
      password); the domain-via-Cloudflare shape; the security review
- [ ] **Port/host bind** — the app serves on `$PORT` / `0.0.0.0` (a start command and/or the runner reads
      `PORT`)
- [ ] **Data on the deploy** — a committed seed DB (or a refresh-on-start hook) so the pages have data
- [ ] **Deploy config** — a `.streamlit/config.toml` (headless; usage-stats off; CORS/XSRF as needed) +
      any host manifest (`render.yaml` / `Procfile` / start command)
- [ ] **A runbook** — a step-by-step: host account → connect the GitHub repo → set the start command → add
      the custom domain → the Cloudflare CNAME → verify TLS
- [ ] **Live** — the owner follows the runbook; `https://fpl.malahide.cc` serves the app (the collaborative
      "done")
- [ ] Core analytics unchanged; the existing **442** tests stay green; the two-edge guardrail holds
- [ ] Docs: ADR-053 + index, Architecture (a deploy note), README (the live URL + how to deploy),
      PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-165 | **Gate.** Deployment design (**ADR-053**): host, data strategy, access, security review | Critical | ✅ Done | 0.5 session |
| US-166 | **Make the repo deploy-ready (Community Cloud)** — make `src` importable under `streamlit run` (a light packaging/bootstrap); a `.streamlit/config.toml`; commit a **seed DB** + point the app at it (a data-path fallback). Tests stay green | High | ✅ Done | 1 session |
| US-167 | **Deploy runbook + docs** — the Community-Cloud step-by-step (connect the repo → set the main file → the `*.streamlit.app` URL); the owner runs it; docs (Architecture deploy note, README live URL + deploy steps, PROJECT_STATUS) | High | ✅ Done | 0.5–1 session |

#### Technical Tasks & Maintenance
- [x] ADR-053 recorded + added to the ADR index — _US-165_
- [x] Importable-under-`streamlit run` + `.streamlit/config.toml` + a committed seed DB — _US-166_
- [x] The Community-Cloud runbook + Architecture/README/PROJECT_STATUS — _US-167_

---

### ✅ Definition of Done (this sprint)

A collaborative DoD (repo prep is Claude's; going live is the owner's, guided):
1. **Deploy-ready + green** — the app binds `$PORT`/`0.0.0.0`, has data on the deploy (seed DB or refresh),
   a deploy config; the existing **442** tests stay green; the core is unchanged; no secrets in the repo.
2. **Live (owner-executed)** — following the runbook, `https://fpl.malahide.cc` serves the app (Cloudflare
   CNAME + host TLS); a quick manual pass (Home + a page + Ask degrading without Ollama).
3. **Documentation** — ADR-053 + index, Architecture (deploy note), README (live URL + deploy steps),
   sprint board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Repo prep ($PORT/host, config, data strategy) + a runbook | Auth/accounts / user data / writes (the deploy is read-only) |
| A public, read-only Streamlit deploy at `fpl.malahide.cc` | Hosting Ollama (the LLM stays optional/absent — degrades) |
| A light security review; optional password | A CI/CD auto-deploy pipeline — later, if wanted |
| The Cloudflare CNAME shape (guidance + runbook) | The owner's account creation / DNS clicks (his to do, guided) |

**External Dependencies (owner):** a host account (PaaS or Streamlit Cloud); Cloudflare DNS for
`malahide.cc`; the GitHub repo (public, already pushed). **Claude cannot create accounts or set DNS** —
those steps are the owner's, guided by the runbook.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Custom domain won't attach (host limits) | Med | Choose a host with **native custom domains** (PaaS); Cloudflare CNAME (DNS-only) + host TLS; the gate settles the host |
| The deploy has no data (DB gitignored) | High | Ship a committed **seed DB** (preseason data is stable) or refresh-on-start — a gate call |
| Public abuse / resource use (ILP, LLM) | Low | Read-only; no secrets; optional password; host free-tier limits; Ollama absent (no LLM cost) |
| Free-tier cold starts | Low | Accept ~30–60s first-hit on idle (a testing demo); note it |
| Secrets/data leak | Low | Verified: no secrets in the repo; only public FPL data; a security check in the gate |

---

### 🗝️ Gating decision (US-165 → ADR-053)

Settle before prep — security is clear (read-only, no secrets); these are the ops calls. Proposed
(confirm/redirect at "start US-165"):

1. **Host — the key call.** A **PaaS with native custom domains** (Render / Railway / Fly.io) so
   `fpl.malahide.cc` attaches cleanly with auto-TLS. *(Streamlit Community Cloud is easiest to deploy but
   doesn't do custom domains cleanly — only if you'd accept a `*.streamlit.app` URL.)* *Propose a PaaS.*
2. **Data strategy.** Ship a committed **seed DB snapshot** (simple; preseason data is near-static; no
   boot-time API calls) *vs* refresh-on-start (fresh but slower/heavier). *Propose the seed DB.*
3. **Access.** **Fully public, read-only** (max ease for testers) *vs* a **simple password** (limit who
   tests). *Propose public — it's read-only public data; add a password later if wanted.*
4. **Domain.** Cloudflare **CNAME `fpl → <host target>`** (DNS-only to start; the host issues TLS).

**Security review (done):** read-only web, no writes; no API keys/secrets in the repo; FPL API public;
Ollama absent → degrades to decision + facts. Worst case is public football analytics + some compute —
low risk.

---

### 📝 Session Progress Log

- **US-165 (gate) ✅** — Recorded **ADR-053**. The owner **relaxed the custom domain** ("whichever is
  easier/better"), which removed the only reason for a PaaS + Cloudflare — so: **host = Streamlit
  Community Cloud** (free, one-click from the public repo, manages the server/port/TLS → a
  `*.streamlit.app` URL); **data = a committed seed DB** (the repo deploy has no DB otherwise; preseason
  data is stable — refresh the snapshot before GW1); **access = fully public, read-only** (low risk —
  public football data, no secrets; a password can come later). Security review passed (no secrets;
  read-only web; FPL API public; Ollama absent → **Ask degrades to decision + facts**). Repo-prep (US-166)
  shrank to: make `src` importable under `streamlit run` (a light packaging/bootstrap), a
  `.streamlit/config.toml`, and the seed DB — **no `$PORT`/Docker/Cloudflare/DNS**. Going live is
  owner-executed via the US-167 runbook. ADR-053 indexed.
- **US-166 ✅** — Repo deploy-ready.
  - **Import fix** — a minimal **`pyproject.toml`** (`packages.find include=["src*"]`) + **`-e .`** in
    `requirements.txt`, so an editable install puts the project root on the path and `import src` resolves
    under `streamlit run src/web_streamlit/Home.py` (no `sys.path` hack, no `PYTHONPATH`). **Proven** by
    running the pages via `AppTest` from **`/tmp`** (CWD ≠ repo root) — no `ModuleNotFoundError`, exactly
    how Community Cloud launches it.
  - **`.streamlit/config.toml`** — `server.headless`, `browser.gatherUsageStats=false`.
  - **Seed DB** — committed **`data/seed.db`** (a 296 KB snapshot of the current cache); un-ignored via a
    `.gitignore` exception (`!data/seed.db` — on its own line, since git has **no inline comments**, which
    first silently broke the negation). `config.DB_PATH` **falls back** to `seed.db` when `fpl.db` is
    absent (a fresh clone / a deploy). **Proven:** with `fpl.db` hidden, the Players page renders data
    from `seed.db`.
  - **Green:** 442 tests, ruff clean; the editable install + config change broke nothing.
- **US-167 ✅** — The **deploy runbook** (`docs/DEPLOY.md`): the Community-Cloud steps (sign in with GitHub
  → New app → repo `tesheridan/fpl-assistant`, branch `master`, main file `src/web_streamlit/Home.py` →
  Deploy → a `*.streamlit.app` URL), a verify checklist, "after it's live" (auto-redeploy on push; refresh
  = `refresh` + `cp fpl.db seed.db` + push, esp. before GW1), a troubleshooting table, and the security
  note. **Docs:** README (a "Live app" line + the deploy pointer), Architecture §12 (the deploy note),
  PROJECT_STATUS (deploy line + ADRs → 53).
  - **Owner-executed:** going live is Tony's few clicks on Community Cloud (after this sprint's push) —
    the repo is deploy-ready + the runbook is the guide.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the repo is **deploy-ready** and a **runbook** takes the owner from the repo →
a public `*.streamlit.app`. **442 tests** (unchanged — repo prep, no analytics); **53 ADRs**. Going live
is the owner's few clicks (guided).

**Delivered**
- **US-165 (gate)** — ADR-053: the owner **relaxed the custom domain** → **Streamlit Community Cloud** + a
  committed **seed DB** + **public/read-only**; security reviewed (no secrets, read-only, Ollama-absent).
- **US-166** — deploy-ready: `pyproject.toml` + `-e .` (so `import src` resolves under `streamlit run`), a
  `.streamlit/config.toml`, a committed `data/seed.db` + a `DB_PATH` fallback.
- **US-167** — the runbook (`docs/DEPLOY.md`) + docs (README live URL, Architecture, PROJECT_STATUS).

**What went well**
- **Relaxing the domain collapsed the sprint** — dropping the custom domain removed the whole PaaS +
  Cloudflare + Docker + `$PORT` + DNS layer; Community Cloud is a few clicks. A good owner call.
- **Every prep item was proven the honest way** — the import fix by running pages from `/tmp` (the cloud's
  path reality); the data fallback by hiding `fpl.db` and seeing `seed.db` serve.
- **The layered core paid off again** — deployment was packaging, not analytics; the engine and 442 tests
  were untouched.
- **Safe to expose** — read-only, no secrets, public data; the security review was quick and clean.

**Challenges / how they were handled**
- **`import src` under `streamlit run`** — Community Cloud runs the entrypoint with the script's folder on
  the path, not the root. An **editable install** (`pyproject` + `-e .`) fixes it cleanly (no per-file
  `sys.path` hack) — proven from `/tmp`.
- **A silent `.gitignore` bug** — git has **no inline comments**, so `!data/seed.db  # …` became a literal
  pattern and didn't un-ignore the file. Caught by `git check-ignore`; fixed by moving the comment.
- **No data on a fresh clone/deploy** — the DB is gitignored; a committed `seed.db` + a `DB_PATH` fallback
  gives the deploy data with no boot-time API calls.

**Carried forward:** *Going live* — the owner runs `docs/DEPLOY.md` on Community Cloud (after this push),
then records the live URL in the README.
