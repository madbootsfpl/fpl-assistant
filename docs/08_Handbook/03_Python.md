# Chapter 3 — Python

**Badges:** 📖 🧪 💻

---

## Purpose

Python is the main programming language for the project. This chapter covers how
it's installed and run. As of Sprint 001 the first real application code exists —
the `src/` package (`api`, `models`, `storage`, `ui`) plus `app.py`.

---

## Why We Use It

Chosen in the Project Charter: readable, beginner-friendly, huge ecosystem, and
well suited to APIs, data and (later) analytics. It's also a core learning goal.

---

## Concepts

- **Interpreter:** the `python3` program that runs your code.
- **Version matters:** this project uses Python **3.14** (via Homebrew).
- **stdlib:** the "standard library" — batteries included (e.g. `sqlite3`, `json`),
  no install needed.

---

## Examples

Confirming the interpreter and version (Session 1):

```bash
which python3        # → /opt/homebrew/bin/python3
python3 --version    # → Python 3.14.6
```

---

## Commands

```bash
python3 --version    # check version
python3 app.py       # run a script
python3 -m venv venv # create a virtual environment (see Chapter 4)
```

---

## Common Mistakes

- **Two Pythons, wrong one runs.** In Session 1 the shell used an old 3.10 even
  though 3.14 was installed. Fix: `hash -r`, then re-check with `which python3`.
- Confusing `python` and `python3` — inside an activated venv, `python` is correct.

---

## Best Practices

- Always know which Python and which environment you're in.
- Prefer the standard library before reaching for a third-party package.

---

## Lessons Learned

- "Installed" and "the one that runs" are not the same thing.

---

## Related Documents

- [Journal — Session 1](../01_Journal/FPL_Assistant_Dev_Journal_Session1.md)
- [Chapter 4 — Virtual Environments](./04_Virtual_Environments.md)
- [Chapter 16 — Debugging](./16_Debugging.md)
