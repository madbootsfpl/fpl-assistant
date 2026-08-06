# Architectural Decision Record: Help tooltips (ⓘ) on web controls

**Decision ID:** ADR-065
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** none — a UX polish over the Streamlit edge (ADR-052). No analytics change.
Triggered by tester feedback (Feedback_Log, 2026-08-06).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

A new user can't tell what each control does. The tester wants a small **ⓘ tooltip** over **all feature
options** explaining what each does.

**Verified in code (2026-08-06):** Streamlit renders an **ⓘ tooltip** for any widget given `help="…"`
(selectbox/multiselect/slider/number_input/text_input/checkbox/radio/button/download_button/file_uploader).
`st.tabs` labels and `st.chat_input` take no `help=` (they keep their captions). **AppTest exposes `.help`**,
so a coverage test can enforce it. Adding help once in the **shared components** (`filters.py`,
`paginate.py`, `squads.py`) covers many pages at a stroke.

#### Decision Drivers
- **Self-explaining UI** — every option says what it does, on hover.
- **Consistent + concise** — one short, action-oriented sentence per control.
- **Enforced** — a coverage test stops new controls shipping without help.
- **No behaviour change** — help text only; analytics untouched.

---

### ✅ Decision

**1. `help=` on every input control.** Add a concise `help` string to every
selectbox/multiselect/slider/number_input/text_input/checkbox/radio in the web — *what it does / what
picking it means* — in a consistent voice. Written **inline** (the string lives on the widget, so control +
help stay together). Important **buttons** (Import team, Use this squad, Apply transfer, Set captain,
Refresh, Show what's talked about) get help too.

**2. Add it at the shared components for leverage.** `filters.py` (`filter_controls` — Team/Position/Player
+ max-price), `paginate.py` (the page selectbox), `squads.py` (`squad_picker` + `render_sidebar`'s upload /
manager-ID / import) carry help for the controls they own — so Players, Player Stats, Trending and every
squad page inherit it. Per-page controls (Players sort, Fixtures weeks, Build Squad's options, My Squad /
Transfer / Captain edits) get their own.

**3. Exemptions.** `st.tabs` labels and `st.chat_input` (Ask) don't accept `help=` — they keep the existing
one-line **captions**. (A caption already sits under most page titles.)

**4. A coverage test (`tests/test_help_tooltips.py`).** For each page, AppTest-run it and assert **every**
input widget (`selectbox/multiselect/slider/number_input/text_input/checkbox/radio`) has a non-empty
`.help`. This gates the tester's "all options" and prevents regressions. Buttons are not strictly gated
(they're actions, not "options") but the key ones get help.

---

### 🔀 Alternatives Considered

- **A central `HELP` dict** keyed by control. Rejected — indirection; inline `help=` keeps the string with
  the control and reads better. The coverage test (not a dict) is what guarantees completeness.
- **Only the non-obvious/advanced controls.** Rejected — the tester asked for **all** options; a blanket
  pass + a strict test is simpler to reason about than a per-control judgement call.
- **Per-page "what this page does" intros instead of per-control help.** Rejected as the primary — pages
  already have captions; the ask is per-*option* tooltips.

---

### 🧭 Consequences

**Positive**
- Every option is self-explaining on hover; new users can learn the app without docs.
- Shared-component help means broad coverage from a few edits.
- The coverage test makes "every option has help" a standing guarantee.

**Negative / risks (mitigations)**
- **`st.tabs`/`st.chat_input` can't show ⓘ** → captions cover them (documented exemption in the test).
- **Help text drifts from behaviour** → it lives next to the control; the coverage test flags a *missing*
  tooltip (not wrong text), and reviews catch wording.
- **A large mechanical diff** → split across two stories (shared+browse, then squad/decision pages).

---

### 📊 Validation

Verified: Streamlit shows an ⓘ for `help=`; AppTest exposes `.help`. Acceptance: the shared components +
each page's controls carry concise help; the coverage test asserts every input widget on the touched pages
has non-empty `.help`; `st.tabs`/`chat_input` exempt; no analytics/data change; the web writes nothing
server-side; the existing 578 tests stay green.
