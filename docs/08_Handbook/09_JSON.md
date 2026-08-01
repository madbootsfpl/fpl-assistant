# Chapter 9 — JSON

**Badges:** 📖 🧪 💻

---

## Purpose

JSON (JavaScript Object Notation) is a structured text format for exchanging data.
The FPL API returns its data as JSON.

---

## Why We Use It — and where it sits in the architecture

JSON is the *shape* of the data as it arrives from the API. It sits between two
layers: the **client** hands us JSON, and the **mapping** step turns it into our
own tidy objects. We deliberately don't let raw JSON spread through the app —
we pick out the handful of fields we need and convert them once, at the edge.

```
API → raw JSON (dict/list) → from_api() maps the fields we want → Player/Team objects
```

---

## Concepts

- **Object `{}`** — key/value pairs (becomes a Python `dict`).
- **Array `[]`** — an ordered list (becomes a Python `list`).
- **Values** — strings, numbers, booleans, null, or nested objects/arrays.
- Python's built-in **`json`** module and `requests`' `.json()` convert JSON text
  into Python objects automatically — no manual parsing.

---

## Examples (from this project)

One raw player ("element") from `bootstrap-static`, trimmed to what we use:

```json
{
  "id": 2,
  "web_name": "B.Fernandes",
  "team": 16,
  "element_type": 3,
  "now_cost": 120,
  "total_points": 235
}
```

The interesting part is the **translation** in `src/models/player.py` — this is
where the API's quirks are handled once so the rest of the app never sees them:

```python
position = POSITION_MAP[raw["element_type"]]  # 3 → "MID"
price    = raw["now_cost"] / 10               # 120 → 12.0
```

So a raw JSON number like `element_type: 3` becomes a readable `"MID"`, and
`now_cost: 120` becomes `£12.0m`.

---

## Common Mistakes

- **Storing raw JSON everywhere.** It's tempting, but then every part of the app
  has to understand FPL's field names and quirks. We map once, at the edge.
- **Assuming every field exists.** We read only the small set we need, so an
  unexpected/changed field elsewhere in the payload can't break us.

---

## Best Practices

- Translate raw JSON into your own objects in one place (`from_api`).
- Keep the mapping next to the model, so the "meaning" of each field is obvious.

---

## Lessons Learned

- The JSON→object boundary is where messy external data becomes clean internal
  data. Getting that boundary right keeps the quirks contained.

---

## Related Documents

- [Chapter 8 — APIs](./08_APIs.md) · [Chapter 10 — SQLite](./10_SQLite.md)
- [Architecture v0.1 §5–§6](../03_Architecture/Architecture.md)
- Code: `src/models/player.py`, `src/models/team.py`
