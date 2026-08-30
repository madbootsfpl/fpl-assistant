"""Admin — beta analytics (ADR-100, US-337).

A **gated** owner view over the anonymous `events` table: sessions, returning devices, most-used pages/features,
success rates, and median/P95 performance. Gated by **`FPL_ADMIN_KEY`** (an owner password) — **inert when unset**
(the public deploy shows a "not configured" note; testers can't see the numbers). Reads via `analytics` (the first
analytics read — needs an anon SELECT policy, docs/ANALYTICS.md); best-effort, so a store hiccup shows a note, not
a crash. The heavy lifting is `analytics.summarise` (pure); this page just renders.
"""

import streamlit as st

from src.web_streamlit import analytics, auth, brand, cloud_store, roster, user_store
from src.web_streamlit.access import require_access, secret

st.set_page_config(**brand.page_config("Admin"))
require_access()          # testers still pass the beta gate first (ADR-087)
analytics.boot("Admin")
st.title("📊 Admin — beta analytics")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)


def _render_ask_evaluation():
    # Retired as a public page: 14 of its 16 intents duplicated a tab, and the two that didn't (rules, scoring)
    # moved to Help, where a reference belongs. It survives **here** because the owner asked the right question —
    # *"maybe I could have it as a tab in Admin so I could test with my local Ollama, which would mimic a hosted
    # model, so I can gauge its usefulness."*
    #
    # ⚠️ **What this can and cannot measure.** Run locally with Ollama it shows the full experience — narration on
    # top of the grounded block — which is exactly the thing a hosted model would buy. Opened on Cloud it shows
    # the same data-only answer every tester saw, because there is no model there either. So it answers *"is the
    # writing worth paying for?"* and says nothing about whether testers would use it, since they will never see it.
    #
    # ⏳ **Decision trigger: the GW4-6 calibration sitting.** By then it has been used or it has not, and "I never
    # opened it" is a decisive answer. An experiment with no end date is just a parked page (this project has two).
    st.divider()
    st.subheader("💬 Ask — under evaluation")
    st.caption("Retired from the sidebar (ADR-168) and kept here to judge one question: **is the narration worth "
               "a hosted model?** Local Ollama → you see what a paid model would add. On Cloud → data-only, the "
               "same answer every tester got. Revisit at the GW4-6 calibration.")

    if st.checkbox("Load Ask", key="admin_ask_on", help="Off by default — it runs the full grounded pipeline."):
        from src import ask as _ask_mod
        from src.storage import Storage as _Store
        from src.ui.ask import render_ask as _render_ask
        from src.web_streamlit.squads import active_squad as _active_squad

        if "admin_ask_history" not in st.session_state:
            st.session_state.admin_ask_history = []
            st.session_state.admin_ask_ctx = None

        _q = st.text_input("Ask a question", key="admin_ask_q",
                           placeholder="who should I captain from my squad?")
        if st.button("Ask →", key="admin_ask_go") and _q.strip():
            _store = _Store()
            try:
                _result, _ctx = _ask_mod.converse(_q, st.session_state.admin_ask_ctx,
                                                  store=_store, active_squad=_active_squad())
            finally:
                _store.close()
            st.session_state.admin_ask_ctx = _ctx
            # `ollama_hint=True` **on purpose**, unlike the old page: this surface exists to tell you whether a
            # model is answering, so the "start Ollama" line is the diagnostic rather than noise.
            st.session_state.admin_ask_history.append((_q, _render_ask(_result, markdown=True)))

        for _question, _answer in reversed(st.session_state.admin_ask_history):
            st.markdown(f"**{_question}**")
            st.markdown(_answer)
            st.divider()


_KEY = secret("FPL_ADMIN_KEY")
_OK = "_admin_ok"

# 💬 Ask renders **before** the analytics gate, and that is the fix for a real mistake: it was appended to the
# end of this page, so `st.stop()` below hid it whenever `FPL_ADMIN_KEY` was unset — which is **every local
# run**. The one surface built to be used with a local Ollama was reachable only where no Ollama exists.
# Trying a question has nothing to do with the analytics store, so it should never have shared its gate.
#
# Owner-only where a key is configured; open when it is not, which means local — there the machine is the
# gate. Same idiom as ADR-087's access gate: inert unless the secret is set.
if not _KEY or st.session_state.get(_OK):
    _render_ask_evaluation()
    st.divider()

if not _KEY:
    st.info("Admin **analytics** isn't configured. Set **`FPL_ADMIN_KEY`** (and `FPL_ANALYTICS`) + add the "
            "anon SELECT policy — see **docs/ANALYTICS.md**. *(💬 Ask above needs none of that.)*")
    st.stop()

if not st.session_state.get(_OK):
    st.caption("Owner only — enter the admin key.")
    entered = st.text_input("Admin key", type="password", key="_admin_key")
    if entered and entered == _KEY:
        st.session_state[_OK] = True
        st.rerun()
    elif entered:
        st.error("That admin key isn't right.")
    st.stop()

