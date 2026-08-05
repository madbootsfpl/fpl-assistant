# Lessons Learned

**Sprint:** Sprint 056 — Deploy & share the Streamlit app (Streamlit Community Cloud)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the repo deploy-ready and write a runbook so the Streamlit UI can go public for functionality
testing. A collaborative sprint: Claude preps the repo + runbook; the owner does the account + deploy
clicks. The gate chose Streamlit Community Cloud (the owner relaxed the custom domain), a committed seed
DB, and a public/read-only posture.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Sizing a "big ask" honestly, then finding the simplest path (drop the domain → drop the infra).
- A security review before exposing an app publicly.
- Proving each deploy-prep item the honest way (from `/tmp`; with the DB hidden).

### New Skills Acquired

- Making a project pip-installable (`pyproject.toml` + `-e .`) so imports work under any launcher.
- Streamlit Community Cloud deployment (repo → main file → `*.streamlit.app`).
- `.gitignore` negation (`!path`) — and that git has **no inline comments**.

---

# What Went Well ✅

- **Relaxing the domain collapsed the sprint** — no PaaS / Cloudflare / Docker / `$PORT` / DNS; Community
  Cloud is a few clicks. The owner's flexibility was the biggest simplifier.
- **Everything was proven, not assumed** — the import fix by running pages from `/tmp`; the data fallback
  by hiding `fpl.db`.
- **Deployment = packaging, not analytics** — the engine + 442 tests were untouched.
- **Safe to expose** — read-only, no secrets, public data.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `import src` fails under `streamlit run` | The launcher puts the script's folder on the path, not the root | An editable install (`pyproject` + `-e .`) — no per-file `sys.path` hack |
| `!data/seed.db` didn't un-ignore | git `.gitignore` has **no inline comments** — the `# …` became part of the pattern | Move the comment to its own line; confirm with `git check-ignore` |
| No data on a fresh clone/deploy | The DB is gitignored | Commit `seed.db` + a `DB_PATH` fallback (fpl.db → seed.db) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Editable install > path hacks | `pip install -e .` puts the root on the path for *any* launcher — cleaner than `sys.path` edits |
| Prove with the real launcher | Running from `/tmp` reproduced the cloud's path reality (CWD ≠ root) |
| `.gitignore` has no inline comments | A trailing `# comment` becomes part of the pattern — put comments on their own line |
| Ship data for a repo deploy | A gitignored DB means the deploy is empty; a committed seed + a fallback fixes it |
| Simplicity is a decision | Dropping one requirement (the domain) removed an entire infra layer |

---

# Development Lessons 💻

- Before building deploy infra, question the requirement that forces it (the custom domain here).
- Verify each deploy-prep item under the *actual* runtime conditions, not the convenient local one.
- Keep deployment out of the core — it's packaging + config + a runbook, not analytics.

---

# AI Collaboration Lessons 🤖

- The owner's "whichever is easier/better" unlocked the simplest path — flexibility beats a fixed plan.
- Clear ownership split: Claude preps + documents; the owner runs the clicks that need his accounts.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-053 | Deploy on **Streamlit Community Cloud** (domain relaxed), a committed **seed DB**, **public/read-only**; `pyproject` + `-e .` for imports; Ask degrades without Ollama; going live is owner-executed via a runbook | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

-

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Go live** (run `docs/DEPLOY.md`) + record the URL; then gather tester feedback. Later: a Compare/
  Captain page; **Data Hardening** post-GW1 (per-GW history + form). GW1: 2026-08-21.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep questioning requirements that force complexity; keep proving deploy items under real conditions.

---

# Key Commands Learned

```text
pip install -e .                     # editable install -> `import src` works anywhere
git check-ignore -q <path>; echo $?  # 1 = not ignored (will be tracked), 0 = ignored
cp data/fpl.db data/seed.db          # refresh the committed deploy snapshot (then commit + push)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Editable install (`-e .`) | Installs the project so its source dir is importable process-wide |
| Streamlit Community Cloud | Free hosting that runs a Streamlit app from a public GitHub repo |
| Seed DB | A committed data snapshot so a repo deploy has data (the live cache is gitignored) |
| `.gitignore` negation | `!pattern` re-includes a path a prior rule excluded (no inline comments!) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/DEPLOY.md` | The Community-Cloud deploy runbook |
| ADR-053 | The deploy decision (host, data, access, security) |
| `pyproject.toml` | The packaging that makes `import src` work in the cloud |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Packaging (`pyproject` / `-e .`) | | |
| Deploying a Streamlit app | | |
| `.gitignore` rules | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-165 Gate — ADR-053 (Community Cloud; seed DB; public/read-only)
- US-166 Repo deploy-ready (pyproject + `-e .`, config, seed DB + fallback)
- US-167 Deploy runbook (`docs/DEPLOY.md`) + docs

**Stories Carried Forward:**

- Going live (owner runs the runbook) + record the URL

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
