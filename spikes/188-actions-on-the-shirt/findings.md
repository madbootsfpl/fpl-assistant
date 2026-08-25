# Spike 188 — actions on the shirt

**Date:** 2026-08-25 · **Timebox:** ~1 hour · **Verdict: the mechanism works. It buys about half the clutter,
not all of it — and the half it can't buy is worth knowing before designing.**

**The goal is less page, not more interaction.** A popup that doesn't shrink the page has failed.

---

## Does one tap carry both the action and the player?

Yes.

```
returned → cap:4      →  Make captain → Saka
returned → sub:4      →  Substitute   → Saka
returned → sel:4      →  Select — open the card
```

`click_detector` returns *"the id of the last link clicked on"* as a **string**, from **any** anchor in the
markup — so `cap:123` encodes both halves. No new dependency; this is the component already shipped for
tap-the-pitch (ADR-133).

**One structural constraint, and it is the only real change needed.** HTML forbids `<a>` inside `<a>` — a
browser silently closes the outer one — so the card **cannot stay wrapped in a single anchor** if the actions
are to be individually clickable. The select-anchor and the action anchors have to be **siblings**:

```html
<div class="kit">
  <a id="sel:4" class="kit-hit"> …name · xP · meta… </a>   ← select
  <div class="acts">
    <a id="cap:4">©</a> <a id="sub:4">🔁</a> <a id="cmp:4">⚔️</a>   ← siblings, not children
  </div>
</div>
```

Verified: no nesting, four distinct ids per card.

---

## What it would actually take off the page

Measured on My Squad with a player selected — **six or seven widgets exist purely to act on one player**:

| widget | fate |
|---|---|
| `Select a player` selectbox | **removable as the primary path** — tapping the name does it (it stays as the accessible/testable fallback, per ADR-133) |
| `👑 Make X captain` button | **removable** — © on the shirt |
| `🔁 Bring/Take X …` selectbox | **removable for on-pitch swaps** — 🔁 then tap the other shirt |
| `Substitute →` confirm button | **removable** — the second tap *is* the confirm |
| `⚔️ Boot Battle — pool` segmented | **stays** — see below |
| `⚔️ compare with…` selectbox | **stays** for off-pitch targets |
| `Club` selectbox (pool = By club) | **stays** |

So roughly **three to four widgets come off**, each about 76-90px of vertical space on a phone once its label
is counted — call it **250-350px reclaimed**, against an 844px screen. That is the density complaint (US-423)
addressed at its source rather than by shrinking captions.

### The half it cannot buy, and why that matters

**You can only tap what is on the pitch.** Boot Battle's whole point is comparing against players you *don't*
own — All, By club — and no amount of shirt-level interaction reaches them. The same is true of any "bring in
X" flow. So the pickers do not disappear; they stop being the *default* path and become the discovery path.

That is worth designing around rather than discovering later: **the shirt owns actions on players you have;
the pickers own finding players you don't.** A design that tries to move everything onto the shirt will end up
re-adding a picker in a worse place.

---

## The same pattern, one level up

The goal named "player **or team or entity**". The league scan on 🧬 Team DNA & FDR is already a row per club,
and its drill-down is a selectbox below it — the identical shape. A `sel:ARS` anchor on the row would replace
that selectbox with a tap, for the same reason and the same cost. Worth doing in the same change so the idiom
is consistent, rather than a pitch that taps and a table that doesn't.

---

## Recommendation

Worth building, **gated as a density change with a measured before/after**, not as an interaction feature. The
ADR should state the target in reclaimed pixels and widgets removed, so it can be judged against the thing that
motivated it.

Two design calls belong in that gate:

1. **Do the actions show always, or on hover/tap?** Always-visible is one tap and honest on mobile; hidden is
   cleaner at rest but adds a tap and reintroduces a desktop-only idiom — which is what the hover card already
   is, and half the complaints have been mobile.
2. **How does the second tap of a two-tap flow (🔁, ⚔️) get cancelled?** A flow you can enter and not leave is
   worse than a picker.

Not in scope: reaching off-pitch players from the shirt. It cannot be done and the design should say so.
