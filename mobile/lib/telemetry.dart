/// What the app tells the server about itself — and nothing else (ADR-280).
///
/// ⭐⭐ **The question this answers is capacity, not curiosity.** The owner: *"I want to see the
/// distribution & number using the apps on the different platforms, the reason, to make sure that we are
/// scaled enough to support. I am not interested in personal information."*
///
/// So three values ride on every request, and they are the whole of it:
///
/// | | |
/// |---|---|
/// | **platform** | `ios` · `android` · `web` — the distribution |
/// | **version** | which build, so an old one in the wild is visible |
/// | **install id** | a random UUID, generated once, ⚠️ **tied to nothing** |
///
/// ⚠️⚠️ **Deliberately absent: the manager id.** The server already receives it on four endpoints and
/// must not join it to this — ⭐ *the difference between "twelve Android devices" and "Tony opened
/// Trending" is the whole of the promise made here.*
///
/// ⭐ The install id exists because *"1,400 requests"* does not answer *"how many people"*, and counting
/// devices needs something stable. It is a random number that identifies nobody: it survives reinstalls
/// no better than the drafts do, and it maps to no person, email or squad. The web app has done exactly
/// this since ADR-100.
library;

import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class Telemetry {
  static const _key = 'install_id';

  /// ⭐ `ios` · `android` · `web` · `macos` … ⚠️ *Not* a device model, which would start to describe a
  /// person's belongings rather than a platform's load.
  static String get platform {
    if (kIsWeb) return 'web';
    return switch (defaultTargetPlatform) {
      TargetPlatform.iOS => 'ios',
      TargetPlatform.android => 'android',
      TargetPlatform.macOS => 'macos',
      TargetPlatform.windows => 'windows',
      TargetPlatform.linux => 'linux',
      TargetPlatform.fuchsia => 'fuchsia',
    };
  }

  /// ⭐⭐ **Resolved once, at start-up, and never again.**
  ///
  /// ⚠️⚠️ This began as a read *inside* the HTTP client — `await installId()` on every request — and it
  /// was wrong twice over: it put a storage lookup in the path of every screen, and it made the API
  /// client depend on a plugin, so **eighteen tests that had nothing to do with telemetry began failing
  /// with "Binding has not yet been initialized"**.
  ///
  /// ⭐ *Telemetry that can slow the app is telemetry that will be blamed for it — and telemetry that
  /// can break a test suite has already cost more than it measures.* Now `main()` resolves it before the
  /// first frame and the client reads a plain field.
  static Map<String, String> headers = const {};

  /// Called once from `main()`. ⚠️ Failing is fine and silent: ⭐ *no identity means no headers, which
  /// means an uncounted install — never a broken one.*
  static Future<void> init() async {
    try {
      headers = {
        'X-Madboots-Platform': platform,
        'X-Madboots-Install': await installId(),
      };
    } catch (_) {
      headers = const {};
    }
  }

  /// A random id for this install, created on first use and then reused.
  ///
  /// ⚠️ **Random, never derived.** A hash of the manager id would be reversible for anyone holding the
  /// list of manager ids — ⭐ *an identifier computed from something personal is that personal thing in
  /// a costume.*
  static Future<String> installId() async {
    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString(_key);
    if (existing != null && existing.isNotEmpty) return existing;

    final rng = Random.secure();
    final id = List.generate(
      16,
      (_) => rng.nextInt(256),
    ).map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    await prefs.setString(_key, id);
    return id;
  }

  /// ⚠️ Used by a *"stop counting me"* control — ⭐ *an identifier a reader cannot reset is one they
  /// cannot decline.* A new one is minted on next use; nothing connects it to the old.
  static Future<void> forget() async =>
      (await SharedPreferences.getInstance()).remove(_key);
}
