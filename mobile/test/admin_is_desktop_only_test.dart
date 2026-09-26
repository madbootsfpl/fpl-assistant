/// The owner's panel is buried, and only where it fits (ADR-305).
///
/// ⚠️⚠️ **Hiding it is tidiness, not security.** The lock is the key check on the server; a phone is
/// simply the wrong shape for a table of medians, and the owner asked for it on the desktop. ⭐ *Saying
/// which of the two a control is doing matters*, because the day someone mistakes the second for the
/// first is the day a secret goes into a binary.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/admin_view.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/settings_view.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

Future<void> pumpSettings(WidgetTester tester, double width) async {
  // ⚠️ **`MediaQuery` is overridden rather than the surface resized.** `setSurfaceSize` did not reach
  // the widget in this harness and the results came back **inverted** — the narrow case showing the
  // panel and the wide case hiding it. ⭐ *A test whose setup silently does nothing produces confident
  // nonsense*, and the give-away was that both assertions failed at once.
  await tester.pumpWidget(
    MaterialApp(
      // ⚠️⚠️ **Inside `MaterialApp`, not around it.** `MaterialApp` installs its own `MediaQuery` from
      // the view, so an override above it is simply discarded — ⭐ *a setup that is silently ignored
      // produces confident nonsense*, and this one first reported the narrow case showing the panel and
      // the wide case hiding it, which is the shape of a harness problem rather than a bug.
      home: MediaQuery(
        data: MediaQueryData(size: Size(width, 900)),
        child: Scaffold(
          backgroundColor: const Color(0xFF17131F),
          body: SettingsView(
            team: sampleTeam(),
            client: ServiceClient(baseUrl: 'http://x'),
            managerId: 1,
            freeTransfers: 1,
            baseUrl: 'http://x',
            onManagerId: (_) {},
            onFreeTransfers: (_) {},
            onServer: (_) async {},
          ),
        ),
      ),
    ),
  );
  await tester.pump();
}

/// Settings is a long `ListView`, and ⚠️ *a `ListView` does not mount what is off-screen* — so a test
/// that simply looks for the last section finds nothing whether or not it is there.
Future<void> scrollToBottom(WidgetTester tester) async {
  for (var i = 0; i < 12; i++) {
    await tester.drag(find.byType(ListView).first, const Offset(0, -400));
    await tester.pump();
  }
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('a phone-width Settings has no owner section', (tester) async {
    await pumpSettings(tester, 390);
    await scrollToBottom(tester);

    expect(find.text('OWNER'), findsNothing);
    expect(find.text('Usage stats'), findsNothing);
  });

  testWidgets('a desktop-width Settings offers it, collapsed', (tester) async {
    await pumpSettings(tester, 1100);
    await scrollToBottom(tester);

    expect(find.text('OWNER'), findsOneWidget);
    expect(find.text('Usage stats'), findsOneWidget);
    // ⭐ Buried: the panel itself is not built until it is opened, so nothing is fetched by arriving.
    expect(find.byType(AdminView), findsNothing);
  });

  testWidgets('opening it reveals the panel and asks for a key', (
    tester,
  ) async {
    await pumpSettings(tester, 1100);
    await scrollToBottom(tester);

    await tester.tap(find.text('Usage stats'));
    await tester.pumpAndSettle();

    expect(find.byType(AdminView), findsOneWidget);
    // ⚠️ And still nothing has been requested — *a panel that loads on reveal would spend a rate-limit
    // slot every time the owner scrolled past it.*
    expect(find.text('Enter the key to load.'), findsOneWidget);
  });

  test('the threshold is a shape, not a platform', () {
    // ⭐ The same 600pt the pitch uses to decide a tablet — ⚠️ *a rule that needs a device class is a
    // rule that has not found what it depends on yet* (ADR-293).
    expect(kAdminMinWidth, 600);
  });
}
