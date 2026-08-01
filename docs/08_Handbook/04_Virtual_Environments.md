# Chapter 4 — Virtual Environments

**Badges:** 📖 🧪 💻

---

## Purpose

A virtual environment (venv) is a private, per-project Python installation. It keeps
this project's packages separate from other projects and from the system Python.

---

## Why We Use It

So installing a package for FPL Assistant never breaks another project (or the OS).
Each project gets its own isolated set of dependencies — a core professional habit.

---

## Concepts

- **venv:** a folder (`venv/`) holding a project-local Python and its packages.
- **Activate:** switching your shell to use that local Python.
- **`requirements.txt`:** the list of packages the project needs, so the environment
  can be recreated anywhere.

---

## Examples

Creating and activating the environment (Session 1):

```bash
python3 -m venv venv
source venv/bin/activate
```

Verifying you're inside it:

```bash
which python     # should point inside the project's venv/ folder
python --version
```

---

## Commands

```bash
python3 -m venv venv          # create
source venv/bin/activate      # activate (macOS/zsh)
deactivate                    # leave the environment
pip install <package>         # install into the venv
pip freeze > requirements.txt # record installed packages
pip install -r requirements.txt  # recreate from the list
```

---

## Common Mistakes

- **Forgetting to activate** — packages install globally instead of in the venv.
  Check `which python` points inside `venv/`.
- **Committing the `venv/` folder to Git** — it shouldn't be tracked; add it to
  `.gitignore`. Commit `requirements.txt` instead.

---

## Best Practices

- One venv per project.
- Keep `requirements.txt` up to date so the environment is reproducible.

---

## Lessons Learned

- The venv is what makes "it works on my machine" reproducible on any machine.

---

## Related Documents

- [Chapter 3 — Python](./03_Python.md)
- [Journal — Session 1](../01_Journal/FPL_Assistant_Dev_Journal_Session1.md)
