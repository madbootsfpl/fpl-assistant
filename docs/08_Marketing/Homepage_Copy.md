# madboots.com — homepage copy deck

**Audited:** 2026-08-27 against the live page and the live app.
**Status:** ⚠️ **Apply by hand.** The homepage source is **not in this repo** (Cloudflare Pages), so this is a
paste-ready deck, not a deploy. Point me at the source and I'll edit it properly.

---

## First: the roadmap item was already fixed

The backlog said the page still read *"No login to look around · your squad saves across devices by a
handle"*, untrue since Google auth went live on 2026-08-12. **That line is not on the page.** It now reads:

> 🔒 Invite-only beta — Free · email-only sign-in · your data stays yours · a personal project.

> Sign in with Google — your squad saves to your account and syncs across your devices. Private beta: new
> sign-ins join the waitlist.

Both are accurate today, including for the ADR-147/148 cross-device preferences. It was fixed in the
2026-08-18 site audit and the roadmap entry outlived the problem. **Roadmap item closed on that basis, and the
real staleness is below** — which is a different thing entirely.

---

## What is actually stale: the feature list

*"What's inside"* predates four surfaces and two renames. Everything in the hero, the "Why MADBOOTS" trio and
the footer checks out; this one grid does not.

| on the page now | reality |
|---|---|
| **Fixtures** — a difficulty ticker + who to target | renamed **🧬 Team DNA & FDR** (ADR-134) and it leads with a 20-club strength scan, not the ticker |
| **Squad optimiser** — a legal 15 to your budget | renamed **🧪 Squad Lab** (ADR-105) |
| — | **🏆 Leagues** missing entirely |
| — | **📡 Signals** missing entirely |
| — | **📈 Trending** missing entirely |
| Players · Transfers · Captain · Ask | accurate, keep as-is |

### Replacement grid

Written to match the existing voice — a name, an em dash, one plain claim, no adjectives.

- **Players** — the whole pool, sortable stats
- **Team DNA** — how strong every club is at both ends, then the week-by-week difficulty ticker
- **Signals** — injuries, news and crowd moves, most reliable first
- **Transfers** — the best swaps by XI gain
- **Captain** — who to armband, with the why
- **Squad Lab** — a legal 15 to your budget
- **Leagues** — import your mini-league by id, or scan the elite
- **Ask** — plain-English questions, grounded answers

**If the grid is fixed at six**, drop *Trending* (already implied by Signals) and fold *Captain* into
*Transfers* as **"Transfers & captain — the best swaps by XI gain, and who to armband"**. Keep **Signals** in
whatever happens: press-plus-crowd departure detection is the most distinctive thing in the app and nothing on
the homepage hints it exists.

---

## Not verified — owner action

**`hello@madboots.com` must be a real inbox.** The footer carries an obfuscated mailto, so the *link* exists;
whether mail sent to it arrives anywhere is not something this audit can check. A contact address that
silently discards a beta tester's reply is worse than no address at all.

---

## The rule this deck exists to enforce

**Marketing copy is a claim about the product, and it goes stale silently.** Nothing broke when Leagues and
Signals shipped — the page simply stopped describing the app, and the only signal was a backlog entry that had
itself gone out of date. Worth re-reading this page at each rename or new surface, which is cheaper than
re-auditing it every few months.
