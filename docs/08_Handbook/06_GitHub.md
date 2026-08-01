# Chapter 6 — GitHub

**Badges:** 📖 🧪 💻

---

## Purpose

GitHub is an online home for a Git repository — a copy of the project (and its full
history) hosted off your machine. This project now lives at
`github.com/tesheridan/fpl-assistant`.

---

## Why We Use It — and what it adds over local git

Local Git (Chapter 5) already records history *on your machine*. GitHub adds three
things on top:

1. **An off-machine backup** — if the Mac died, the whole project and its history
   are safe on GitHub.
2. **A remote** — a shared copy that other machines (or collaborators, or CI) can
   push to and pull from.
3. **A hub for Issues and Actions** — a backlog and automation, *when we want them*
   (not set up yet — see Status).

The key mental model: **local git and GitHub are two copies of the same history.**
`push` sends your local commits up; `pull` brings remote commits down. GitHub
doesn't replace Git — it's a *remote* that Git talks to.

---

## Concepts

- **Remote:** a named link to a copy of the repo elsewhere. The default name is
  `origin`.
- **`origin`:** conventionally, your main GitHub copy.
- **Tracking / upstream:** a local branch (`master`) can be linked to a remote one
  (`origin/master`) so `git push`/`pull` know where to go.
- **Push / pull:** send commits up / bring commits down.

---

## Examples (what was actually done)

Setting this project up on GitHub — create the empty repo on github.com, then from
the project folder:

```bash
git remote add origin https://github.com/tesheridan/fpl-assistant.git
git push -u origin master     # -u links master → origin/master (first push only)
```

Checking it worked:

```bash
git remote -v                 # shows origin (fetch/push) URLs
git status -sb                # top line: "## master...origin/master"
```

After that first `-u` push, everyday pushing is just:

```bash
git push
```

---

## Common Mistakes

- **Confusing GitHub with Git.** GitHub is a *remote copy*; Git is the tool. You can
  use Git with no GitHub at all (as we did for all of Sprint 001).
- **Forgetting `-u` on the first push** — then `git push` doesn't know where to go.
  The `-u` links the branch once; after that plain `git push` works.
- **Pushing secrets or generated files** — `.gitignore` already keeps `venv/`,
  `.env` and `data/*.db` out; keep it that way.

---

## Best Practices

- Push regularly, so the off-machine backup stays current.
- Keep `.gitignore` honest — the remote should hold source, not generated files.

---

## Lessons Learned

- `push`/`pull` clicked once "two copies of the same history" made sense — GitHub
  isn't a different thing to learn, it's a remote that Git already knows how to use.

---

## Status in this project

**Done:** created the repo, added `origin`, and pushed the full history
(`git push -u origin master`). All Sprint 001–002 commits are on GitHub.

**Not yet (future chapters/tasks):**

- GitHub **Issues** as the backlog (suggested in the Session 1 journal)
- GitHub **Actions** for linting/tests (Roadmap Phase 1 — Environment & CI/CD)
- A pull-request workflow (currently committing straight to `master`)

---

## Related Documents

- [Chapter 5 — Git](./05_Git.md)
- [Roadmap — Phase 1 (Environment & CI/CD)](../04_Roadmap/Roadmap.md)
