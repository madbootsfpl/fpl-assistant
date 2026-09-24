/// Transfers moved under This Week, and Signals took the tab (ADR-283).
///
/// ⭐⭐ **These screens had no widget tests at all**, which is how a nav change and a new required
/// constructor argument passed 287 tests without asserting anything. ⚠️ *A suite that stays green
/// through a rewiring is not confirming the rewiring; it is silent about it.*
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/this_week_view.dart';

String sampleText(String name) =>
    File('../spikes/018-flutter-read-slice/api-samples/$name.json')
        .readAsStringSync();

MyTeam team() =>
    MyTeam.fromJson(jsonDecode(sampleText('my-team')) as Map<String, dynamic>);

/// ⭐ The real parsing runs, so a test that passes here is a path the app passes.
ServiceClient sampleClient() => ServiceClient(
  baseUrl: 'http://test',
  client: MockClient((request) async {
    final body = request.url.path.contains('gameweek')
        ? sampleText('gameweek-plan')
        : '{}';
    return http.Response(
      body,
      200,
      headers: {'content-type': 'application/json; charset=utf-8'},
    );
  }),
);

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(backgroundColor: Brand.ink, body: child),
);

Future<void> pumpThisWeek(WidgetTester tester, {VoidCallback? onTap}) async {
  // ⚠️⚠️ **A tall surface, and that is not cosmetic.** This Week scrolls, so on the default 800×600 test
  // window the list stops building at the Lineup card — the Transfer card, the button and Timing are
  // never constructed. ⭐ *A widget test on a short window asserts about the top of the page and reports
  // it as the whole page*, and the first run of these tests failed for exactly that reason.
  tester.view.physicalSize = const Size(1200, 5000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    // ⭐ No scroll wrapper: `ThisWeekView` supplies its own, and nesting two is an unbounded-height
    // assertion rather than a failed expectation.
    wrap(
      ThisWeekView(
        client: sampleClient(),
        team: team(),
        onApply: (_) async {},
        onAlternatives: onTap ?? () {},
      ),
    ),
  );
  // ⭐ Two pumps, not `pumpAndSettle`: the loading spinner animates forever and settling
  // against it is a timeout, not a wait.
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 50));
}

void main() {
  group('the way into the transfer board', () {
    testWidgets('This Week offers it', (tester) async {
      await pumpThisWeek(tester);

      expect(find.text('See transfer alternatives'), findsOneWidget);
    });

    testWidgets('tapping it calls back', (tester) async {
      var opened = 0;
      await pumpThisWeek(tester, onTap: () => opened++);

      await tester.tap(find.text('See transfer alternatives'));
      await tester.pump();

      expect(opened, 1);
    });

    testWidgets('it sits between the transfer and the timing', (tester) async {
      // ⚠️⚠️ **The owner asked for this position specifically**, and position is the whole point: the
      // button answers the card above it. ⭐ *A button that drifts to the bottom of the page is a
      // different feature wearing the same label.*
      await pumpThisWeek(tester);

      final labels = tester
          .widgetList<Text>(find.byType(Text))
          .map((t) => t.data ?? '')
          .toList();
      // ⚠️ The card renders its label uppercased, so the source spelling ('Transfer') finds nothing —
      // ⭐ *asserting against what the code says rather than what the screen shows is how a passing test
      // describes a page nobody sees.*
      final transfer = labels.indexOf('TRANSFER');
      final button = labels.indexOf('See transfer alternatives');
      final timing = labels.indexOf('TIMING');

      expect(transfer, isNonNegative, reason: 'no Transfer card rendered');
      expect(timing, isNonNegative, reason: 'no Timing card rendered');
      expect(button, greaterThan(transfer));
      expect(button, lessThan(timing));
    });
  });

  group('the bottom navigation', () {
    // ⚠️ `_Tab` is private to main.dart, so this reads the source. ⭐ *A guard that cannot reach the
    // thing it guards is still worth having when the alternative is no guard* — and the mistake it
    // catches (a tab left in the row, or two rows disagreeing) is exactly a spelling mistake.
    final main = File('lib/main.dart').readAsStringSync();

    test('Signals has the slot and Transfers does not', () {
      expect(
        main,
        contains('enum _Tab { myTeam, thisWeek, signals, players, more }'),
      );
      expect(
        main.contains('_Tab.transfers'),
        isFalse,
        reason: 'a Transfers tab is still referenced somewhere',
      );
    });

    test('the label and the icon moved together', () {
      // ⭐ Three switches key off this enum — label, icon, body. Dart makes the third exhaustive; the
      // first two would happily keep saying "Transfers" over a Signals screen.
      expect(main, contains("_Tab.signals => 'Signals',"));
      expect(main, contains('_Tab.signals => Icons.campaign_outlined,'));
      expect(main.contains("=> 'Transfers',"), isFalse);
      expect(main.contains('=> Icons.swap_horiz,'), isFalse);
    });

    test('Signals reports what it has marked seen', () {
      // ⚠️⚠️ As a pushed screen the caller re-read the count on the way back. A tab is never come back
      // from — ⭐ *without this the badge sits there while you read the thing it points at.*
      expect(main, contains('onSeen:'));
      expect(
        File('lib/signals_view.dart').readAsStringSync(),
        contains('widget.onSeen?.call();'),
      );
    });
  });

  group('what the app says about a plan', () {
    final main = File('lib/main.dart').readAsStringSync();

    test('the draft banner does not deny whose team this is', () {
      // ⚠️ *"A plan — not your FPL team"* landed three minutes after a message that genuinely was an
      // identity error, and read as the same complaint twice.
      expect(main.contains("'A plan — not your FPL team'"), isFalse);
      expect(main, contains("'Your plan — not saved to FPL yet'"));
    });

    test('a cleared plan says it will not happen again', () {
      // ⭐ The old wording was true about the machine and silent about the cause, which reads as a fault.
      expect(
        main.contains(
          "'That plan belonged to a different manager id. Cleared.'",
        ),
        isFalse,
      );
      expect(main, contains('Plans you make from now on are kept.'));
    });
  });
}
