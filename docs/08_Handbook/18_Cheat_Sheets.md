# Chapter 18 — Cheat Sheets

**Badges:** 💻

---

## Purpose

A quick-reference of the commands we actually use, so you don't have to hunt through
the other chapters mid-task. Only commands used on *this* project belong here.

---

## Terminal

```bash
pwd                 # where am I?
ls                  # list files
cd <folder>         # change directory
which <command>     # which program actually runs
hash -r             # forget cached command locations
clear               # clear the screen
```

---

## Python & Virtual Environments

```bash
python3 --version               # check Python version
python3 -m venv venv            # create a virtual environment
source venv/bin/activate        # activate it (macOS/zsh)
deactivate                      # leave it
which python                    # confirm it's the venv's Python
pip install <package>           # install into the venv
pip freeze > requirements.txt   # record dependencies
pip install -r requirements.txt # recreate the environment
```

---

## Homebrew

```bash
brew --version          # check Homebrew
brew install <package>  # install a tool
brew list               # what's installed
```

---

## Git

```bash
git status              # what's changed
git status --short      # compact view
git add -A              # stage everything
git commit -m "msg"     # commit
git log --oneline -5    # recent history
git diff                # unstaged changes
git branch              # list branches
```

---

## Related Documents

- [Chapter 2 — Terminal](./02_Terminal.md)
- [Chapter 4 — Virtual Environments](./04_Virtual_Environments.md)
- [Chapter 5 — Git](./05_Git.md)

*(Grow this sheet as new commands earn their place through real use.)*
