/// The web app can tell you it is out of date (ADR-339).
///
/// 🔴 **The owner reported a bug that was not one**: a bank that went negative but did not go red. The
/// server had deployed on push; his browser tab had not. ⭐ *An app that cannot tell you it is stale
/// makes every stale symptom look like a defect* — and the one he hit looked exactly like the feature
/// being half-built.
///
/// ⚠️ Web was silenced along with iOS, and the reasoning only fitted iOS: *"a notice is a promise that
/// tapping it will help"*, and an iPhone cannot use an APK. A browser can refresh.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/main.dart';
import 'package:madboots/update_check.dart';

void main() {
  http.Client manifest(List<String> hits) => MockClient((request) async {
    hits.add('${request.url}');
    return http.Response(
      '{"version":"1.0.0","build":40,"url":"u","notes":["something"]}',
      200,
    );
  });

  test('a browser IS asked to check, where an iPhone is not', () async {
    // ⭐⭐ **The branch a Mac test run cannot otherwise reach.** `kIsWeb` is a compile-time constant, so
    // without the override this assertion would pass by never running the web path at all — ⚠️ *which
    // is precisely how the iOS banner shipped offering an iPhone an APK* (ADR-282).
    final hits = <String>[];
    final found = await published(
      client: manifest(hits),
      selfHosted: false,
      onWeb: true,
    );

    expect(hits, isNotEmpty, reason: 'the web never asked for the manifest');
    expect(found?.build, 40);
  });

  test('and neither route means no request at all', () async {
    final hits = <String>[];
    expect(
      await published(client: manifest(hits), selfHosted: false, onWeb: false),
      isNull,
    );
    expect(hits, isEmpty, reason: 'an iPhone fetched a manifest it cannot use');
  });

  testWidgets('the web banner says refresh, and offers nothing to tap', (
    tester,
  ) async {
    // ⚠️⚠️ *A notice is a promise that tapping it will help.* The manifest describes an **APK** — on the
    // web the help is a refresh, which the reader does, not the app.
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: UpdateBanner(
            available: Available(version: '1.0.0', build: 40, url: 'u'),
            onWeb: true,
          ),
        ),
      ),
    );

    expect(find.textContaining('Refresh the page'), findsOneWidget);
    expect(find.textContaining('Tap to update'), findsNothing);
    expect(
      find.byIcon(Icons.chevron_right),
      findsNothing,
      reason: 'a chevron promises a tap that does nothing here',
    );
    expect(find.byType(GestureDetector), findsNothing);
  });

  testWidgets('and off the web it still offers the download', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: UpdateBanner(
            available: Available(version: '1.0.0', build: 40, url: 'u'),
            onWeb: false,
          ),
        ),
      ),
    );

    expect(find.textContaining('Tap to update'), findsOneWidget);
    expect(find.byIcon(Icons.chevron_right), findsOneWidget);
  });

  test('a newer build is newer, and the same build is not', () {
    // ⭐ The comparison the banner turns on — pinned here because the web path now depends on it too.
    const here = 39;
    expect(
      isNewer(
        available: const Available(version: '1.0.0', build: 40, url: 'u'),
        runningBuild: here,
      ),
      isTrue,
    );
    expect(
      isNewer(
        available: const Available(version: '1.0.0', build: 39, url: 'u'),
        runningBuild: here,
      ),
      isFalse,
    );
    expect(
      isNewer(
        available: const Available(version: '1.0.0', build: 38, url: 'u'),
        runningBuild: here,
      ),
      isFalse,
      reason: 'an older published build must never prompt',
    );
  });

  test('a missing manifest never prompts', () {
    // ⚠️ Null on every failure — offline, a typo, a half-deployed site serving HTML.
    expect(isNewer(available: null, runningBuild: 39), isFalse);
  });
}
