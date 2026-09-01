#!/usr/bin/env python3
"""Swap the Maddie intro video on madboots.com — one command instead of a hand-edit.

    python scripts/swap_intro_video.py https://youtu.be/NEW_ID

The site lives at ~/madboots-site/index.html and is **not** a git repo, so a bad hand-edit has no undo.
This backs up first (outside the deploy folder, so the backup is never published), replaces the id in
**both** places it appears, and refuses to write unless it found exactly the two it expected.

Accepts any YouTube form — youtu.be/ID, watch?v=ID, /embed/ID, or a bare 11-character id.
"""

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

SITE = Path.home() / "madboots-site" / "index.html"
BACKUPS = Path.home() / "madboots-site-backups"      # NOT inside the deploy folder — see ADR-note below
ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
EXPECTED_SITES = 2                                    # the lightbox comment + the mbPlay() iframe src


def extract_id(text: str) -> str:
    """The 11-character id from any YouTube URL form, or the id itself."""
    for pattern in (r"youtu\.be/([A-Za-z0-9_-]{11})",
                    r"[?&]v=([A-Za-z0-9_-]{11})",
                    r"/embed/([A-Za-z0-9_-]{11})"):
        if m := re.search(pattern, text):
            return m.group(1)
    if ID_RE.fullmatch(text.strip()):
        return text.strip()
    raise SystemExit(f"✗ Could not find a YouTube id in {text!r} — pass a youtu.be/… URL or the bare id.")


def current_id(html: str) -> str:
    """The id the page plays today — read from the iframe, the one that actually matters."""
    m = re.search(r"youtube\.com/embed/([A-Za-z0-9_-]{11})", html)
    if not m:
        raise SystemExit("✗ No embed id found in index.html — has the lightbox markup changed?")
    return m.group(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Swap the Maddie intro video on madboots.com")
    ap.add_argument("url", help="the new YouTube URL (or bare 11-char id)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    args = ap.parse_args()

    if not SITE.exists():
        raise SystemExit(f"✗ {SITE} not found. The site is outside the repo — is it somewhere else?")

    html = SITE.read_text()
    old, new = current_id(html), extract_id(args.url)
    if old == new:
        print(f"Nothing to do — the page already plays {new}.")
        return

    found = html.count(old)
    if found != EXPECTED_SITES:
        raise SystemExit(f"✗ Expected {EXPECTED_SITES} occurrences of {old}, found {found}. "
                         "The markup has changed — swap it by hand and update this script.")

    print(f"  {old}  →  {new}   ({found} places: the lightbox comment + the iframe src)")
    if args.dry_run:
        print("  --dry-run: nothing written.")
        return

    BACKUPS.mkdir(exist_ok=True)
    backup = BACKUPS / f"index.html.bak-{date.today()}"
    shutil.copy2(SITE, backup)
    SITE.write_text(html.replace(old, new))

    after = SITE.read_text()
    assert after.count(new) == EXPECTED_SITES and old not in after
    print(f"✓ Swapped. Backup: {backup}")
    print("\nNext:")
    print(f"  1. open {SITE} in a browser and click 'See how it works' — the new clip should play")
    print("  2. drag ~/madboots-site to Cloudflare Pages")
    print("  3. hard-refresh madboots.com and check the hero tagline + the video")


if __name__ == "__main__":
    sys.exit(main())
