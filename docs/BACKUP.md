# Backup runbook — no single point of failure

Right now the whole project lives in **one** place: GitHub (`origin`). If that account were lost, locked, or a
bad force-push wiped history, there's no second copy. This runbook sets up a **mirror** so the full history (all
branches + tags) is copied elsewhere automatically, plus a manual offline fallback. Background:
[ADR-095](06_Decisions/ADR-095-running-a-wider-beta.md). **Cost: £0.**

> The **seed data** (`data/seed.db`, `data/seed_squads.json`) is committed to the repo, so it's backed up with
> the code — no separate data backup is needed. The live cache (`data/fpl.db`) and local `squads.json` are
> gitignored working state and are always rebuildable with `python app.py refresh` / `reseed`.

---

## 1. The automatic mirror (recommended, ~5 min)

A GitHub Action (`.github/workflows/mirror.yml`) mirrors the repo to a second remote **on every push** and **once
a day**. It's **inert until you set the secret**, so nothing runs (or fails) until you opt in.

1. **Create a free mirror repo** on a different host — e.g. [Codeberg](https://codeberg.org) or GitLab. Make an
   empty repo `fpl-assistant` (private is fine).
2. **Make a push credential** on that host: a personal access token (or a deploy key) with **write** access to
   the mirror repo.
3. **Add the GitHub secret.** In the GitHub repo → **Settings → Secrets and variables → Actions → New repository
   secret**:
   ```
   Name:  MIRROR_URL
   Value: https://<user>:<token>@codeberg.org/<user>/fpl-assistant.git
   ```
   (Use the host + user + token for whichever mirror you made.)
4. **Trigger it once.** Push any commit, or run it by hand: **Actions → Mirror backup → Run workflow**. Check the
   mirror repo now has all the branches + tags.

That's it — from now on every push (and a daily cron) copies the full history to the mirror.

> **Note:** the workflow mirror-*clones* this repo over public HTTPS (no auth needed while the repo is public).
> If you ever make the GitHub repo **private**, add a read token to the clone URL in `mirror.yml` too (the
> `git clone --mirror https://github.com/…` line), or the Action can't read the source.

---

## 2. A manual offline copy (belt & braces)

Any time, from a local clone, make a single-file snapshot of the entire history and drop it in cloud storage
(Google Drive / iCloud / a USB stick):

```bash
git bundle create fpl-assistant-$(date +%Y%m%d).bundle --all
```

To restore from a bundle later:

```bash
git clone fpl-assistant-YYYYMMDD.bundle fpl-assistant
```

A `.bundle` is a complete, self-contained backup of every branch and tag — no server needed.

---

## 3. What to do if you need to restore

- **GitHub is gone / broken** → clone from the mirror (`git clone <mirror-url>`), then point `origin` back at a
  fresh GitHub repo and `git push --mirror origin`.
- **A bad force-push / deleted branch** → the mirror or a recent `.bundle` still has the lost refs; fetch from it
  and restore the branch.
- **You lost your laptop** → clone from GitHub (or the mirror); the committed `seed.db` means the app runs
  immediately (`python -m src.web_streamlit`), and `python app.py refresh` re-pulls live data.

---

## Summary

| Layer | What it protects against | Cost | Effort |
|-------|--------------------------|------|--------|
| GitHub (`origin`) | local machine loss | £0 | already have it |
| **Mirror remote** (Action) | GitHub account loss / bad force-push | £0 | ~5 min once |
| **`git bundle`** offline | everything online failing at once | £0 | ~10 s, ad hoc |
