"""Stage C, proven against real Supabase with real tokens.

⭐ The local spike used a hand-rolled `auth.uid()` and simulated claims. This uses tokens Supabase actually
issued, over real PostgREST — so what it proves is the production mechanism, not a convincing model of it.
"""
import json
import os
import sys

import requests

URL, KEY = os.environ["SUPA_URL"], os.environ["SUPA_KEY"]
LEGACY = sys.argv[1]
TOK = {u: open(f"/tmp/tok_{u}.txt").read().strip() for u in ("alice", "bob")}
UID = {}
for u, t in TOK.items():
    import base64
    b = t.split(".")[1]; b += "=" * (-len(b) % 4)
    UID[u] = json.loads(base64.urlsafe_b64decode(b))["sub"]

def rest(method, path, who=None, body=None, prefer=None):
    """A PostgREST call as `who` (None = the publishable key alone, i.e. signed out)."""
    h = {"apikey": KEY, "Content-Type": "application/json"}
    if who:
        h["Authorization"] = f"Bearer {TOK[who]}"
    if prefer:
        h["Prefer"] = prefer
    r = requests.request(method, f"{URL}/rest/v1/{path}", headers=h,
                         data=json.dumps(body) if body is not None else None, timeout=20)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text

def show(label, status, body, expect):
    verdict = "✅" if expect(status, body) else "🔴 UNEXPECTED"
    s = json.dumps(body) if not isinstance(body, str) else body
    print(f"  {verdict} {label:52} [{status}] {s[:70]}")

print("── setup: each user saves their own squad ──")
show("alice saves her squad", *rest("POST", "c_squads", "alice",
     {"user_id": UID["alice"], "handle": "alice-squad", "data": {"picks": [1, 2, 3]}}),
     lambda s, b: s in (201, 200))
show("bob saves his squad", *rest("POST", "c_squads", "bob",
     {"user_id": UID["bob"], "handle": "bob-squad", "data": {"picks": [9]}}),
     lambda s, b: s in (201, 200))

print("\n── the app still works for each of them ──")
show("alice lists squads (expect exactly 1)", *rest("GET", "c_squads?select=handle", "alice"),
     lambda s, b: s == 200 and len(b) == 1 and b[0]["handle"] == "alice-squad")
show("bob lists squads (expect exactly 1)", *rest("GET", "c_squads?select=handle", "bob"),
     lambda s, b: s == 200 and len(b) == 1 and b[0]["handle"] == "bob-squad")

print("\n── the attacks that succeed TODAY ──")
show("bob GETs alice's squad by exact handle", *rest("GET", "c_squads?handle=eq.alice-squad", "bob"),
     lambda s, b: s == 200 and b == [])
show("bob overwrites alice's squad", *rest("PATCH", "c_squads?handle=eq.alice-squad", "bob",
     {"data": {"picks": [666]}}, prefer="return=representation"),
     lambda s, b: s in (200, 204) and b in ([], "", None))
show("bob deletes alice's squad", *rest("DELETE", "c_squads?handle=eq.alice-squad", "bob",
     prefer="return=representation"),
     lambda s, b: s in (200, 204) and b in ([], "", None))
show("bob inserts a row owned by ALICE", *rest("POST", "c_squads", "bob",
     {"user_id": UID["alice"], "handle": "planted", "data": {}}),
     lambda s, b: s == 403)
show("bob reassigns HIS OWN row to alice", *rest("PATCH", "c_squads?handle=eq.bob-squad", "bob",
     {"user_id": UID["alice"]}),
     lambda s, b: s == 403)

print("\n── a signed-OUT caller holding the publishable key (the mobile-binary case) ──")
show("anon lists squads", *rest("GET", "c_squads?select=handle"),
     lambda s, b: s in (401, 403))

print("\n── the migration: claiming rows that already exist ──")
show("alice's legacy row is invisible before claiming",
     *rest("GET", f"c_squads?handle=eq.{LEGACY}", "alice"),
     lambda s, b: s == 200 and b == [])
show("BOB (impostor) calls claim", *rest("POST", "rpc/c_claim_my_legacy_rows", "bob"),
     lambda s, b: s == 200 and b.get("squads") == 0)
show("alice calls claim", *rest("POST", "rpc/c_claim_my_legacy_rows", "alice"),
     lambda s, b: s == 200 and b.get("squads") == 1)
show("alice now sees it, data intact", *rest("GET", f"c_squads?handle=eq.{LEGACY}&select=data", "alice"),
     lambda s, b: s == 200 and len(b) == 1 and b[0]["data"]["picks"] == [7, 7, 7])
show("alice claims again (idempotent)", *rest("POST", "rpc/c_claim_my_legacy_rows", "alice"),
     lambda s, b: s == 200 and b.get("squads") == 0)
show("bob still cannot see it", *rest("GET", f"c_squads?handle=eq.{LEGACY}", "bob"),
     lambda s, b: s == 200 and b == [])

print("\n── ground truth (service key bypasses RLS — what is REALLY there) ──")
h = {"apikey": os.environ["SUPA_SERVICE_KEY"],
     "Authorization": f"Bearer {os.environ['SUPA_SERVICE_KEY']}"}
r = requests.get(f"{URL}/rest/v1/c_squads?select=handle,user_id,data", headers=h, timeout=20)
for row in r.json():
    owner = (row["user_id"] or "NULL")[:8]
    who = next((u for u, i in UID.items() if i == row["user_id"]), "—")
    print(f"     {row['handle'][:34]:36} owner={owner} ({who})  {json.dumps(row['data'])[:34]}")
