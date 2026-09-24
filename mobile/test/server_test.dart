/// The API's address, and what the app says when it is wrong (ADR-239).
///
/// ⭐⭐ **The reason this is worth testing at all is that every failure here looks the same from the phone.**
/// A sleeping Mac, a server bound to loopback, a phone on 4G instead of the Wi-Fi, a typo, and a router
/// admin page answering 200 are five different problems with one symptom. The app's only job is to tell
/// them apart, so the tests are one per confusion rather than one per function.
library;

import 'dart:convert';

import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/server.dart';

/// ⭐ The real `/api/v1/health` body, copied from what the route returns — see
/// `tests/test_service_health.py`, which asserts the server keeps returning exactly this.
const _health =
    '{"ok": true, "service": "madboots", "version": "0.0.1", "usage": "off"}';

void main() {
  _retryAffordance();
  _refusedWording();
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
      expect(
        Server.tidy('https://api.madboots.app'),
        'https://api.madboots.app',
      );
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
      await reach(
        'http://host:8078/',
        client: MockClient((r) async {
          asked = r.url;
          return http.Response(_health, 200);
        }),
      );
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
      final r = await against(
        (_) => http.Response('<html>Router setup</html>', 200),
      );
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
      final r = await reach(
        'http://localhost:8078/api/v1/docs',
        client: MockClient((_) async {
          called = true;
          return http.Response(_health, 200);
        }),
      );
      expect(r.reach, Reach.badAddress);
      // ⭐ *"That is not an address"* beats *"the server did not answer"* when the fault is the address —
      // and a request that is never sent cannot be answered by the wrong machine either.
      expect(called, isFalse);
    });

    test('nothing listening names all three causes, because they are indistinguishable', () async {
      final r = await reach(
        'http://host:8078',
        client: MockClient((_) async => throw http.ClientException('refused')),
      );
      expect(r.reach, Reach.refused);
      // ⚠️ Most of these are not the app's fault, and two are permissions a person has to grant that
      // never announce themselves again once denied. A bare "connection refused" sends someone hunting
      // through the code for a phone that is on 4G.
      for (final cause in [
        'Local Network',
        'same Wi-Fi',
        'awake',
        'address change',
      ]) {
        expect(
          r.message,
          contains(cause),
          reason: 'the message drops "$cause"',
        );
      }
    });
  });

  test('the refusal never tells a phone to run a server command', () {
    // ⚠️⚠️ **The message this replaced said `venv/bin/python -m uvicorn …`** — a command you cannot run
    // on the device you are holding, for a server that was already running. ⭐ *Advice written for the
    // machine the developer sits at stops being advice once the client is a handset.*
    final message = refusedMessage('http://192.168.1.35:8078');
    for (final desktopism in ['venv/', 'uvicorn', 'python']) {
      expect(
        message.toLowerCase(),
        isNot(contains(desktopism)),
        reason: 'the message tells a phone to run "$desktopism"',
      );
    }
    expect(
      message,
      contains('Settings'),
      reason: 'it has to say where the address is changed',
    );
  });

  test(
    'the Settings check and a failed call explain it the same way',
    () async {
      // ⭐ Two doors to one room drift apart (ADR-184). The check would be worthless if it disagreed with
      // the screen that sent you to it.
      final fromCheck = await reach(
        'http://host:8078',
        client: MockClient((_) async => throw http.ClientException('refused')),
      );
      expect(fromCheck.message, refusedMessage('http://host:8078'));
    },
  );

  test('the default is a compile-time default, overridable at build time', () {
    // ⚠️ Not asserting the literal — `--dart-define=MADBOOTS_API=…` is meant to change it, and a test
    // pinned to localhost would fail the hosted build it exists to support.
    expect(
      Server.problemWith(kDefaultBaseUrl),
      isNull,
      reason: 'whatever is baked in has to be a usable address',
    );
  });

  test(
    'the health body this file asserts against is the shape the client reads',
    () {
      // ⭐ The sample above is a literal, which is exactly the thing that rots. This pins the two fields
      // the client actually branches on, so a rename on the server fails here rather than in the field.
      final body = jsonDecode(_health) as Map<String, dynamic>;
      expect(body['service'], 'madboots');
      expect(body.containsKey('version'), isTrue);
    },
  );
}

