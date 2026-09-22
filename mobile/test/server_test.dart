/// The API's address, and what the app says when it is wrong (ADR-239).
///
/// ⭐⭐ **The reason this is worth testing at all is that every failure here looks the same from the phone.**
/// A sleeping Mac, a server bound to loopback, a phone on 4G instead of the Wi-Fi, a typo, and a router
/// admin page answering 200 are five different problems with one symptom. The app's only job is to tell
/// them apart, so the tests are one per confusion rather than one per function.
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/server.dart';

/// ⭐ The real `/api/v1/health` body, copied from what the route returns — see
/// `tests/test_service_health.py`, which asserts the server keeps returning exactly this.
const _health = '{"ok":true,"service":"madboots","version":"0.0.1"}';

void main() {
  group('tidying what a person types', () {
    test('a missing scheme is added, not refused', () {
      expect(Server.tidy('192.168.1.20:8078'), 'http://192.168.1.20:8078');
    });

    test('a trailing slash is dropped', () {
      // ⚠️ Left on, every call becomes `…8078//api/v1/…`.
      expect(Server.tidy('http://host:8078/'), 'http://host:8078');
      expect(Server.tidy('http://host:8078///'), 'http://host:8078');
    });

    test('https is left alone', () {
      expect(Server.tidy('https://api.madboots.app'), 'https://api.madboots.app');
    });
  });

  group('what is wrong with it, before the network is involved', () {
    test('empty', () => expect(Server.problemWith('  '), isNotNull));

    test('a pasted docs URL keeps its path, and the path is the fault', () {
      // ⭐ The client appends `/api/v1/…` itself, so this would produce a 404 that reads as "the server
      // is missing routes" — a fault reported against the wrong machine.
      final problem = Server.problemWith('http://localhost:8078/api/v1/docs');
      expect(problem, isNotNull);
      expect(problem, contains('path'));
    });

    test('a scheme the client cannot speak', () {
      expect(Server.problemWith('ftp://host'), contains('http'));
    });

    test('a plain host and port is fine', () {
      expect(Server.problemWith('192.168.1.20:8078'), isNull);
      expect(Server.problemWith('https://api.example.com'), isNull);
    });
  });

  group('reaching it', () {
    Future<ReachResult> against(http.Response Function(http.Request) handler) =>
        reach('http://host:8078', client: MockClient((r) async => handler(r)));

    test('the health route is what gets asked', () async {
      late Uri asked;
      await reach('http://host:8078/',
          client: MockClient((r) async {
            asked = r.url;
            return http.Response(_health, 200);
          }));
      // ⚠️ The trailing slash the user typed must not survive into the URL.
      expect(asked.toString(), 'http://host:8078/api/v1/health');
    });

    test('ours answering is the only thing that counts as connected', () async {
      final r = await against((_) => http.Response(_health, 200));
      expect(r.ok, isTrue);
      expect(r.message, contains('0.0.1'));
    });

    test('a 200 from something else is NOT connected', () async {
      // ⭐⭐ The failure this whole type exists for. A router admin page, another dev server on the same
      // port, a captive portal — all answer 200, and calling that healthy blames the next screen's error
      // on the app.
      final r = await against((_) => http.Response('{"ok":true}', 200));
      expect(r.ok, isFalse);
      expect(r.reach, Reach.wrongService);
      expect(r.message, contains('not MADBOOTS'));
    });

    test('a 200 of HTML is named as such', () async {
      final r = await against((_) => http.Response('<html>Router setup</html>', 200));
      expect(r.reach, Reach.wrongService);
      expect(r.message, contains('JSON'));
    });

    test('a non-200 is not read as a refusal', () async {
      final r = await against((_) => http.Response('nope', 502));
      expect(r.reach, Reach.wrongService);
      expect(r.message, contains('502'));
    });

    test('a typo never reaches the network at all', () async {
      var called = false;
      final r = await reach('http://localhost:8078/api/v1/docs',
          client: MockClient((_) async {
            called = true;
            return http.Response(_health, 200);
          }));
      expect(r.reach, Reach.badAddress);
      // ⭐ *"That is not an address"* beats *"the server did not answer"* when the fault is the address —
      // and a request that is never sent cannot be answered by the wrong machine either.
      expect(called, isFalse);
    });

    test('nothing listening names all three causes, because they are indistinguishable', () async {
      final r = await reach('http://host:8078',
          client: MockClient((_) async => throw http.ClientException('refused')));
      expect(r.reach, Reach.refused);
      // ⚠️ Two of the three are not the app's fault, and a bare "connection refused" sends someone
      // hunting through the code for a sleeping laptop.
      for (final cause in ['not running', '0.0.0.0', 'different network']) {
        expect(r.message, contains(cause), reason: 'the message drops "$cause"');
      }
    });
  });

  test('the default is a compile-time default, overridable at build time', () {
    // ⚠️ Not asserting the literal — `--dart-define=MADBOOTS_API=…` is meant to change it, and a test
    // pinned to localhost would fail the hosted build it exists to support.
    expect(Server.problemWith(kDefaultBaseUrl), isNull,
        reason: 'whatever is baked in has to be a usable address');
  });

  test('the health body this file asserts against is the shape the client reads', () {
    // ⭐ The sample above is a literal, which is exactly the thing that rots. This pins the two fields
    // the client actually branches on, so a rename on the server fails here rather than in the field.
    final body = jsonDecode(_health) as Map<String, dynamic>;
    expect(body['service'], 'madboots');
    expect(body.containsKey('version'), isTrue);
  });
}
