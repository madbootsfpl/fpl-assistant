# Sprint 189: Actions on the entity — met the target, reverted anyway (ADR-135)

**Dates:** 2026-08-25
**Status:** ↩️ **Reverted, owner-verified on Cloud.** 1297 → 1294 tests, ruff clean. ADR-133 (tap-to-select)
survives and is live.

> **Owner:** set the goal, gated the ADR, reviewed the shipped thing on desktop and iPhone, called it worse,
> and approved the revert the same day. Verified the revert on Cloud: *"looks much better on cloud, tap works
> and no mess. tap has teal outline and populates the panel below with 👑 / 🔁 / ⚔️."*

---

### 🔍 Why this sprint exists

The owner's framing, which is the standard the work should be judged against:

> Reduce as much clutter on each page so it can be embedded in the player / the team / the entity. This will
> reduce the real estate needed and improve the experience on both mobile and desktop. **We are not doing this
> because we can.**

Measured on the live page with a player selected, **six or seven widgets below the pitch existed purely to act
on one selected player**, at roughly 76-90px each. ADR-133 had just shipped the input that made another
arrangement possible: a tap already resolves to a player id.

### 🔧 What shipped, and what happened to it

The shirt grew a labelled menu — Make captain · Substitute · Compare — on the selected card only, with an
*armed* state for the two-tap flows. It worked, and it **hit its number exactly: 6-7 widgets → 3**, the three
being the discovery pickers ADR-135 predicted would stay (you cannot tap a player who isn't on your pitch).

Then the owner used it:

> *"I think we are making the user experience worse… the hover is following the players around, so now I can
> see one player whom I am going to captain, and stats on another. It is slow, takes too much time to process a
> double click and have moved on — then the mess. Boot Battle is still not called."*

---

### 🐛 Three causes; only two were mine to fix

1. **The hover suppression was one selector too narrow.** `.kit.selected .kit-pop{display:none}` hid the
   popover on the *selected* card — every **other** shirt still popped on hover, right next to the open menu.
   The screenshot showed one player's menu beside a different player's stats. Fixable.
2. **Boot Battle's state wiring never took.** Fixable.
3. **The latency is architectural.** Every tap is a full Streamlit rerun, and the rerun recomputes
   `decision_xp` for the squad. A menu that opens on one round-trip and completes on a second costs **two**.
   FFH and fplapex feel instant because they are client-side apps; we are not, and no CSS closes that gap.

The third is the one that decided it. **A floating menu advertises the responsiveness of a client-side app and
then fails to deliver it** — which is exactly why it read as *"slow… then the mess"*, while the plain picker
below the pitch, doing the same work at the same speed, never did.

---

### 💡 The lesson

**Widget count was a proxy for clutter, and it turned out to be a bad one.** Three fast, legible controls beat
one control that opens a menu you wait for and that collides with the surface next to it.

> **A measured target that hits and still makes the thing worse means the metric was wrong, not the
> measurement.**

This is worth more than the feature was. The measurement was honest, the build was correct, the target was
met — and the answer was still no. Anyone who counts widgets on this page in future will find that written
down next to the number, in ADR-135 §Outcome and in the test that used to enforce it.

Two smaller lessons, both about prior work:

- **The design was gated properly and still went wrong.** The gate catches *unagreed* work; it does not catch
  *wrong* work. Only using the thing catches that. Same-day owner review on a real device is what saved this,
  and it is cheap.
- **Reverting is not the same as deleting.** ADR-135 keeps its status as reverted-with-reasons rather than
  vanishing, because the queued follow-on (ADR-134's league-scan rows) would otherwise inherit the idiom
  uncritically. A row tap that *selects* is ADR-133's shape and is still wanted; a row tap that opens a menu is
  this ADR again.

---

### ✅ What survives, deliberately

- **ADR-133's tap-to-select.** One tap → one round-trip → a selection. It genuinely replaces a dropdown and
  never promises more than it delivers. Cloud-verified twice now.
- **The selected-card outline.** Purely visual, says which player the panel below is about, nothing went wrong
  with it.
- **Two bug fixes that stand on their own**, both found while debugging the menu:
  - **Every link state must be pinned.** The component renders inside an iframe shipping `bootstrap.min.css`,
    which styles `a:visited` blue-and-underlined — so the card you had just clicked turned into a visible
    hyperlink. Styling the base `a` state is not enough inside someone else's CSS.
  - **A replayed click fired forever.** `click_detector` hands back its *last* click on every rerun, so every
    later rerun re-wrote the selection back to the last-tapped shirt and the dropdown could never override a
    tap. Guarded, with tests for both "fires once" and "the next real tap still fires".

### 🧪 Test record

`test_the_pitch_carries_its_own_actions_so_the_page_below_stays_thin` (the `<= 3` assertion) became
`test_the_actions_are_back_below_the_pitch_after_the_adr_135_revert`, which records that the count is back up
**by decision** and guards the shape that was worth keeping — actions in one panel, tap as an input to it.
`test_the_selected_card_carries_no_actions_only_an_outline` and `test_the_hover_popover_survives_on_every_card`
pin the revert itself.

**1294 green, ruff clean.** Net −3 from the peak: four ADR-135 tests retired, one added.
