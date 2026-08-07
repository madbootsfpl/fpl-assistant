"""A live, client-side countdown clock for the next FPL deadline (Sprint 103, ADR-088).

`render_countdown` builds one self-contained HTML/CSS + `<script>` block and renders it with
`components.html` (a sandboxed iframe), so a `setInterval` ticks the clock every second **in the browser** —
no server reruns. The cells are filled server-side too, so it's readable even if the JS/iframe is blocked (and
the ADR-086/US-267 text line sits beneath as the accessible fallback). Display-only; the only values embedded
are our own (the deadline ISO + the gameweek number). The first JS in the app.
"""

import html as _html
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

_UK = ZoneInfo("Europe/London")
_ACCENT = {"calm": "#22c55e", "today": "#f59e0b", "imminent": "#ef4444"}


def _parts(total_seconds: int):
    """Non-negative `total_seconds` → (days, hours, minutes, seconds)."""
    total = max(0, int(total_seconds))
    days, rem = divmod(total, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes, seconds = divmod(rem, 60)
    return days, hours, minutes, seconds


def countdown_html(gameweek: int, deadline: datetime, now: datetime, urgency: str = "calm") -> str:
    """The self-contained HTML/CSS + tick-script for the clock (pure → unit-tested). Cells are filled with the
    current remaining time (readable without JS); `setInterval` keeps them live off the embedded deadline ISO.
    Urgency-coloured; `now`/`deadline` are timezone-aware."""
    accent = _ACCENT.get(urgency, _ACCENT["calm"])
    d, h, m, s = _parts((deadline - now).total_seconds())
    iso = deadline.isoformat()                                   # our own value; parsed by JS `new Date(...)`
    when = _html.escape(deadline.astimezone(_UK).strftime("%a %-d %b, %H:%M"))
    cells = [("DAYS", "d", d), ("HRS", "h", h), ("MINS", "m", m), ("SECS", "s", s)]
    cell_html = "".join(
        f'<div class="cell"><div class="num" id="{cid}">{val:02d}</div><div class="lab">{lab}</div></div>'
        for lab, cid, val in cells
    )
    block = f"""
<style>
.cd-wrap{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:14px;padding:14px 12px;
box-shadow:inset 0 0 0 1px rgba(255,255,255,.06);color:#e2e8f0;text-align:center;}}
.cd-title{{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:{accent};font-weight:700;
margin-bottom:8px;}}
.cd-grid{{display:flex;justify-content:center;gap:10px;}}
.cd-grid .cell{{min-width:56px;background:rgba(255,255,255,.05);border-radius:10px;padding:8px 4px;}}
.cd-grid .num{{font-size:1.7rem;font-weight:800;line-height:1;color:{accent};
font-variant-numeric:tabular-nums;}}
.cd-grid .lab{{font-size:.6rem;letter-spacing:.1em;color:#94a3b8;margin-top:4px;}}
.cd-sub{{font-size:.72rem;color:#cbd5e1;margin-top:9px;}}
</style>
<div class="cd-wrap">
<div class="cd-title">GW{gameweek} deadline</div>
<div class="cd-grid">{cell_html}</div>
<div class="cd-sub" id="cd-sub">{when} (UK)</div>
</div>
<script>
(function() {{
  const target = new Date("{iso}").getTime();
  const pad = n => String(n).padStart(2, "0");
  function tick() {{
    let left = Math.floor((target - Date.now()) / 1000);
    if (left <= 0) {{
      ["d","h","m","s"].forEach(id => document.getElementById(id).textContent = "00");
      document.getElementById("cd-sub").textContent = "deadline passed — good luck!";
      clearInterval(iv);
      return;
    }}
    const d = Math.floor(left/86400); left -= d*86400;
    const h = Math.floor(left/3600);  left -= h*3600;
    const m = Math.floor(left/60);    const s = left - m*60;
    document.getElementById("d").textContent = pad(d);
    document.getElementById("h").textContent = pad(h);
    document.getElementById("m").textContent = pad(m);
    document.getElementById("s").textContent = pad(s);
  }}
  tick();
  const iv = setInterval(tick, 1000);
}})();
</script>
"""
    return block


def render_countdown(gameweek: int, deadline: datetime, now: datetime, urgency: str = "calm") -> None:
    """Render the live Days:Hrs:Mins:Secs clock (ADR-088) — our own HTML embedded in a JS-enabled iframe."""
    st.iframe(countdown_html(gameweek, deadline, now, urgency), height=138)
