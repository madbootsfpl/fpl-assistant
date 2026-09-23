/// What the device has already shown you (ADR-232, shared in ADR-256).
///
/// ⭐⭐ **The server cannot answer "what is new".** It has no idea when you last looked — so it says what
/// *exists*, carrying a stable key per signal, and the device works out the rest. ⚠️ *That split is the
/// whole reason the what-changed view needed no new data*, and it is why the pitch badge needed no new
/// endpoint either.
///
/// ⭐ Moved out of `signals_view.dart` **the moment the pitch needed it too** — a second copy would be two
/// memories of one thing, and they would disagree the first time one screen saved and the other did not.
library;

import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Remembers which signals have already been shown. ⭐ One key, like the draft store — the app needs a
/// memory, not a database.
class SeenStore {
  static const String _key = 'madboots.signals.seen.v1';

  Future<Set<String>> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return {};
    try {
      return (jsonDecode(raw) as List).cast<String>().toSet();
    } catch (_) {
      return {};
    }
  }

  Future<void> save(Set<String> keys) async {
    final prefs = await SharedPreferences.getInstance();
    // ⚠️ Replaced, not merged: a key that no longer comes back is a signal that has passed, and keeping it
    // forever would grow a list nobody reads until it slowed the thing it was meant to speed up.
    await prefs.setString(_key, jsonEncode(keys.toList()));
  }
}
