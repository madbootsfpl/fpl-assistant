# ADR-263 — Feedback you can act on

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner, once the sink finally worked — *"get the feedback - dont have an email to respond
too in the feedback - is that expected?"*
**Follows:** ADR-262 (getting it delivered at all), ADR-231 (the relay)

---

## Context

Yes, expected — the screen had **one** field, the message. `contact` existed all the way through the
request, the payload and the Sheet column, and nothing ever filled it.

⭐ **A closed beta runs on replies.** A report you cannot answer is a bug you cannot ask a question about,
and the tester never learns whether it mattered.

## ⚠️ And a second defect the first one uncovered

The screen sent the literal string `'mobile'` as the location of **every** report — while its own copy
read:

> *"Screen and app version travel with it, so you do not have to describe where you were."*

⭐⭐ **The false promise was the reason nobody added the detail by hand.** A tester reads that and
reasonably stops describing where they were; the app then discards exactly that. ⚠️ *A UI claim that is
wrong is worse than a missing feature, because it suppresses the workaround.*

## Decisions

**1. An optional address, labelled by what it buys.** *"Email, so we can reply (optional)"* — ⭐ *"Email
(optional)" asks for data; "so we can reply" says why it is worth giving.*

**2. It is remembered.** ⚠️ *The cost of asking is paid per report; the cost of remembering is paid once* —
an optional field that must be retyped every time is one that gets filled in once. Saved **before** the
send, because a tester whose report fails still typed it. Blank **clears** rather than being ignored: a
tester removing their address means it.

**3. The report names the screen the tester was actually on.** `_lastScreen` is updated by both the tab bar
and the pushed routes, ⚠️ *because missing either would make the value confidently stale, which is worse
than blank.* Feedback deliberately does not record itself — ⭐ *it is the one route that is never what a
report is about, and letting it overwrite would erase the answer on the way to asking the question.*

**4. The copy now states what it will send** — *"Sent as a report about Signals, with the app version."*
⭐ *A promise the reader can check is worth more than one they must take on trust*, and this one had been
false. With no screen known it names the app rather than inventing one: ⚠️ *an invented location is worse
than none, because it is believed.*

**5. The Apps Script sets `replyTo`** — hitting Reply answers the tester rather than yourself.

📌 **Device-local**, like the draft (ADR-260) and the seen set (ADR-232): a convenience about this handset,
not a record about a person.

## ⚠️ A test that passed for the wrong reason

*"The address is remembered"* passed **with the save deleted entirely**. `pumpWidget` reuses the `State`
when the widget type and position are unchanged, so the second pump kept the first one's
`TextEditingController`. ⭐ *It was asserting that a controller holds its own text, which nothing has ever
doubted.* A `UniqueKey` forces a genuinely new screen, which is what *"next time"* means.

⚠️⚠️ **Found by mutation, not review** — and only after a second fault: the restore step used `git
checkout` on a file that was **new and untracked**, so one mutation silently stayed in the tree and its
result was void. ⭐ *A mutation harness that cannot restore is a harness that reports fiction.*

## Verification

* **7 Dart tests** reading the **request the client actually sent** — ⚠️ stubbing `feedback()` would have
  skipped `_post`, which is exactly where a field silently fails to serialise (ADR-241's lesson).
* **5/5 mutations killed**, two of them only after the test flaw above was fixed.
