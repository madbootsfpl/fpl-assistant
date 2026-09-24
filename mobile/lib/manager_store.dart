/// Whose team this is (ADR-279).
///
/// ⚠️⚠️ **The manager id was a `const` in the source and was never saved.** Every install opened on the
/// author's squad, and a tester who typed their own id in Settings found it gone the next launch — the
/// app persisted their drafts, their seen signals, their feedback address and their server URL, and not
/// the one value that says *whose team this is*.
///
/// ⭐ *The most personal setting in the app was the only one that did not stick.*
library;

import 'package:shared_preferences/shared_preferences.dart';

class ManagerStore {
  static const _key = 'fpl_manager_id';

  /// The saved id, or `null` when nobody has said yet.
  ///
  /// ⭐ **Null, not a default.** A default here is a guess about whose team you are looking at, and ⚠️
  /// *the app cannot tell a guess from an answer once it has written one down.*
  Future<int?> load() async {
    final raw = (await SharedPreferences.getInstance()).getInt(_key);
    return (raw == null || raw < 1) ? null : raw;
  }

  Future<void> save(int managerId) async {
    if (managerId < 1) return;
    await (await SharedPreferences.getInstance()).setInt(_key, managerId);
  }

  /// ⚠️ Used by *"this is not my team"* — ⭐ a way back out matters more here than anywhere, because
  /// getting this one wrong means every screen is about a stranger.
  Future<void> clear() async =>
      (await SharedPreferences.getInstance()).remove(_key);
}
