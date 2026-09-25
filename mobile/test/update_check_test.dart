/// The update check (ADR-282).
///
/// ⭐ Every test here is about **not causing harm**: a check that throws, blocks, or cries wolf is worse
/// than no check at all, because the app worked fine before it existed.
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/update_check.dart';

http.Client _serving(int status, String body) =>
    MockClient((_) async => http.Response(body, status));

void main() {
  _notes();
  group('published', () {
    test('reads the manifest', () async {
      final available = await published(
        client: _serving(
          200,
          jsonEncode({
            'version': '1.0.1',
            'build': 4,
            'url': 'https://madboots.com/app/madboots.apk',
          }),
        ),
      );

      expect(available, isNotNull);
      expect(available!.build, 4);
      expect(available.version, '1.0.1');
      expect(available.url, 'https://madboots.com/app/madboots.apk');
    });

    test('asks the site, not the API', () async {
      late Uri asked;
      await published(
        client: MockClient((request) async {
          asked = request.url;
          return http.Response('{}', 200);
        }),
      );

      expect(asked.toString(), kManifestUrl);
      // ⚠️ The manifest sits beside the APK, so the two cannot describe different builds.
      expect(asked.path, endsWith('/app/version.json'));
    });

    test('is null when the site 404s', () async {
      // ⚠️ With a **valid manifest body**, deliberately. A 404 whose body is also unparseable is
      // rejected twice over, and ⭐ *a test that two guards both satisfy cannot tell you either one
      // is still there* — this one fails the moment the status check goes.
      expect(
        await published(
          client: _serving(404, '{"version":"9.9.9","build":99,"url":"x"}'),
        ),
        isNull,
      );
    });

    test('is null when the site serves HTML', () async {
      // ⭐ A half-deployed Pages site answers 200 with its own index page.
      expect(await published(client: _serving(200, '<!doctype html>')), isNull);
    });

    test('is null when the manifest is JSON but not an object', () async {
      // ⚠️ Separate from the HTML case: `[]` **parses**, so only the shape check rejects it. Unparseable
      // bodies are caught by the `try`, which would hide a missing guard here.
      expect(await published(client: _serving(200, '[]')), isNull);
    });

    test('is null when the manifest has no build number', () async {
      // ⚠️ Rather than a build 0 that every running build would look newer than.
      expect(
        await published(client: _serving(200, '{"version":"1.0.1"}')),
        isNull,
      );
    });

    test('never throws when the network does', () async {
      expect(
        await published(
          client: MockClient((_) async => throw const SocketExceptionish()),
        ),
        isNull,
      );
    });

    test('gives up rather than hanging', () async {
      final available = await published(
        client: MockClient((_) async {
          await Future<void>.delayed(const Duration(seconds: 2));
          return http.Response('{"build":9}', 200);
        }),
        timeout: const Duration(milliseconds: 40),
      );

      expect(available, isNull);
    });
  });

  group('isNewer', () {
    Available at(int build) =>
        Available(version: '1.0.0', build: build, url: 'https://x/a.apk');

    test('a higher build is newer', () {
      expect(isNewer(available: at(3), runningBuild: 2), isTrue);
    });

    test('the same build is not', () {
      expect(isNewer(available: at(2), runningBuild: 2), isFalse);
    });

    test('an older build is not', () {
      // ⭐ A tester running a build newer than the site (mine, usually) is not prompted to downgrade.
      expect(isNewer(available: at(1), runningBuild: 2), isFalse);
    });

    test('a failed check is not', () {
      expect(isNewer(available: null, runningBuild: 2), isFalse);
    });

    test('ignores the version name', () {
      // ⚠️⚠️ The whole point: `1.0.0` ships many times in a beta, so the name cannot be the comparison.
      expect(
        isNewer(
          available: Available(version: '9.9.9', build: 2, url: 'https://x'),
          runningBuild: 2,
        ),
        isFalse,
      );
    });
  });
}

class SocketExceptionish implements Exception {
  const SocketExceptionish();
}

/// What changed, carried into the banner (ADR-296).
///
/// ⭐⭐ **The field shipped empty in ADR-282 and stayed empty**, because nothing produced it. Now the
/// release derives it from its own commits — and the client has to read both shapes, because manifests
/// already published carry `"notes": ""`.
void _notes() {
  Available parse(Object? notes) => Available.fromJson({
    'version': '1.0.1',
    'build': 4,
    'url': 'https://x/a.apk',
    'notes': notes,
  });

  group('reading what changed', () {
    test('a list arrives as a list', () {
      expect(parse(['Landscape fixed', 'Faster search']).notes, [
        'Landscape fixed',
        'Faster search',
      ]);
    });

    test(
      'an older manifest\'s empty string is no notes, not one blank note',
      () {
        // ⚠️⚠️ **The shape already on the website.** ⭐ *A reader that only understands the new format
        // makes every older release unreadable, which is the opposite of what a version check is for.*
        expect(parse('').notes, isEmpty);
        expect(parse('   ').notes, isEmpty);
      },
    );

    test('an older manifest with real text still says it', () {
      expect(parse('Landscape fixed').notes, ['Landscape fixed']);
    });

    test('a missing field is no notes', () {
      expect(
        Available.fromJson({'version': '1.0.1', 'build': 4, 'url': 'x'}).notes,
        isEmpty,
      );
    });

    test('blank entries are dropped rather than rendered', () {
      // ⭐ A bullet with nothing after it is a bug the reader has to interpret.
      expect(parse(['Real note', '', '  ']).notes, ['Real note']);
    });

    test('whitespace does not survive into the banner', () {
      expect(parse(['  Landscape fixed  ']).notes, ['Landscape fixed']);
    });

    test('a busy week is capped, in one place', () {
      // ⚠️⚠️ **The cap used to live in three places** — the model, the release script and the banner's
      // own `take(3)` — and mutating any one left the other two passing. ⭐ *A cap enforced in several
      // places is a cap that moves*; the banner now renders whatever this returns.
      final many = [for (var i = 0; i < 9; i++) 'Change number $i'];

      expect(parse(many).notes.length, kMaxNotes);
      expect(parse(many).notes.first, 'Change number 0');
    });
  });
}