# --- unlocked -----------------------------------------------------------------------
if not analytics.is_enabled():
    st.warning("Analytics is currently **off** (`FPL_ANALYTICS` unset) — no new events are being collected.")

rows = analytics.recent_events()
if rows is None:
    st.error("Couldn't read the events store. Check the store secrets + the **anon SELECT policy** on `events` "
             "(docs/ANALYTICS.md).")
    st.stop()

s = analytics.summarise(rows)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Events", s["events"])
c2.metric("Sessions", s["sessions"])
c3.metric("Devices", s["devices"])
c4.metric("Returning", s["returning"])
span = f" · {s['since'][:10]} → {s['until'][:10]}" if s.get("since") else ""
pct = f" · {s['success_pct']}% ok" if s.get("success_pct") is not None else ""
st.caption(f"Last {len(rows)} events{span}{pct}. Anonymous — no personal data (ADR-100).")

if not rows:
    st.info("No events yet. Once `FPL_ANALYTICS=1` and testers use the app, they'll appear here.")
    st.stop()

# --- Load & concurrency (ADR-120) ------------------------------------------------------
# Registered testers is cheap; the real limit is how many are active *at once* on one small container. The
# failure mode is sluggishness, not a crash — most likely at a deadline spike.
_load = analytics.load_summary(rows)
_icon = {"green": "🟢", "amber": "🟡", "red": "🔴"}[_load["health"]]
st.subheader(f"{_icon} Load & concurrency")
l1, l2, l3 = st.columns(3)
l1.metric("Active now", _load["active_now"], help=f"Distinct sessions with an event in the last "
                                                  f"{_load['window_min']} minutes.")
l2.metric("Peak concurrent", _load["peak_concurrent"], help="The busiest such window in this data — the number "
                                                            "to watch at a deadline.")
l3.metric("P95 latency", f"{_load['p95_ms']} ms" if _load["p95_ms"] else "—",
          help="Slowest 5% of analysis / data-load timings. Climbing P95 alongside concurrency means the "
               "container is stretched.")
st.caption("Both counts are **proxies** — an event is a click, not a held connection, so an idle open tab is "
           "invisible. Directional: watch the trend beside P95. Thresholds are uncalibrated heuristics "
           "(ADR-120) — tune them against real load.")

# --- Tester activity (ADR-120) ---------------------------------------------------------
# The analytics above are anonymous by design and cannot name anyone. This is a *separate* join over the
# owner's own allow-list — never a de-anonymisation of an event.
st.subheader("👥 Tester activity")
_emails = user_store.all_emails()
if not _emails:
    st.caption("No allow-list to read (store unconfigured, or `beta_users` is empty).")
else:
    # ADR-142 — TWO signals, kept apart. "Signed in" is *used the app*; "saved a squad" is a much rarer,
    # much stronger act. The panel used to judge activity on the save alone, which reported 18 of 25 testers
    # as ⚪ never while at least two were using it daily.
    _keys = {e: auth.user_key(e) for e in _emails}
    _saved = cloud_store.updated_at_by_handle(_keys.values())
    _seen = user_store.last_seen_by_email(_emails)
    _rows = roster.build(_emails, _saved, key_for=_keys.get, seen_by_email=_seen)
    _t = roster.totals(_rows)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Registered", _t["registered"])
    r2.metric("🟢 Active", _t["active"], help="Signed in within the last 7 days.")
    r3.metric("🟡 Dormant", _t["dormant"], help="Last signed in 7–30 days ago.")
    r4.metric("⚪ Never", _t["never"], help="On the allow-list but has never signed in.")
    _badge = {"active": "🟢 active", "dormant": "🟡 dormant", "lapsed": "🔴 lapsed", "never": "⚪ never"}
    st.dataframe([{"Tester": r["email"], "Status": _badge[r["status"]],
                   "Last used": r["last_seen"][:10] if r["last_seen"] else "—",
                   "Last saved a squad": r["last_saved"][:10] if r["last_saved"] else "—",
                   "Days ago": r["days"] if r["days"] is not None else "—"} for r in _rows],
                 hide_index=True, use_container_width=True)
    if not _seen:
        # Say it plainly rather than showing a column of dashes and letting it read as "nobody has been here".
        st.warning("**No sign-in times recorded yet**, so status below falls back to *when a squad was last "
                   "saved* — which most testers never do, and is why this panel under-reported activity. "
                   "The column has to exist:  "
                   "`alter table beta_users add column if not exists last_seen timestamptz;`")
    # ADR-142 rev — a diagnostic, because the write is deliberately silent for testers and that made an
    # all-NULL column impossible to explain: never attempted? no row matched? refused by a policy? This runs
    # the **same** `touch_last_seen` the sign-in does — a probe down a different path would prove nothing —
    # and prints what it actually got back. Owner-only page, so the raw store error is safe to show.
    with st.expander("🔧 Why isn't `last_seen` filling in?"):
        st.caption("Runs the real sign-in stamp for one tester and reports exactly what the store said. "
                   "Two failures look nothing alike and need different fixes: a **401/403** is a missing "
                   "`GRANT` (the role can't touch the table); **\"reached no rows\"** is row-level security "
                   "with no UPDATE policy — Postgres doesn't raise for that, it just narrows the update to "
                   "nothing, so it fails in total silence.")
        _who = st.selectbox("Stamp this tester", _emails, key="admin_touch_who")
        if st.button("Run the stamp now", key="admin_touch_go"):
            _result = user_store.touch_last_seen(_who)
            (st.success if _result == "ok" else st.error)(f"`touch_last_seen({_who})` → **{_result}**")
            if _result != "ok":
                st.code("revoke update on public.beta_users from anon;\n"
                        "grant  update (last_seen) on public.beta_users to anon;\n\n"
                        'create policy "anon stamps last_seen" on public.beta_users\n'
                        "  for update to anon using (true) with check (true);", language="sql")
                st.caption("Grants **one column**, not the table — the anon key ships to the browser, so a "
                           "blanket update policy would let anyone rewrite an allow-listed `email` to their "
                           "own and admit themselves. The app only ever writes `last_seen` here, so nothing "
                           "else needs the privilege.")
            st.caption("Then sign out and back in — or press this again — and re-run the page to see it land.")
    st.caption("**Last used** = signed in. **Last saved a squad** = pressed save, which is rarer and a "
               "stronger signal — someone actively managing a team rather than visiting. A tester browsing "
               "**signed-out** appears in neither. Read it beside the anonymous totals above; those stay "
               "anonymous and are never joined to this (ADR-100).")

