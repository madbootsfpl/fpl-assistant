# Deploy runbook — Streamlit Community Cloud

How to put the Streamlit UI online for others to test (**ADR-053**). The repo is already deploy-ready
(pyproject `-e .` so `import src` works; a committed `data/seed.db`; `.streamlit/config.toml`) — this is
the few-clicks part, which **you run** (Claude can't create the account).

**Time:** ~5 minutes + a ~2–5 min first build. **Cost:** free. **Result:** a public URL like
`https://<name>.streamlit.app`.

---

## Prerequisites

- The repo is **public** on GitHub (`tesheridan/fpl-assistant`) ✅ and the **latest is pushed** (the
  deploy-ready commit — `pyproject.toml`, `-e .` in `requirements.txt`, `data/seed.db`).
- A GitHub account (you have one) — Streamlit Community Cloud signs in with it.

---

## Steps

1. **Go to** [share.streamlit.io](https://share.streamlit.io) → **Sign in with GitHub** → authorize
   Streamlit (grant access to the `fpl-assistant` repo when asked).
2. **Create the app** → **“Deploy a public app from GitHub”**, then set:
   - **Repository:** `tesheridan/fpl-assistant`
   - **Branch:** `master`
   - **Main file path:** `src/web_streamlit/Home.py`
   - *(Optional)* **Advanced settings → Python version:** `3.13` (the project needs ≥ 3.11).
3. **Deploy.** Community Cloud runs `pip install -r requirements.txt` (which installs the project via
   `-e .`) and then `streamlit run src/web_streamlit/Home.py`. First build takes ~2–5 min.
4. **Live** → the app opens at `https://<auto-name>.streamlit.app`. *(Optional)* In the app’s **Settings →
   General**, set a nicer **custom subdomain**, e.g. `fpl-assistant.streamlit.app`.
5. **Verify:** **Home** (all six pages in the sidebar) · **Players** (photos + the scatter) · **Fixtures**
   (team badges) · **Ask** (type a question → the decision + data + the ✓/⚠ trust line; **no written
   narration** — that’s expected, Ollama isn’t in the cloud).
6. **Share** the URL with your testers.

---

## After it’s live

- **Update the app:** push to `master` → Community Cloud **auto-redeploys**. (Or **Reboot** in the app’s
  menu.)
- **Refresh the data** (the deploy reads the committed snapshot). Two refresh stories:
  - **Cloud** (what testers see): `python app.py reseed` (one command — refresh into `data/fpl.db`, then
    copy it to `data/seed.db`), then **commit + push** (auto-redeploys, or Reboot). **Do this before GW1
    (2026-08-21)** and whenever prices/injuries move enough to matter. The player count in the app's
    freshness caption tells you whether the live snapshot is current.
  - **Local** (your own run): no reseed needed — the sidebar **🔄 Refresh data** button updates `fpl.db`
    in place, or just restart the app after a `python app.py refresh`.
- **Record the live URL** in the README’s “Live app” line.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Ensure `-e .` is in `requirements.txt` and `pyproject.toml` is committed (both are). Reboot. |
| Pages say **“No data yet”** | Ensure `data/seed.db` is committed and pushed (`git check-ignore -q data/seed.db` should exit 1). |
| **Ask** shows no written paragraph | Expected — no Ollama in the cloud; the decision + facts + trust line still show. |
| App shows a **“waking up”** screen | Normal on the free tier — it sleeps on idle and wakes on visit. |
| Build fails on install | Check the build log; confirm `requirements.txt` is valid; Python ≥ 3.11. |

---

## Security note (why this is safe to make public)

Read-only (the web never writes); no API keys/secrets in the repo; the FPL API is public; the LLM is
local-only and simply absent in the cloud. Worst case is public football analytics + some compute — low
risk. Add a password later (`st.secrets`) if you want to limit who tests. See **ADR-053**.
