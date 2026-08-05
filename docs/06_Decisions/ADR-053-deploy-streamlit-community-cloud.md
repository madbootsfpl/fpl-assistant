# Architectural Decision Record: Deploy & share the Streamlit app (Community Cloud)

**Decision ID:** ADR-053
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** First public deployment of the app (the Streamlit edge, ADR-051/052). No
change to the analytics core.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The Streamlit UI is now presentable (Sprint 055), and the owner wants it **shared publicly** so others can
help functionality-test. The initial idea was a custom domain (`a custom domain`) via Cloudflare + a PaaS
— but **the owner relaxed the custom-domain requirement** ("whichever is easier/better"). That removes the
only reason to run a PaaS, and points at the simplest path.

#### A security review — safe to go public
- **No secrets in the repo** — no API keys/tokens; the FPL API is public (a User-Agent only); Ollama is
  **local and absent** in a deploy (the app degrades to decision + facts — fine, and cleaner for a demo).
- **The web is read-only** — the web edges never write (only `st.chat_message().write()` display calls);
  no auth needed.
- **Worst case** is public football analytics + some compute — low risk.

#### Decision Drivers
- **Easiest path to a shareable URL** (the owner's stated priority, domain relaxed).
- **No new infra** — avoid servers, ports, Docker, DNS/TLS if not needed.
- **Unchanged core** — deployment is packaging, not analytics.

---

### ✅ Decision

**1. Host — Streamlit Community Cloud.** With the custom domain dropped, deploy the **public GitHub repo**
straight to **Streamlit Community Cloud** (free; one-click; it runs `streamlit run <entrypoint>` and
manages the server/port/TLS). The app gets a `*.streamlit.app` URL — shareable immediately. *(No PaaS,
Cloudflare, Docker, `$PORT` bind or start command needed.)*

**2. Data — a committed seed DB.** `data/*.db` is gitignored, so a repo deploy has **no data**. Commit a
**seed snapshot** (e.g. `data/seed.db`, un-ignored) that the deployed app reads — no boot-time API calls,
fast, simple. Preseason data is near-static; **refresh the snapshot** occasionally (and before GW1). The
local dev DB stays gitignored.

**3. Access — fully public, read-only.** Anyone with the link can use it — it's read-only public football
data with no secrets, so this maximises ease for testers. A simple password (`st.secrets`) can be added
later if wanted.

**4. Repo-prep (US-166), kept minimal.**
- Make `src` importable under Community Cloud's `streamlit run` (the same import/`sys.path` reality the
  runner handles locally) — via a light packaging step or an entrypoint bootstrap.
- A `.streamlit/config.toml` (headless; usage-stats off; sensible defaults).
- The **seed DB** committed + the app pointed at it (a data-path fallback).
- No `$PORT`/`0.0.0.0`/Docker/DNS — Community Cloud handles the server.

**5. Ask on the deploy.** No Ollama in the cloud → **Ask degrades to the decision + facts** (no written
prose), exactly like the CLI without Ollama. Documented on the page / README.

**6. Going live (US-167) is owner-executed.** Claude makes the repo deploy-ready + writes the runbook;
the owner connects the repo on Community Cloud (a few clicks). Claude cannot create the account.

---

### 🔀 Alternatives Considered

- **A PaaS (Render / Fly.io) + Cloudflare custom domain.** The plan when a custom domain was wanted —
  native custom domains + TLS, but more setup (an account, a start command with `PYTHONPATH`/`$PORT`,
  Cloudflare DNS, TLS, a Dockerfile for Fly). **Unnecessary once the domain was relaxed.**
- **A custom domain via Cloudflare on Community Cloud.** Community Cloud doesn't support custom domains
  cleanly (a fragile Host-header rewrite). Dropped with the domain.
- **A password / auth.** Deferred — it's read-only public data; add later if abuse appears.
- **Refresh-on-start for data.** Fresher, but slower boot + API calls per wake + more moving parts;
  the seed DB is simpler for a preseason demo. Revisit post-GW1.
- **Self-host (VPS).** Overkill for a read-only demo.

---

### 🧭 Consequences

**Positive**
- The fastest route to a public, shareable URL — a few clicks on Community Cloud from the existing repo.
- Zero new infra (no server/port/Docker/DNS); the analytics core is untouched.
- Read-only + no secrets → low-risk to expose; unblocks real functionality-testing feedback.

**Negative / risks (mitigations)**
- **The seed DB goes stale** → refresh + recommit the snapshot (and before GW1); note the "as of" date.
- **Community Cloud sleeps on idle** (a wake screen on first hit) → acceptable for a testing demo.
- **The cloud import/`sys.path`** must be handled → US-166 (a light packaging/bootstrap; the local
  behaviour is unchanged).
- **No narration on Ask** (Ollama absent) → documented; the decision + facts + trust line still show.

---

### 📊 Validation

Security reviewed (no secrets; read-only; public data; Ollama-absent degrade). Acceptance for the sprint:
the repo is deploy-ready (importable under `streamlit run`, a committed seed DB, a `.streamlit` config)
and a runbook takes the owner from the repo → a live `*.streamlit.app` URL; a manual pass shows Home + a
page + Ask degrading gracefully. Going live is the owner's execution of the runbook.
