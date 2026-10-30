// The external tick for the data pipeline (ADR-378).
//
// ⭐⭐ **This exists because GitHub's own cron does not fire at the rate it declares.** Measured twice:
// `*/15` fired 6 times in 24 hours (6-7% of declared, 2026-09-26), and `0 * * * *` arrives a median
// **3.9 h** apart (100 runs, 2026-10-30). The consequence is not cosmetic — `cadence()`'s pre-deadline
// branch promises *"four chances in the last hour"* and gets about one in four deadlines, so the app can
// show team news that is four hours old in the hour when team news is the whole game.
//
// ⭐ **Deliberately dumb.** It does not know when a deadline is and must never learn: the policy lives in
// `src/pipeline.py` where it is testable, and `data.yml`'s own comment says so — *"the schedule lives in
// Python, not in this cron line, because the thing it depends on moves every week."* This only supplies
// the opportunities; `refresh_due` decides. A tick with nothing to do exits in well under a second and
// makes no FPL request.
//
// ⚠️ `force` is **false**, always. Forcing would bypass the cadence gate 96 times a day and hammer FPL.
//
// 🔴 **Cloudflare's cron is also best effort**, and assuming otherwise is the mistake that produced this
// file. It is verified, not trusted: every refresh line prints the settled crowd phase (ADR-377), so
// comparing deadline coverage against the measured 26% baseline is how we find out whether this worked.

const OWNER = "madbootsfpl";
const REPO = "fpl-assistant";
const WORKFLOW = "data.yml";     // kept in step with .github/workflows/ by tests/test_external_trigger.py
const REF = "master";

async function dispatch(env) {
  if (!env.GITHUB_TOKEN) {
    // ⭐ Inert without its secret, the same shape as the workflows (`mirror.yml`, `data.yml`): an
    // unconfigured deployment does nothing rather than failing loudly every quarter hour.
    console.log("no GITHUB_TOKEN — nothing dispatched");
    return;
  }
  const url = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      // ⚠️ GitHub rejects an API request with no User-Agent.
      "User-Agent": `${OWNER}-pipeline-trigger`,
    },
    body: JSON.stringify({ ref: REF, inputs: { force: false } }),
  });
  // 204 is the success case for this endpoint — there is no body to read.
  console.log(res.status === 204
    ? `dispatched ${WORKFLOW} on ${REF}`
    : `dispatch failed: ${res.status} ${await res.text()}`);
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },

  // ⚠️ **Deliberately inert.** A fetch handler that dispatched would be an unauthenticated endpoint for
  // triggering workflows in this repo. ⭐ *A debugging convenience that anyone on the internet can call is
  // not a convenience.* Cron-trigger logs live in the Cloudflare dashboard; the end-to-end check is the
  // crowd phase in the refresh line.
  async fetch() {
    return new Response(
      "madboots pipeline trigger — runs on a cron trigger only; this endpoint does nothing.\n",
      { status: 200, headers: { "content-type": "text/plain" } },
    );
  },
};
