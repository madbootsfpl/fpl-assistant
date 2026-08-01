# Chapter 1 — Mac Development Environment

**Badges:** 📖 🧪 💻

---

## Purpose

How the Mac mini (Apple Silicon) is set up for software development, and the tools
that make it a working development machine rather than just a computer.

---

## Why We Use It

This is the machine the project is built on. Getting the foundation right —
correct Homebrew, correct Python, sensible defaults — avoids confusing problems
later (like the shell running the wrong Python, which we hit in Session 1).

---

## Concepts

- **Apple Silicon (arm64):** newer Macs use Apple's own chips. Native tools live in
  `/opt/homebrew` (older Intel Macs used `/usr/local`).
- **Homebrew:** the "missing package manager" for macOS — installs developer tools
  from the terminal.
- **PATH:** the list of folders the shell searches for commands. Which tool runs
  depends on PATH order.

---

## Examples

From Session 1, installing native Apple Silicon Homebrew and verifying it:

```bash
which brew        # → /opt/homebrew/bin/brew
```

---

## Commands

```bash
brew --version          # check Homebrew is installed
brew install <package>  # install a tool
brew list               # what's installed
which <command>         # show which program actually runs
```

---

## Common Mistakes

- **Wrong Homebrew for the chip** — installing the Intel build on Apple Silicon.
  Confirm the path is `/opt/homebrew`, not `/usr/local`.
- **Shell caching an old command location** — see the `hash -r` fix in
  [Chapter 3 (Python)](./03_Python.md) and [Chapter 16 (Debugging)](./16_Debugging.md).

---

## Best Practices

- Verify every install with `which` and `--version` — don't assume.
- Keep one machine setup documented (this chapter) so it can be reproduced.

---

## Lessons Learned

- The path a command resolves to matters as much as it being installed. `which`
  is your friend.

---

## Related Documents

- [Journal — Session 1 (Environment Setup)](../01_Journal/FPL_Assistant_Dev_Journal_Session1.md)
- [Chapter 2 — Terminal & Shell](./02_Terminal.md)
- [Chapter 3 — Python](./03_Python.md)
