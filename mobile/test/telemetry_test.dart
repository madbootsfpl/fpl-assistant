// What the app says about itself, and what it must never say (ADR-280).
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/telemetry.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  group('the install id', () {
    test('is minted once and then reused', () async {
      final first = await Telemetry.installId();
      expect(first, isNotEmpty);
      expect(
        await Telemetry.installId(),
        first,
        reason: 'a new id per call counts one device as many',
      );
    });

    test('is random — two installs do not collide', () async {
      final a = await Telemetry.installId();
      SharedPreferences.setMockInitialValues({});
      final b = await Telemetry.installId();
      expect(a, isNot(b));
    });

    // ⚠️⚠️ An id derived from the manager id would be reversible for anyone holding the list of manager
    // ids — an identifier computed from something personal is that personal thing in a costume.
    test('is not derived from anything', () async {
      final id = await Telemetry.installId();
      expect(id, hasLength(32));
      expect(RegExp(r'^[0-9a-f]+$').hasMatch(id), isTrue);
      expect(id, isNot(contains('2885974')));
    });

    test('can be forgotten, and comes back different', () async {
      final before = await Telemetry.installId();
      await Telemetry.forget();
      // ⭐ An identifier a reader cannot reset is one they cannot decline.
      expect(await Telemetry.installId(), isNot(before));
    });
  });

  group('the headers on every request', () {
    test(
      'carry platform, version and install — and nothing else of ours',
      () async {
        Map<String, String>? sent;
        final client = ServiceClient(
          baseUrl: 'http://test',
          client: MockClient((request) async {
            sent = request.headers;
            return http.Response(
              '{"gameweeks": [], "rows": []}',
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }),
        );
        // ⭐ Exactly what `main()` does — the app resolves the identity once before anything requests.
        await Telemetry.init();
        await client.ticker();

        expect(sent!['x-madboots-platform'], isNotEmpty);
        expect(sent!['x-madboots-version'], kAppVersion);
        expect(sent!['x-madboots-install'], isNotEmpty);

        // ⚠️ The promise: no manager id, no squad, no email anywhere in what we add.
        // ignore: avoid_print
        print('HEADERS: ${sent!.keys.toList()}');
        final ours = sent!.keys.where(
          (k) => k.toLowerCase().startsWith('x-madboots'),
        );
        expect(ours, hasLength(3), reason: 'a fourth header appeared: $ours');
        expect(sent.toString(), isNot(contains('2885974')));
      },
    );

    test('the platform is a platform, not a device model', () {
      // ⭐ "android", not "Pixel 7 Pro" — a model starts to describe somebody's belongings.
      expect(
        Telemetry.platform,
        anyOf('ios', 'android', 'web', 'macos', 'windows', 'linux', 'fuchsia'),
      );
    });
  });

  group('the version', () {
    // ⚠️ A version number kept in two places is one that will disagree with itself — and this is what
    // tells the owner an old build is still in somebody's pocket.
    test('matches pubspec.yaml', () {
      final pubspec = File('pubspec.yaml').readAsLinesSync();
      final line = pubspec.firstWhere((l) => l.startsWith('version:'));
      final declared = line.split(':')[1].trim().split('+').first;
      expect(
        kAppVersion,
        declared,
        reason: 'kAppVersion has drifted from pubspec.yaml',
      );
    });
  });
}
