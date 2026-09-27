import 'package:shared_preferences/shared_preferences.dart';

/// The manager's own free-transfer count, when he has corrected the one the server worked out (ADR-321).
///
/// ⚠️⚠️ **This did not exist, and the setting did not survive the app closing.** `_freeTransfers` was a
/// plain field initialised to `1`: set it to 2 in Settings, quit, reopen, and it was 1 again — silently,
/// with every screen then advising a position the manager was not in. ⭐ *A setting that does not persist
/// is a setting that was never really offered* — the exact sentence [ManagerStore] already carries, about
/// the field directly above this one on the same screen (ADR-279).
///
/// ⭐⭐ **Null is the normal state, not an empty one.** Nobody should have to tell the app this: since
/// ADR-318 the server derives it from the manager's own transfer history. A saved value means *"your
/// history is out of date, here is the real number"* — ⚠️ which is a claim worth keeping, and a claim the
/// code can only act on while it can still tell it apart from having asked nobody.
class FreeTransferStore {
  static const _key = 'fpl_free_transfers';

  /// The manager's override, or `null` when he has not contradicted the server.
  Future<int?> load() async {
    final raw = (await SharedPreferences.getInstance()).getInt(_key);
    // ⚠️ Range-checked on the way out as well as in. A value written by an older build — or by a hand
    // editing preferences — should not be able to fail the request it is put into.
    return (raw == null || raw < 0 || raw > 5) ? null : raw;
  }

  Future<void> save(int count) async {
    if (count < 0 || count > 5) return;
    await (await SharedPreferences.getInstance()).setInt(_key, count);
  }

  /// ⭐ **The way back to automatic.** Without this an override is a one-way door: correct the number once
  /// and the app never trusts the history again, including after the deadline that made the history right.
  Future<void> clear() async =>
      (await SharedPreferences.getInstance()).remove(_key);
}
