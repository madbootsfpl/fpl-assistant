"""Value analytics — the project's first derived metric.

Points-per-£m answers a simple question: "how many points does each £1m of a
player's price buy?" It's the first number the app calculates rather than reads.
"""


def points_per_million(total_points, price):
    """Points per £1m of price.

    Returns None when the value is *undefined* — price missing or <= 0 — rather
    than inventing a number. A 0-price player isn't genuinely "worth zero", and
    dividing by zero has no answer, so we say "undefined" and let the caller show
    a dash and sort it last.
    """
    if total_points is None or not price or price <= 0:
        return None
    return total_points / price


def rank_players(rows, sort_by: str = "points") -> list[dict]:
    """Attach a `value` (points-per-£m) to each row, then sort.

    `rows` is a sequence of mappings (e.g. from Storage.get_players()). Returns a
    list of plain dicts. With sort_by="value", best value ranks first and
    undefined values sort to the bottom; otherwise rows are ranked by total points.
    """
    enriched = []
    for row in rows:
        data = dict(row)
        data["value"] = points_per_million(data.get("total_points"), data.get("price"))
        enriched.append(data)

    if sort_by == "value":
        # (has-value, value): the first element pushes None values to the bottom.
        enriched.sort(
            key=lambda d: (d["value"] is not None, d["value"] or 0.0),
            reverse=True,
        )
    else:
        enriched.sort(key=lambda d: d.get("total_points") or 0, reverse=True)

    return enriched
