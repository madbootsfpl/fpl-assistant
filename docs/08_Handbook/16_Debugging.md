# Chapter 16 — Debugging

**Badges:** 📖 🧪

---

## Purpose

Debugging is the process of working out *why* something isn't behaving as expected,
and fixing it. This chapter collects real problems solved on the project.

---

## Why We Use It

Every project hits surprises. Writing down how each one was solved means the next
time it happens (to you or "future Tony"), the fix takes minutes not hours.

---

## Concepts

- **Reproduce first:** confirm the exact wrong behaviour before changing anything.
- **Check assumptions:** "installed" ≠ "the one that runs" (see below).
- **Change one thing at a time**, then re-check.

---

## Solved problems log

### The wrong Python ran (Session 1)

- **Symptom:** `python3 --version` showed 3.10.4 even though Homebrew Python 3.14
  was installed.
- **Cause:** the shell had cached the old command location on its PATH.
- **Fix:**
  ```bash
  hash -r
  which python3     # re-check it now points at /opt/homebrew/bin/python3
  python3 --version # Python 3.14.6
  ```
- **Lesson:** after installing a new version of an existing command, clear the
  shell's cache with `hash -r` and verify with `which`.

*(Add new entries here as bugs are solved — each with Symptom → Cause → Fix → Lesson.)*

---

## Best Practices

- Keep a log (this chapter). A solved bug is only valuable if it's written down.
- Verify the fix, don't assume it (`which`, `--version`, re-run).

---

## Related Documents

- [Chapter 1 — Mac Development](./01_Mac_Development.md)
- [Chapter 3 — Python](./03_Python.md)
- [Bug Report Template](../07_Templates/Bug_Report_Template.md)
