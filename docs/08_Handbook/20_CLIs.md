# Chapter 20 — Command-Line Interfaces (CLIs)

**Badges:** 📖 🧪 💻

---

## Purpose

A CLI (command-line interface) lets you drive a program by typing commands. This
project uses one so the user can `refresh`, `table`, `search` and `filter` on demand.

---

## Why We Use It — and where it sits in the architecture

The CLI is the **interaction layer** — it sits on *top* of everything else. Its one
job is to decide *what the user asked for* and call the right pieces. It holds no FPL
logic itself. That thinness is deliberate: adding a new command doesn't touch the
layers below it (client, storage, analytics, display).

```
user types a command → CLI (routes) → calls the existing layers → prints the result
```

This is the same "add capability at the edge, leave the core untouched" idea that a
future web UI would use — the web layer would replace the CLI, and nothing beneath it
would change. (See [ADR-003](../06_Decisions/ADR-003-cli-approach.md).)

---

## Concepts

- **`argparse`:** Python's standard-library tool for reading command-line arguments.
- **Subcommand:** a named action under one program (`app.py table`, `app.py search`).
- **Handler:** the function a subcommand runs.
- **Dispatch:** matching the parsed command to its handler and calling it.
- **Positional vs optional args:** `search haaland` (positional) vs `table --limit 5`
  (optional).

---

## Examples (from this project)

The structure lives in `src/cli.py`. The key idea is that each subcommand is *wired*
to a handler, and `main` just parses and dispatches:

```python
def build_parser():
    parser = argparse.ArgumentParser(prog="fpl-assistant")
    sub = parser.add_subparsers(dest="command")

    p_table = sub.add_parser("table", help="Show stored players")
    p_table.add_argument("--limit", type=int, default=20)
    p_table.set_defaults(handler=cmd_table)   # ← wire command to its function
    ...
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    args.handler(args)                        # ← dispatch
```

Because commands are just parsed data, they're easy to **test** without running the
program — parse an argument list and check the shape.

---

## Commands

```bash
python app.py --help                             # list commands (with examples)
python app.py refresh                            # fetch + store (players, teams, fixtures)
python app.py table --sort value --limit 20      # players, ranked by points or value
python app.py search haaland                     # find players by name
python app.py filter --pos DEF --max-price 6     # narrow the player list
python app.py fdr --type custom --next 5         # teams by fixture difficulty (fpl or custom)
python app.py fixtures --team ARS --type custom  # a team's fixtures + difficulty
```

---

## Common Mistakes

- **Putting logic in the handler.** Handlers should stay thin and call the layers;
  the work belongs below (see `src/ingest.py`, `src/analytics/`).
- **Forgetting the no-command case.** If the user runs bare `app.py`, print help
  rather than doing nothing.

---

## Best Practices

- Keep the CLI a routing layer; no FPL logic in it.
- Prefer the standard library (`argparse`) until a real need justifies more.
- Make commands scriptable and testable (parse → assert), not interactive-only.

---

## Lessons Learned

- A CLI is just another entry point. The value of the layered design is that adding
  one (or four) commands didn't disturb the client/storage/display below.

---

## Related Documents

- [ADR-003 — CLI approach](../06_Decisions/ADR-003-cli-approach.md)
- [Architecture v0.1 §4](../03_Architecture/Architecture.md)
- [Chapter 21 — Analytics](./21_Analytics.md)
- Code: `src/cli.py`, `app.py`
