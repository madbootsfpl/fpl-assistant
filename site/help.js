// Maddie's videos, straight from the table the owner curates (ADR-319).
//
// ⭐⭐ **Not generated into the page, and that is the point.** The owner adds, replaces, reorders or hides a
// video by editing a row in the Supabase dashboard — exactly as the Streamlit hub has always worked. Baking
// them in at build time would have turned "edit a row" into "run a deploy", which is the opposite of what
// was asked for.
//
// ⚠️ The publishable key is in this file and that is expected. `maddie_videos` is `SELECT`-only for `anon`
// and holds public marketing content — the same reasoning ADR-216 records for the key compiled into the app
// binary. ⚠️⚠️ *The moment this page reads anything a person typed, that stops being true.*
(function () {
  'use strict';

  // Filled by scripts/generate_site_palette.py-style substitution at deploy; see release_web.sh.
  var STORE = window.MADBOOTS_STORE || {};

  var list = document.getElementById('video-list');
  var status = document.getElementById('v-status');
  if (!list) return;

  function say(text) { if (status) status.textContent = text; }

  // ⭐ youtu.be/ID · watch?v=ID · /embed/ID all become an embeddable URL. ⚠️ A URL we cannot parse renders
  // as a **link** rather than a broken frame: *a clip that will not play should still be reachable.*
  function embed(url) {
    var m = String(url || '').match(/(?:youtu\.be\/|[?&]v=|\/embed\/)([\w-]{6,})/);
    return m ? 'https://www.youtube-nocookie.com/embed/' + m[1] : null;
  }

  function render(rows) {
    if (!rows.length) { say('None published yet — check back soon.'); return; }
    say(rows.length + (rows.length === 1 ? ' video' : ' videos'));
    list.innerHTML = rows.map(function (row) {
      var src = embed(row.youtube_url);
      var head = '<div class="cap"><h3>' + esc(row.topic || 'Untitled') + '</h3>'
        + (row.blurb ? '<p>' + esc(row.blurb) + '</p>' : '') + '</div>';
      if (src) {
        return '<article class="video"><iframe src="' + src + '" title="' + esc(row.topic || '')
          + '" loading="lazy" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>'
          + head + '</article>';
      }
      if (row.youtube_url) {
        return '<article class="video">' + head.replace('</div>',
          '<p><a href="' + esc(row.youtube_url) + '" rel="noopener">Watch on YouTube →</a></p></div>')
          + '</article>';
      }
      // ⚠️ A row with no URL is a promise, not a video — say "coming soon" rather than draw an empty player.
      return '<article class="video">' + head.replace('</div>',
        '<p>Coming soon.</p></div>') + '</article>';
    }).join('');
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  if (!STORE.url || !STORE.key) {
    // ⭐ Fail soft, exactly like the Streamlit hub: the page is useful without the clips.
    say('Video hub not configured.');
    return;
  }

  fetch(STORE.url + '/maddie_videos?select=topic,blurb,youtube_url,sort_order'
        + '&published=eq.true&order=sort_order',
        { headers: { apikey: STORE.key, Authorization: 'Bearer ' + STORE.key } })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (rows) { render(Array.isArray(rows) ? rows : []); })
    // ⚠️ Never a stack trace on a marketing page — *a reader who sees an error concludes the product is
    // broken, not that one table was unreachable.*
    .catch(function () { say('Could not load the videos just now.'); });
})();