# ADR-147 — the same one-click diagnostic ADR-142 needed, added *before* it is needed rather than after a day
# of NULLs. `user_prefs` is a new table; until it exists (or if its policies are wrong) preferences silently
# stay session-only, which looks exactly like the feature not working.
with st.expander("🔧 Are cross-device preferences storing?"):
    st.caption("Writes a harmless value to `user_prefs` as you, and reports what the store said. **200 OK with "
               "zero rows** means row-level security with no INSERT/UPDATE policy — Postgres does not raise "
               "for that, it narrows the write to nothing (the failure that cost a day in ADR-142).")
    if st.button("Test the preference store", key="admin_prefs_go"):
        from src.web_streamlit import prefs as _prefs
        _r = _prefs.remember(manager_id=str(st.session_state.get("manager_id") or "1"))
        (st.success if _r in ("ok", "unchanged") else st.error)(f"`prefs.remember(…)` → **{_r}**")
        if _r not in ("ok", "unchanged", "session only (not signed in)"):
            st.code(
                    "create table if not exists public.user_prefs (\n"
                    "  user_key   text primary key,\n"
                    "  manager_id text,\n"
                    "  league_id  bigint,\n"
                    "  updated_at timestamptz default now()\n"
                    ");\n"
                    "alter table public.user_prefs enable row level security;\n"
                    "\n"
                    "-- No 'create policy if not exists' in Postgres — drop-then-create keeps this\n"
                    "-- whole block safe to run again.\n"
                    "-- The anon key ships to the browser, so every policy is scoped to this table alone.\n"
                    "drop policy if exists \"prefs read\"   on public.user_prefs;\n"
                    "drop policy if exists \"prefs insert\" on public.user_prefs;\n"
                    "drop policy if exists \"prefs update\" on public.user_prefs;\n"
                    "drop policy if exists \"prefs delete\" on public.user_prefs;\n"
                    "\n"
                    "create policy \"prefs read\"   on public.user_prefs for select to anon using (true);\n"
                    "create policy \"prefs insert\" on public.user_prefs for insert to anon with check (true);\n"
                    "create policy \"prefs update\" on public.user_prefs for update to anon\n"
                    "  using (true) with check (true);\n"
                    "create policy \"prefs delete\" on public.user_prefs for delete to anon using (true);",
                    language="sql")
            st.caption("Rows are keyed by a **hash** of the email (`auth.user_key`), never the address itself "
                       "— the same handle the squads table uses (ADR-106).")

left, right = st.columns(2)
with left:
    st.subheader("Most-viewed pages")
    st.dataframe(s["top_pages"] or [{"page": "—", "views": 0}], hide_index=True, use_container_width=True)
with right:
    st.subheader("Events")
    st.dataframe(s["event_counts"], hide_index=True, use_container_width=True)

st.subheader("Performance — median / P95 (ms)")
if s["perf"]:
    st.dataframe(s["perf"], hide_index=True, use_container_width=True)
else:
    st.caption("No `perf` events yet (data-load / analysis / save / load timings appear here).")
