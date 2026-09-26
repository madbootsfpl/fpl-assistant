/// How old the numbers are, on the pitch (ADR-303).
///
/// ⚠️⚠️ **The stale banner could not see this**, because it fires only when a completed gameweek has no
/// rows — and *a five-hour-old row is still a row*. ⭐ This is the quiet counterpart: no colour, no icon,
/// no border. The banner means **a gameweek is missing**; this means **it has been a while**, and
/// conflating the two would make the loud one meaningless.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/pitch.dart';

/// The committed sample, with the freshness we want to test.
MyTeam teamAged(int? ageMinutes) {
  final raw = jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>;
  final data = raw['data'] as Map<String, dynamic>;
  if (ageMinutes == null) {
    data.remove('age_minutes');
  } else {
    data['age_minutes'] = ageMinutes;
  }
  return MyTeam.fromJson(raw);
}

Widget screen(Widget child) => MaterialApp(
  home: Scaffold(
    backgroundColor: const Color(0xFF17131F),
    body: SizedBox(width: 390, height: 760, child: child),
  ),
);

Future<void> pumpPitch(
  WidgetTester tester,
  MyTeam team, {
  int? gameweek,
}) async {
  await tester.pumpWidget(
    screen(
      PitchView(
        team: team,
        mode: PitchMode.nextGw,
        onMode: (_) {},
        onTapPlayer: (_) {},
        gameweek: gameweek,
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('fresh data says nothing at all', (tester) async {
    // ⭐ *A notice that is always on is a decoration* (ADR-248). Measured gaps run 2h27m to 5h41m, so the
    // threshold has to sit above the normal case rather than at it.
    await pumpPitch(tester, teamAged(20));
    expect(find.textContaining('old'), findsNothing);
  });

  testWidgets('data old enough to matter says so, quietly', (tester) async {
    await pumpPitch(tester, teamAged(5 * 60));

    expect(find.text('5h old'), findsOneWidget);
    // ⚠️ And it is **not** the warning banner: no colour, no icon, no border.
    final label = tester.widget<Text>(find.text('5h old'));
    expect(label.style?.color, isNot(Brand.warn));
    expect(label.style!.fontSize! < 12, isTrue, reason: 'it is shouting');
  });

  testWidgets('three hours is the line', (tester) async {
    // ⭐ Two missed hourly refreshes, not one — pinned so the threshold is a decision rather than a drift.
    await pumpPitch(tester, teamAged(179));
    expect(find.textContaining('old'), findsNothing);

    await pumpPitch(tester, teamAged(180));
    expect(find.text('3h old'), findsOneWidget);
  });

  testWidgets('a forward page does not carry it', (tester) async {
    // ⚠️ The header there already says *"projected"* — ⭐ *the age of the board is a fact about now*, and
    // a GW9 page is not about now.
    await pumpPitch(tester, teamAged(5 * 60), gameweek: 9);
    expect(find.textContaining('old'), findsNothing);
  });

  testWidgets(
    'an older server that sends no age says nothing, rather than zero',
    (tester) async {
      // ⚠️⚠️ *A field added on one side must not blank a line that was working on the other*, and it must
      // certainly not claim the data is brand new.
      await pumpPitch(tester, teamAged(null));
      expect(find.textContaining('old'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  group('the age comes from the server, not the device clock', () {
    test('because a phone an hour fast would lie about it', () {
      final team = teamAged(240);
      expect(team.data.ageMinutes, 240);
      expect(team.data.since, '4 hours ago');
      expect(team.data.shortAge, '4h old');
      expect(team.data.isOld, isTrue);

      // ⭐⭐ **And `age` prefers it over the device clock.** The sample's `refreshed_at` is days old, so
      // a device-clock reading would say "days ago" where the server says four hours — ⚠️ *a phone an
      // hour fast would tell its owner the data was an hour staler than it is*, and the banner reads
      // this same getter.
      expect(team.data.age, '4 hours ago');
      expect(
        DateTime.now().toUtc().difference(team.data.refreshedAt!).inHours,
        greaterThan(24),
        reason: 'the sample is too recent for this test to distinguish the two',
      );
    });

    test(
      'and an older server still gets a readable line from its timestamp',
      () {
        // ⭐ The fallback: `refreshed_at` has always been sent, so the banner's own line keeps working.
        final team = teamAged(null);
        expect(team.data.ageMinutes, isNull);
        expect(team.data.age, isNot('unknown'));
        expect(team.data.isOld, isFalse);
      },
    );

    test('never refreshed reads as unknown, never as "just now"', () {
      final freshness = DataFreshness(
        refreshedAt: null,
        missingGameweeks: const [],
        behind: false,
        why: '',
      );
      expect(freshness.since, 'unknown');
      expect(freshness.age, 'unknown');
      expect(freshness.shortAge, '');
      expect(freshness.isOld, isFalse);
    });
  });
}
