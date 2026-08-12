# MADBOOTS infra changeover — runbook

Move the project onto the MADBOOTS brand's own GitHub + Streamlit + domain, and put the homepage live. Do it in
**one coordinated sitting** (~30–40 min), **before** the feature work — smallest beta, still preseason (GW1 =
2026-08-21), and the subdomain rename resets the per-domain cookie anyway (so do it before rebuilding persistence).

**Legend:** 🧑 = you click · 🤖 = Claude does (code/doc) · ✅ = verify before moving on.

> **The one real side-effect:** renaming the Streamlit subdomain **logs everyone out** (the remember-me cookie is
> per-domain) and the **old URL stops working**. That's fine for a small closed beta — testers just re-enter the
> code. **Cloud-saved squads survive** (they're keyed by handle, not domain).

---

## 0. Pre-flight (no downtime)

- ✅ **Everything committed + pushed** (the working tree is clean before we start).
- 🧑 **Copy your Streamlit secrets** — the app's *Settings → Secrets* (all the `FPL_*` values, `FPL_STORE_URL/KEY`,
  etc.). Paste them into a scratch note. *(If reconnecting redeploys the app as new, you re-enter these.)*
- 🧑 **Note any GitHub Actions secrets** — e.g. `MIRROR_URL` for the mirror-backup Action (*repo → Settings →
  Secrets and variables → Actions*). **These do NOT transfer** with the repo; you re-add them after.
- 🧑 Confirm you can access **`madbootsfpl`** (GitHub) and that **`madboots.streamlit.app`** is free (Streamlit app
  settings will tell you when you try to set it).
- 🧑 Decide: keep the repo name **`fpl-assistant`** (recommended — matches the package, least churn, GitHub
  auto-redirects the old URL) or rename to `madboots` later (optional, separate step).

---

## 1. Transfer the GitHub repo → `madbootsfpl`

- 🧑 On **github.com/tesheridan/fpl-assistant → Settings → (bottom) Danger Zone → Transfer ownership** → new owner
  **`madbootsfpl`** → confirm.
- ✅ Repo now lives at **github.com/madbootsfpl/fpl-assistant**; issues/stars/history intact; the old URL redirects.
- 🧑 **Re-add the Actions secrets** you noted (e.g. `MIRROR_URL`) in the new repo's *Settings → Secrets*.
- 🤖 **Update the local git remote** → `git remote set-url origin …/madbootsfpl/fpl-assistant.git`; confirm a push works.

---

## 2. Reconnect Streamlit to the new repo

- 🧑 In **Streamlit Community Cloud**, make sure the platform is **authorized for the `madbootsfpl` GitHub account**
  (*Workspace settings → linked GitHub / grant access*).
- 🧑 Point the app at **`madbootsfpl/fpl-assistant`**. Two paths:
  - If the app **auto-follows** the transfer (source shows the new owner) → nothing to do.
  - Else **delete + redeploy** the app from `madbootsfpl/fpl-assistant` (main branch, `app.py`), and **re-paste the
    secrets** from step 0.
- ✅ The app **builds and runs** from the new repo (open it, click through a page or two).

---

## 3. Rename the Streamlit subdomain → `madboots.streamlit.app`

- 🧑 App **Settings → General → (custom subdomain)** → set **`madboots`** → save.
- ✅ **`https://madboots.streamlit.app`** loads the app. *(⚠ everyone is logged out now; the old subdomain 404s.)*

---

## 4. Update the in-app URLs + docs (code/doc side)

- 🤖 Update the old-URL references and push to `madbootsfpl/fpl-assistant`:
  - `web_streamlit/pages/8_Feedback.py` — `_GITHUB_ISSUE` (→ `madbootsfpl/fpl-assistant`) + `_DEFAULT_ORIGIN`
    (→ `https://madboots.streamlit.app`).
  - `web_streamlit/Home.py` — the GitHub-issue link (→ `madbootsfpl`).
  - `README.md` — the CI badge + Actions links (→ `madbootsfpl`).
  - Any `FPL_FEEDBACK_ORIGIN` default / origin references → `madboots.streamlit.app`.
  - Docs (`DEPLOY.md`, `CLOUD_SQUADS.md`, `BETA.md`) — the old subdomain/repo mentions.
- 🤖 Commit + push. 🧑 If Streamlit Cloud serves a **stale build**, *Manage app → ⋮ → Reboot* (retry once if needed).
- ✅ Feedback tab shows the right GitHub link; a submitted feedback carries the new origin.

---

## 5. Homepage live on Cloudflare Pages (`madboots.com`)

*(You're already on Cloudflare DNS → one dashboard for Pages + DNS + SSL.)*

- 🧑 Rename **`~/Downloads/madboots-home.html` → `index.html`** (it's a single self-contained file).
- 🧑 **Cloudflare → Workers & Pages → Create → Pages → Direct Upload** → drag in the folder containing `index.html`
  → deploy. *(Or connect a small `madbootsfpl/madboots-site` repo if you'd rather deploy from git.)*
- 🧑 **Custom domain** → add **`madboots.com`** (+ `www`) to the Pages project → Cloudflare auto-creates the DNS +
  SSL (a couple of clicks since DNS is already here).
- ✅ **`https://madboots.com`** loads the homepage; the **Launch the app →** button opens `madboots.streamlit.app`.
- 🧑 *(Optional)* **`app.madboots.com` → 301 → `madboots.streamlit.app`** via a Cloudflare **Redirect Rule** (a
  tidy branded link; the URL bar still ends on `…streamlit.app`).

---

## 6. Verify end-to-end + tidy up

- ✅ **`madboots.com` → Launch → app → gate (enter code) → save/load a squad** all work.
- 🧑 Update any **shared links** (Reddit posts, the signup form, socials) to `madboots.com` / the new app URL.
- 🤖 Update **PROJECT_STATUS / Architecture / memory** to record the changeover as done.

---

## Rollback / safety

- **Repo transfer** is reversible (transfer back to `tesheridan`).
- **Subdomain** can be changed again (the old name may be reclaimable) — but every change logs everyone out, so
  avoid churn.
- **Secrets:** you kept a copy (step 0); Actions secrets were re-added (step 1).
- **Do it in a quiet window** and give any active testers a heads-up that they'll re-enter the code once.

---

*After this: the app lives at `madboots.streamlit.app` under `madbootsfpl`, `madboots.com` is the brand front door,
and we start the feature work (P0 quick-wins → IA restructure → persistence + Google auth). See `docs/Backlog.md`.*
