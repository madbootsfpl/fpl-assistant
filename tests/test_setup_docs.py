"""No runbook may instruct a reader to re-open the tables the hardening closed.

⭐⭐ **The failure this exists for is silent and has already happened.** Stages A/B/B3 closed `beta_users`,
`squads`, `user_prefs`, `player_watchlist`, `beta_waitlist` and `events` to the publishable key. Nothing in
`docs/` changed — so `BETA.md`, `CLOUD_SQUADS.md` and `ANALYTICS.md` went on printing `create policy …
using (true)` and `disable row level security` as *setup instructions*. No test went red, because no code was
wrong. **The system was hardened and the manual still described the hole**, and the manual is what a person
follows when they rebuild the project or set up a second one.

⚠️ **This guard scans fenced ```sql blocks, not prose.** A blacklist of words would fire on the paragraphs
that *warn* against these statements — and the usual response to a guard that cries wolf is to weaken it
(ADR-178: *a word blacklist is not the same as "no word appears"*). What makes something dangerous here is
that it sits in a block a reader is told to paste.

⭐ **Everything under `docs/` is scanned by default**; exemptions are named individually below. ADR-184's
lesson was a guard that checked the two files someone thought of and missed six surfaces — so a new runbook
is covered the day it is written, without anyone remembering to add it.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Statements that hand a table to `anon` wholesale. Each is matched inside a ```sql fence only.
DANGEROUS = [
    (re.compile(r"\busing\s*\(\s*true\s*\)", re.I),
     "a `using (true)` policy makes the whole table readable with the publishable key"),
    (re.compile(r"\bwith\s+check\s*\(\s*true\s*\)\s*;?\s*$", re.I | re.M),
     "a `with check (true)` policy on a table holding user data"),
    (re.compile(r"\bdisable\s+row\s+level\s+security\b", re.I),
     "`disable row level security` removes the protection entirely"),
    (re.compile(r"\bgrant\s+(all|select)\b[^;]*\bto\s+[^;]*\banon\b", re.I),
     "granting `anon` a direct read re-opens enumeration"),
]

# ── Exemptions, each with a reason ────────────────────────────────────────────────────────────────────────
EXEMPT = {
    # The ADRs are the historical record of how the system got here. Rewriting one to match today would
    # destroy the thing it exists for. They are decisions, not instructions.
    "06_Decisions",
    # These three document the hardening itself: the "before" it removed, and a rollback block that has to
    # keep working at 2am. Their dangerous SQL is the subject matter.
    "SUPABASE_RLS.md",
    "SUPABASE_PRODUCTION_CUTOVER.md",
    "SUPABASE_STAGING.md",
    # Sprint records and journals are dated write-ups of what happened, same argument as the ADRs.
    "05_Sprints",
    "01_Journal",
}

SQL_FENCE = re.compile(r"```sql\n(.*?)```", re.S)


def _scanned_docs():
    for path in sorted((ROOT / "docs").rglob("*.md")):
        rel = path.relative_to(ROOT)
        if any(part in EXEMPT for part in rel.parts):
            continue
        yield rel, path


def test_the_scan_actually_covers_the_runbooks():
    """⭐ A sweep that matches nothing passes loudly. Pin that the three files this was written for are in it.

    ⚠️ ADR-178: *a test that skips is not a test that passes* — and a guard whose corpus quietly became empty
    is the same failure wearing a green tick.
    """
    scanned = {str(rel) for rel, _ in _scanned_docs()}
    for name in ("docs/BETA.md", "docs/CLOUD_SQUADS.md", "docs/ANALYTICS.md"):
        assert name in scanned, f"{name} must be scanned — it is a setup runbook"
    assert len(scanned) >= 10, "the corpus collapsed; the guard is no longer sweeping anything"


@pytest.mark.parametrize("rel,path", list(_scanned_docs()), ids=lambda v: str(v) if isinstance(v, Path) else "")
def test_no_runbook_tells_you_to_open_a_table(rel, path):
    text = path.read_text()
    for block in SQL_FENCE.findall(text):
        for pattern, why in DANGEROUS:
            hit = pattern.search(block)
            assert not hit, (
                f"\n🔴 {rel} contains a SQL block a reader is told to run, which would undo the hardening."
                f"\n   Found: {hit.group(0)!r}"
                f"\n   Why it matters: {why}."
                f"\n   Point at sql/setup.sql instead — see docs/SUPABASE_RLS.md.")


def test_the_runbooks_point_at_the_one_setup_file():
    """The positive half: they must not merely *lack* bad SQL, they must send you to the good file.

    ⭐ *Removing the wrong instruction is not the same as giving the right one* — a runbook with its SQL
    simply deleted leaves the reader with no way to create the tables at all.
    """
    for name in ("BETA.md", "CLOUD_SQUADS.md", "ANALYTICS.md"):
        text = (ROOT / "docs" / name).read_text()
        assert "sql/setup.sql" in text, f"docs/{name} must point the reader at sql/setup.sql"


def test_setup_sql_closes_every_table_it_creates():
    """The file's own claim, checked statically so it holds even without a Postgres to run it against.

    (`tests/test_setup_sql.py` proves the behaviour on a real database; this proves the *file* still says so
    when that suite is skipped — which is every local run without MADBOOTS_TEST_DSN.)
    """
    sql = (ROOT / "sql" / "setup.sql").read_text()
    for table in ("beta_users", "squads", "user_prefs", "player_watchlist", "beta_waitlist", "events"):
        assert re.search(rf"revoke all on public\.{table}\s+from anon", sql), (
            f"{table} is created but never revoked from anon")
    # maddie_videos is the deliberate exception: public marketing content, readable and never writable.
    assert "grant select on public.maddie_videos to anon" in sql
    assert not re.search(r"grant\s+(insert|update|delete|all)\s+on public\.maddie_videos", sql)
