# Chapter 2 — Terminal & Shell

**Badges:** 📖 🧪 💻

---

## Purpose

The terminal is where we run commands, and the shell (zsh on this Mac) is the
program that interprets them. Almost everything in this project starts here.

---

## Why We Use It

It's the fastest, most precise way to control the machine: run Python, use Git,
manage the virtual environment, install packages. Documenting the handful of
commands we actually use beats memorising hundreds we don't.

---

## Concepts

- **Shell:** the command interpreter. This Mac uses **zsh**.
- **Working directory:** the folder the terminal is "in" right now.
- **PATH:** folders searched for commands (see [Chapter 1](./01_Mac_Development.md)).
- **`hash -r`:** clears the shell's memory of where commands live — needed after
  installing a new version of something already on PATH.

---

## Examples

Checking which Python the shell will run (Session 1):

```bash
which python3
python3 --version
```

---

## Commands

```bash
pwd                 # print working directory (where am I?)
ls                  # list files
cd <folder>         # change directory
which <command>     # which program runs for this command
hash -r             # forget cached command locations
clear               # clear the screen
```

---

## Common Mistakes

- Running a command from the wrong directory (check with `pwd`).
- Expecting a newly installed tool to be picked up immediately — the shell may
  have cached the old one (`hash -r` fixes it).

---

## Best Practices

- When something behaves unexpectedly, first confirm *where* you are (`pwd`) and
  *what* you're running (`which`).

---

## Lessons Learned

- Small terminal habits (`pwd`, `which`) prevent a lot of confusion.

---

## Related Documents

- [Chapter 1 — Mac Development Environment](./01_Mac_Development.md)
- [Chapter 5 — Git](./05_Git.md)
- [Chapter 18 — Cheat Sheets](./18_Cheat_Sheets.md)