/// The refused message tells the reader about **their** deployment (ADR-288).
///
/// ⭐⭐ **One wording served two situations that fail for unrelated reasons.** A tester on the hosted
/// service, whose only problem was a server waking up, was told to check their Wi-Fi, grant a Local
/// Network permission, and see whether a shell script was running on a computer they do not own.
void _refusedWording() {
  group('which explanation a reader gets', () {
    test('a machine on the network gets the developer advice', () {
      for (final base in const [
        'http://192.168.1.35:8078',
        'http://10.0.2.2:8078',
        'http://localhost:8078',
        'http://127.0.0.1:8078',
        'http://mac.local:8078',
        'http://172.16.4.2:8078',
      ]) {
        expect(isLocalAddress(base), isTrue, reason: base);
        expect(refusedMessage(base), contains('same Wi-Fi'));
      }
    });

    test('the hosted service gets the reason it actually failed', () {
      final message = refusedMessage('https://madboots-api.onrender.com');

      expect(message, contains('sleeps'));
      // ⚠️ None of the developer advice. *An error message that describes somebody else's setup sends
      // the reader to fix something that was never broken.*
      expect(message, isNot(contains('Wi-Fi')));
      expect(message, isNot(contains('serve_api.sh')));
      expect(message, isNot(contains('Local Network')));
      // ⭐ And a way out that is not "go and read a runbook".
      expect(message, contains('Try again'));
    });

    test('172.32 is not somebody\'s kitchen table', () {
      // ⚠️ 172.16–172.31 is private; a `startsWith("172.")` would claim half the public internet is on
      // the reader's own network and hand them the wrong advice.
      expect(isLocalAddress('http://172.16.0.1'), isTrue);
      expect(isLocalAddress('http://172.31.255.1'), isTrue);
      expect(isLocalAddress('http://172.32.0.1'), isFalse);
      expect(isLocalAddress('http://172.15.0.1'), isFalse);
    });

    test(
      'a hostname that merely starts with a private prefix is not local',
      () {
        expect(isLocalAddress('https://10-0-0-1.example.com'), isFalse);
        expect(isLocalAddress('https://localhost.evil.com'), isFalse);
      },
    );

    test('plain HTTP on an explicit port is a machine on this network', () {
      // ⭐ The shape `scripts/serve_api.sh` produces, and the one case a private-range check cannot
      // catch: `http://mac:8078` is a hostname with no address in it at all.
      expect(isLocalAddress('http://host:8078'), isTrue);
      expect(isLocalAddress('http://mac:8078'), isTrue);
      // ⚠️ But the hosted service is HTTPS, and must not be mistaken for one.
      expect(isLocalAddress('https://madboots-api.onrender.com'), isFalse);
    });

    test('a private address is local on its own merits', () {
      // ⚠️⚠️ **Without the port, or the range check is never exercised.** Every earlier example here was
      // `http://…:8078`, so the explicit-port rule answered first and a mutation deleting the whole
      // private-range branch survived — ⭐ *two rules that both return true make each other untestable,
      // and the test suite reports the pair as covered.*
      expect(isLocalAddress('https://192.168.1.35'), isTrue);
      expect(isLocalAddress('https://10.0.2.2'), isTrue);
      expect(isLocalAddress('https://172.20.0.5'), isTrue);
      expect(isLocalAddress('https://mac.local'), isTrue);
    });
  });
}

/// The retry that did not exist (ADR-288).
///
/// ⚠️⚠️ **The commonest failure in this app is also the most temporary** — the service sleeps when idle
/// and takes seconds to wake — and until now the only way out of the error screen was to force-quit.
/// ⭐ *An error a second attempt would fix, with no way to make a second attempt, is an error that reads
/// as broken.*
void _retryAffordance() {
  final main = File('lib/main.dart').readAsStringSync();
  final client = File('lib/api/client.dart').readAsStringSync();

  group('a failed load offers a way back', () {
    test('the error screen carries a button', () {
      expect(main, contains("child: const Text('Try again')"));
      expect(main, contains('onPressed: _retry'));
    });

    test('retrying replaces the future through setState', () {
      // ⚠️ *Or the screen keeps showing the error it is being asked to leave.*
      expect(
        main,
        contains('void _retry() => setState(() => _team = _load(_managerId));'),
      );
    });

    test('the message names the button that exists', () {
      // ⚠️⚠️ **It said "Pull down to try again" and there is no pull-to-refresh in this app** — the same
      // fault as the advice it replaced: ⭐ *telling the reader to do something the screen cannot do.*
      final hosted = refusedMessage('https://madboots-api.onrender.com');

      expect(hosted, contains('Try again'));
      expect(hosted, isNot(contains('Pull down')));
      expect(client, isNot(contains('Pull down')));
    });
  });
}
