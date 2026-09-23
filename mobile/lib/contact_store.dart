/// The address a tester gave us last time.
///
/// ⭐ **Remembered on purpose.** Feedback is worth replying to, and an optional field that must be retyped
/// on every report is an optional field that gets filled in once. ⚠️ *The cost of asking is paid per
/// report; the cost of remembering is paid once* — so the second report is the one this exists for.
///
/// 📌 Device-local, like the draft (ADR-260) and the seen-signals set (ADR-232): it is a convenience about
/// this handset, not a record about a person.
library;

import 'package:shared_preferences/shared_preferences.dart';

class ContactStore {
  static const _key = 'feedback_contact';

  Future<String> load() async =>
      (await SharedPreferences.getInstance()).getString(_key) ?? '';

  /// ⚠️ Blank **clears** rather than being ignored — a tester removing their address means it.
  Future<void> save(String contact) async {
    final prefs = await SharedPreferences.getInstance();
    final tidy = contact.trim();
    if (tidy.isEmpty) {
      await prefs.remove(_key);
    } else {
      await prefs.setString(_key, tidy);
    }
  }
}
