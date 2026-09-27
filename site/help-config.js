// Where the video hub lives — written at deploy time by scripts/release_web.sh from the environment.
//
// ⭐ Committed **empty** on purpose. The key is publishable (ADR-216: `maddie_videos` is `SELECT`-only for
// `anon`), but a credential in git is still a credential nobody rotated — ⚠️ *"safe to publish" and "safe
// to commit" are different questions, and only one of them has an audit trail.*
//
// With this empty the help page renders in full and the video section says so, exactly as the Streamlit
// hub does when the store is unreachable.
window.MADBOOTS_STORE = { url: '', key: '' };
