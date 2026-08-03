# FPL Assistant Developer Handbook

**Project:** FPL Assistant

**Owner:** Tony Sheridan

**Technical Mentor:** ChatGPT

**Version:** 1.0

---

# Purpose

This handbook documents the knowledge, tools, conventions and working practices used throughout the FPL Assistant project.

Unlike a programming book, this handbook only contains technologies, techniques and lessons that have been used within this project.

It serves as both:

- a personal reference guide
- a record of the learning journey

The handbook should evolve throughout the lifetime of the project.

---

# Guiding Principles

This handbook follows a few simple principles.

## Learn by Building

Knowledge is retained far better when learned through solving real problems.

Every chapter should relate back to something implemented within the project.

---

## Keep It Practical

Avoid long theoretical explanations.

Explain things simply.

Include examples.

Include commands.

Include common mistakes.

---

## Explain the Why

Don't simply document *what* to do.

Document *why* it is done that way.

---

## Future Tony

Assume you will return to this project after six months.

Everything should be understandable without needing to remember previous sessions.

---

# Progress Badges

Each chapter carries a row of badges showing how far the learning has gone. Add
badges to a chapter as they become true — you should be able to *watch your skills
grow* chapter by chapter.

| Badge | Meaning                        |
| ----- | ------------------------------ |
| 📖    | Read about it                  |
| 🧪    | Tried it                       |
| 💻    | Used it in the project         |
| 🧠    | Confident enough to explain it |
| ⭐     | Best practice understood       |

A chapter's badge line is a simple left-to-right progression, e.g. Git might show
`📖 🧪 💻 🧠 ⭐` while FastAPI (not built yet) shows just `📖`.

---

# Handbook Structure

| Chapter | Topic | Badges | Status |
|---------|-------|--------|--------|
| 1 | [Mac Development Environment](./01_Mac_Development.md) | 📖 🧪 💻 | In progress |
| 2 | [Terminal & Shell](./02_Terminal.md) | 📖 🧪 💻 | In progress |
| 3 | [Python](./03_Python.md) | 📖 🧪 💻 | In progress |
| 4 | [Virtual Environments](./04_Virtual_Environments.md) | 📖 🧪 💻 | In progress |
| 5 | [Git](./05_Git.md) | 📖 🧪 💻 🧠 | In progress |
| 6 | [GitHub](./06_GitHub.md) | 📖 🧪 💻 | In progress |
| 7 | [Visual Studio Code](./07_VS_Code.md) | 📖 🧪 💻 | In progress |
| 8 | [APIs](./08_APIs.md) | 📖 🧪 💻 | In progress |
| 9 | [JSON](./09_JSON.md) | 📖 🧪 💻 | In progress |
|10 | [SQLite](./10_SQLite.md) | 📖 🧪 💻 | In progress |
|11 | [Testing](./11_Testing.md) | 📖 🧪 💻 | In progress |
|12 | [FastAPI](./12_FastAPI.md) | 📖 | Not started |
|13 | [Claude Code](./13_Claude_Code.md) | 📖 🧪 💻 | In progress |
|14 | [ChatGPT](./14_ChatGPT.md) | 📖 🧪 💻 | In progress |
|15 | [Prompt Engineering](./15_Prompt_Engineering.md) | 📖 🧪 | In progress |
|16 | [Debugging](./16_Debugging.md) | 📖 🧪 | In progress |
|17 | [Software Engineering Principles](./17_Best_Practices.md) | 📖 🧪 💻 | In progress |
|18 | [Cheat Sheets](./18_Cheat_Sheets.md) | 💻 | In progress |
|19 | [Glossary Index](./19_Glossary_Index.md) | 💻 | In progress |
|20 | [CLIs](./20_CLIs.md) | 📖 🧪 💻 | In progress |
|21 | [Analytics](./21_Analytics.md) | 📖 🧪 💻 | In progress |
|22 | [Optimisation (Linear Programming)](./22_Optimisation.md) | 📖 🧪 💻 | In progress |
|23 | [External Data & Graceful Degradation](./23_External_Data.md) | 📖 🧪 💻 | In progress |
|24 | [Expected Goals (xG / xA / xGI)](./24_Expected_Goals.md) | 📖 🧪 💻 | In progress |
|25 | [Defensive Contribution (DefCon)](./25_Defensive_Contribution.md) | 📖 🧪 💻 | In progress |

Update the badges and status as each chapter grows.

---

# Every Chapter Should Contain

Each chapter should follow the same structure.

## Purpose

What is this technology?

---

## Why We Use It

Why was it chosen for this project?

---

## Concepts

Key ideas explained simply.

---

## Examples

Real examples taken from this project.

---

## Commands

Useful commands.

---

## Common Mistakes

Typical beginner problems.

---

## Best Practices

Recommended approaches.

---

## Lessons Learned

Insights gained while using it.

---

## Related Documents

Links to Architecture, Decisions, Journal entries and Sprint documentation.

---

# Keeping This Handbook Updated

Whenever one of the following happens, update the relevant chapter:

- Learn a new command
- Discover a useful shortcut
- Solve a difficult bug
- Adopt a new tool
- Change the architecture
- Learn a better approach
- Make a mistake worth remembering

---

# Golden Rule

> If Future Tony would benefit from knowing it again, add it to the handbook.

---

# Final Thought

The aim of this handbook is not to become an encyclopedia.

Its purpose is to become **my personal software engineering reference**, built through experience rather than copied from documentation.

Every page should answer one simple question:

> **"If I had to build this project again in a year's time, what would I wish I'd written down?"**
