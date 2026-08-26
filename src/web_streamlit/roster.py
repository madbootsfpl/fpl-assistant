"""Admin — who is actually testing (ADR-120).

The analytics are anonymous **by design** (a random session id and a random device id; no emails, no user keys,
no IPs — ADR-100). So the Admin page can say *"12 returning devices this week"* and cannot say *who*.

The privacy-respecting answer is a **separate join over data the owner already owns** — the `beta_users`
allow-list they maintain, against the account store's `updated_at` — never a de-anonymisation of an event. This
lives in its own module for exactly that reason: `analytics.py` stays anonymous-only, and the boundary is
structural rather than a comment.

**What it measures, and does not.** A tester appears as active only if they signed in *and* their squad
persisted. Someone who browses signed-out is invisible here, which is why the Admin page shows this **beside**
the anonymous totals: named engaged users next to overall usage.
"""

from datetime import datetime, timedelta, timezone

ACTIVE_DAYS = 7        # "active" = persisted a squad within the last week — roughly a gameweek's cadence
DORMANT_DAYS = 30      # beyond this a signed-up tester has effectively stopped


def _parse(ts):
    """An ISO timestamp from Supabase → an aware datetime, or None if absent/unparseable."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def classify(last_active, now, *, active_days: int = ACTIVE_DAYS, dormant_days: int = DORMANT_DAYS) -> str:
    """A tester's state: `active` · `dormant` · `lapsed` · `never`.

    `never` is its own state rather than the far end of dormant — a tester who has never signed in is a
    different problem (an unsent invite, a broken link) from one who signed in and drifted away.
    """
    dt = _parse(last_active)
    if dt is None:
        return "never"
    age = now - dt
    if age <= timedelta(days=active_days):
        return "active"
    return "dormant" if age <= timedelta(days=dormant_days) else "lapsed"


def days_since(last_active, now):
    dt = _parse(last_active)
    return None if dt is None else max(0, (now - dt).days)


def build(emails, updated_by_handle, key_for, now=None, seen_by_email=None) -> list[dict]:
    """The roster: one row per allow-listed email, most recently active first.

    `key_for` hashes an email to its account handle (`auth.user_key`) — passed in so this module never needs to
    know how identity is derived, and so the whole thing is testable without Supabase or Streamlit.

    **Two different signals, and telling them apart is the point (ADR-142).**

    * `seen_by_email` — when they last **signed in**. This is "used the app", and it is what status is judged
      on whenever it is available.
    * `updated_by_handle` — when they last **saved a squad**. Kept as its own column because it is genuinely
      interesting (who is actively managing a team, not just visiting), but it is a terrible proxy for use:
      most people browse and never press save. Judging activity on it reported 18 of 25 testers as "never"
      while at least two were using the app daily.

    With no sign-in data (the column not yet added), status falls back to the save time — the old behaviour,
    so the panel degrades to what it did before rather than showing everyone as never-seen.

    Never-signed-in testers sort last: the list is for spotting who has gone quiet, and a column of blanks at
    the top would bury that.
    """
    now = now or datetime.now(timezone.utc)
    rows = []
    for email in emails or []:
        saved = (updated_by_handle or {}).get(key_for(email))
        seen = (seen_by_email or {}).get(email)
        basis = seen or saved
        rows.append({"email": email, "last_active": basis, "last_seen": seen, "last_saved": saved,
                     "status": classify(basis, now), "days": days_since(basis, now)})
    order = {"active": 0, "dormant": 1, "lapsed": 2, "never": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["days"] if r["days"] is not None else 10**6, r["email"]))
    return rows


def totals(rows) -> dict:
    """Headline counts for the roster — how many testers are actually testing."""
    out = {"active": 0, "dormant": 0, "lapsed": 0, "never": 0}
    for r in rows or []:
        out[r["status"]] += 1
    out["registered"] = len(rows or [])
    return out
