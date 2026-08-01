# Chapter 7 — Visual Studio Code

**Badges:** 📖 🧪 💻

---

## Purpose

VS Code is the code editor (IDE) used for the project — where files are written,
edited, and navigated.

---

## Why We Use It

Chosen in the Project Charter: free, popular, excellent Python and Git support, and
a large extension ecosystem. It's also a learning goal in its own right.

---

## Concepts

- **Workspace:** the project folder opened in VS Code.
- **Integrated terminal:** a terminal built into the editor (same commands as
  [Chapter 2](./02_Terminal.md)).
- **Extensions:** add-ons (e.g. Python) that add language features.
- **Interpreter selection:** VS Code should point at the project's `venv/` Python
  (see [Chapter 4](./04_Virtual_Environments.md)).

---

## Examples & Commands

To be expanded as we use more features. Early useful moves:

- Open the project: `code .` from the project folder (if the `code` command is set up)
- Use the integrated terminal for Git and Python instead of a separate window

---

## Common Mistakes

- VS Code using the wrong Python interpreter — make sure it's set to the venv, or
  tests and imports behave differently from the terminal.

---

## Best Practices

- Point VS Code at the project venv so the editor and terminal agree.

---

## Lessons Learned

*(To be filled as the project grows.)*

---

## Related Documents

- [Chapter 2 — Terminal & Shell](./02_Terminal.md)
- [Chapter 4 — Virtual Environments](./04_Virtual_Environments.md)
