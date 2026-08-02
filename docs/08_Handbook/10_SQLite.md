# Chapter 10 — SQLite

**Badges:** 📖 🧪 💻

---

## Purpose

SQLite is a small database stored in a single local file. It's how the project
stores player and team data locally instead of re-fetching from the API every time.

---

## Why We Use It — and where it sits in the architecture

SQLite is the **storage** layer — the middle of the pipeline. It sits between
ingestion (which fills it) and presentation (which reads from it). This is what
makes "fetch once, read locally" possible: once data is saved, the app doesn't
need the internet to show it.

```
map → Storage.save_*()  →  data/fpl.db  →  Storage.get_players() → display
```

The storage layer knows about SQLite but nothing about HTTP or the screen — that
isolation is the whole point of the design.

---

## Concepts

- **Table:** rows and columns. We have `teams` and `players`.
- **Primary key:** a column that uniquely identifies a row — the FPL `id`.
- **Upsert:** insert a row, or update it if the id already exists. This is what
  makes re-running the app *refresh* data instead of duplicating it.
- **Parameterised query:** passing values with `?` placeholders (never string-
  building SQL) — safe and correct.
- **JOIN:** combining tables. A `LEFT JOIN` keeps a player even if its team is missing.
- **Migration:** bringing an *existing* database up to a new schema. `CREATE TABLE IF
  NOT EXISTS` won't change a table that already exists, so new columns are added with
  `ALTER TABLE ADD COLUMN`.
- **`sqlite3`:** Python's built-in module — no install needed.

---

## Examples (from this project)

The upsert that makes refreshes idempotent (`src/storage.py`):

```sql
INSERT INTO players (id, web_name, team_id, position, price, total_points)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    web_name = excluded.web_name,
    price = excluded.price,
    total_points = excluded.total_points
```

Reading players back with their team's short name via a join:

```sql
SELECT p.*, t.short_name AS team
FROM players p
LEFT JOIN teams t ON p.team_id = t.id
ORDER BY p.total_points DESC
```

**Proof it works:** running `python app.py` twice both times reported
"564 players / 20 teams" — the upsert refreshed rather than duplicated.

Evolving the schema — adding columns to a table that already has data (Sprint 004):

```python
# CREATE TABLE IF NOT EXISTS won't alter an existing table, so add missing columns.
existing = {row[1] for row in conn.execute("PRAGMA table_info(teams)")}
for column, col_type in NEW_COLUMNS.items():
    if column not in existing:
        conn.execute(f"ALTER TABLE teams ADD COLUMN {column} {col_type}")
```

This ran on the real `data/fpl.db`: a `teams` table of `[id, name, short_name]` gained
`strength_overall_home/away` on the next startup, with no data lost. Idempotent — it
only adds columns that are missing. Sprint 005 generalised it to a
`{table: {column: type}}` map, so the *same* mechanism migrates any table (teams, then
players) — a pattern used twice, made reusable.

---

## Commands

```bash
sqlite3 data/fpl.db "SELECT web_name, total_points FROM players LIMIT 5;"
```

---

## Common Mistakes

- **Building SQL with string formatting** (injection risk) — always use `?` placeholders.
- **Saving players before teams** — players reference a team, so teams go first.
- **Committing the `.db` file** — it's a generated cache; `data/*.db` is gitignored.

---

## Best Practices

- Upsert on a stable id so re-runs are idempotent.
- Wrap saves in a transaction (commit on success, roll back on error).
- Store only the fields you use; design the schema so a later PostgreSQL move is a
  storage-layer swap, not a rewrite.

---

## Lessons Learned

- Upsert + a stable id is a simple, powerful pattern: the app can re-fetch as often
  as it likes and the database stays clean.

---

## Related Documents

- [Architecture v0.1 §6 (Data model)](../03_Architecture/Architecture.md)
- [Chapter 9 — JSON](./09_JSON.md)
- Code: `src/storage.py`
