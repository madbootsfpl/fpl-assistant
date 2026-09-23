/// Where the API is — **typed by a person, not compiled in** (ADR-239).
///
/// ⭐⭐ **The address was a `const`, and that is what kept the app on this machine.** `localhost:8078`
/// reaches the dev server from macOS, the iOS simulator and Chrome, because all three share the host's
/// network. A phone does not. Baking a LAN address in instead would just move the problem: it would be
/// wrong on Wi-Fi at a friend's house, wrong the moment the router hands out a new lease, and wrong again
/// when the API is finally hosted — three rebuilds for three answers to the same question.
///
/// ⭐ So it is **runtime state with a compile-time default**. The default still travels with the build via
/// `--dart-define=MADBOOTS_API=…`, which is how a hosted build will ship without anyone typing anything;
/// the stored value wins when there is one.
///
/// ⚠️⚠️ **This field points the app wherever someone types.** That is harmless on the owner's own phone
/// and is *not* something to hand a tester — it belongs behind a build flag before any wider build. Said
/// here rather than discovered later.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'api/client.dart';

import 'package:shared_preferences/shared_preferences.dart';

const String _key = 'server_base_url';

/// ⭐ `--dart-define=MADBOOTS_API=https://api.example.com` at build time; localhost when nobody says.
/// Whether the **Server** field is offered in Settings (ADR-270).
///
/// ⚠️⚠️ **Off unless a build asks for it.** A tester handed an editable API address has a way to point
/// the app at nothing, and ⭐ *the only bug report that follows is "the app stopped working"* — with no
/// sign in it that a field was ever touched. It is a developer's tool for pointing at a laptop on the
/// LAN, and it has no job on a handset that already knows where the hosted API is.
///
/// ⭐ Compile-time, so it is **absent from the build**, not merely hidden in it — *a control you can
/// reach by accident is a control that is enabled.*
///
/// Developer builds pass `--dart-define=MADBOOTS_DEV=true`.
const bool kServerFieldEnabled = bool.fromEnvironment('MADBOOTS_DEV');

const String kDefaultBaseUrl = String.fromEnvironment(
  'MADBOOTS_API',
  defaultValue: 'http://localhost:8078',
);

class Server {
  /// The address to use, stored value first.
  static Future<String> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_key)?.trim();
    return (saved == null || saved.isEmpty) ? kDefaultBaseUrl : saved;
  }

  static Future<void> save(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, tidy(url));
  }

  static Future<void> forget() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }

  /// ⭐ **Fixes what a person plausibly types** rather than refusing it. A trailing slash and a missing
  /// scheme are the two everyone produces, and both are unambiguous — rejecting them would be pedantry
  /// dressed as validation.
  static String tidy(String raw) {
    var s = raw.trim();
    while (s.endsWith('/')) {
      s = s.substring(0, s.length - 1);
    }
    if (s.isNotEmpty && !s.contains('://')) s = 'http://$s';
    return s;
  }

  /// What is wrong with this address, or null if nothing is.
  ///
  /// ⚠️ **Not a reachability check** — this is the half that can be answered without the network, and
  /// keeping the two apart is what lets the app say *"that is not an address"* rather than *"the server
  /// did not answer"* when the fault is a typo.
  static String? problemWith(String raw) {
    final s = tidy(raw);
    if (s.isEmpty) return 'Enter an address, or use the default.';
    final uri = Uri.tryParse(s);
    if (uri == null || uri.host.isEmpty) return 'That is not an address.';
    if (uri.scheme != 'http' && uri.scheme != 'https') {
      return 'The address has to start with http:// or https://';
    }
    if (uri.path.isNotEmpty && uri.path != '/') {
      // ⭐ The client appends `/api/v1/…` itself, so a pasted docs URL would produce `…/api/v1/docs/api/v1/…`
      // and a 404 that looks like the server is missing routes.
      return 'Leave off the path — just the host and port, like http://192.168.1.20:8078';
    }
    return null;
  }
}

/// What happened when the app tried the address — ⭐ **four outcomes, not two.**
///
/// ⭐⭐ `wrongService` is the one that earns this type. A phone on a home network can land on a router's
/// admin page, another dev server on the same port, or a captive portal, and **every one of those answers
/// 200**. Reporting that as a healthy connection is worse than reporting a failure, because the next
/// screen's error is then blamed on the app.
enum Reach { ok, refused, wrongService, badAddress }

class ReachResult {
  const ReachResult(this.reach, this.message);

  final Reach reach;
  final String message;

  bool get ok => reach == Reach.ok;
}

/// Try the address and say, in a sentence, what came back.
Future<ReachResult> reach(String raw, {http.Client? client}) async {
  final problem = Server.problemWith(raw);
  if (problem != null) return ReachResult(Reach.badAddress, problem);

  final base = Server.tidy(raw);
  final own = client == null;
  final c = client ?? http.Client();
  try {
    final response = await c
        .get(Uri.parse('$base/api/v1/health'))
        .timeout(const Duration(seconds: 6));

    if (response.statusCode != 200) {
      return ReachResult(
        Reach.wrongService,
        'Something answered at $base, but with HTTP ${response.statusCode} — that is not the API.',
      );
    }
    Map<String, dynamic> body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      // ⚠️ A router admin page or a captive portal answers 200 with HTML.
      return ReachResult(
        Reach.wrongService,
        'Something answered at $base, but not with JSON — check the address and port.',
      );
    }
    if (body['service'] != 'madboots') {
      return ReachResult(
        Reach.wrongService,
        'Something is running at $base, but it is not MADBOOTS. Check the port.',
      );
    }
    return ReachResult(
      Reach.ok,
      'Connected — MADBOOTS ${body['version'] ?? ''}'.trim(),
    );
  } on TimeoutException {
    return ReachResult(
      Reach.refused,
      'No answer from $base within six seconds. If that is your Mac, check it is awake and on the '
      'same Wi-Fi.',
    );
  } on SocketException {
    return ReachResult(Reach.refused, _refused(base));
  } on http.ClientException {
    // ⚠️ On web there is no SocketException — a refused connection arrives as a ClientException.
    return ReachResult(Reach.refused, _refused(base));
  } catch (e) {
    return ReachResult(Reach.refused, 'Could not reach $base — $e');
  } finally {
    if (own) c.close();
  }
}

/// ⭐ One wording, defined in `client.dart` and used by both — ⚠️ *two doors to one room drift apart*
/// (ADR-184), and a Settings check that explained the failure differently from the screen that hit it
/// would be exactly that.
String _refused(String base) => refusedMessage(base);
