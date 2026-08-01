# Chapter 5 — Git

**Badges:** 📖 🧪 💻 🧠

---

## Purpose

Git records the history of the project — every change, when it happened, and why.
It lets you see what changed, undo mistakes, and understand past decisions.

---

## Why We Use It

It's the backbone of professional development and a core learning goal. On this
project we've used it heavily: staging, committing in small logical chunks, and
writing clear messages that explain *why*.

---

## Concepts

- **Repository (repo):** the project folder plus its full history.
- **Working tree:** your current files. **Staging area:** what's queued for the next
  commit. **Commit:** a saved snapshot with a message.
- **Branch:** a line of development. This project currently works on `master`.
- **Commit message:** a short summary line, then a body explaining *why*.

The flow: edit files → `git add` (stage) → `git commit` (save) → repeat.

---

## Examples

Real commits from Session 2 (small, logical, well-described):

```text
5b53cef  Add Sprint 001 plan, update project status, reorganise docs
d67c085  Add architecture v0.1 draft and ADR-001/ADR-002
e05b084  Mark architecture v0.1 as agreed
e1ddb7c  End-of-session updates: status, journal, glossary
```

Notice each commit is one coherent idea, not a dump of unrelated changes.

---

## Commands

```bash
git status              # what's changed / staged
git status --short      # compact version
git add <file>          # stage a file
git add -A              # stage everything (new, modified, deleted)
git commit -m "msg"     # commit staged changes
git log --oneline -5    # recent history, one line each
git diff                # unstaged changes
git branch              # list branches
```

---

## Common Mistakes

- **Giant, vague commits** ("stuff", "updates"). Prefer small commits with a clear
  reason.
- **Committing generated/large folders** like `venv/` — use `.gitignore`.
- Forgetting to stage a new file (untracked files aren't committed until `add`ed).

---

## Best Practices

- Commit little and often; one logical change per commit.
- Message = *what* in the summary, *why* in the body.
- Check `git status` before and after committing.

---

## Lessons Learned

- Clean, small commits make the history readable — "future Tony" can follow the
  reasoning, not just the changes.

---

## Related Documents

- [Chapter 6 — GitHub](./06_GitHub.md)
- [Journal — Session 2](../01_Journal/FPL_Assistant_Dev_Journal_Session1.md)
- [Chapter 18 — Cheat Sheets](./18_Cheat_Sheets.md)
