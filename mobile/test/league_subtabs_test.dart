/// Transfers, Rank, Chips and Awards (ADR-287).
///
/// ⭐⭐ **Parked as unbuilt while the data was already arriving.** `withCaptains` spends one request per
/// manager, and that payload carries `active_chip` and an `entry_history` holding the overall rank, the
/// transfer count, the hit and the bench points — ⚠️ *four tabs' worth of answers, fetched and
/// discarded.*
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/leagues_view.dart';

LeagueTable table() => LeagueTable.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/league.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(backgroundColor: Brand.ink, body: child),
);

/// ⚠️ A tall surface: these are lists, and the default 800×600 window stops building them part-way —
/// ⭐ *a widget test on a short window asserts about the top of the page and reports it as the whole
/// page* (ADR-285's lesson, one screen along).
Future<void> open(WidgetTester tester, Widget view) async {
  tester.view.physicalSize = const Size(420, 2000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(wrap(view));
  await tester.pump();
}

void main() {
  group('the sample is worth testing against', () {
    test('it has managers who differ on every column', () {
      final t = table();

      expect(t.managers.length, greaterThan(1));
      // ⚠️⚠️ **The stub used to omit `entry_history` entirely**, so every one of these was null and the
      // sample documented the empty screen — ⭐ *a fixture where nothing differs makes every difference
      // disappear.*
      expect(t.managers.map((m) => m.points).toSet().length, t.managers.length);
      expect(t.managers.any((m) => m.chip != null), isTrue);
      expect(t.managers.any((m) => (m.hit ?? 0) > 0), isTrue);
      expect(t.managers.any((m) => (m.benchPoints ?? 0) > 0), isTrue);
    });

    test('the overall rank is not the league rank', () {
      // ⭐ The whole point of the Rank tab: where you are in the world, not among eleven people.
      expect(table().managers.first.overallRank, greaterThan(1000));
    });
  });

  group('Transfers', () {
    testWidgets('shows each manager and what their moves cost', (tester) async {
      await open(
        tester,
        LeagueManagers(table: table(), column: LeagueColumn.transfers),
      );
      final t = table();

      for (final m in t.managers) {
        expect(find.text(m.manager!), findsOneWidget);
      }
      // ⚠️ The hit, not just the count — *three transfers for nothing and three for minus eight are
      // different weeks.*
      final hit = t.managers.firstWhere((m) => (m.hit ?? 0) > 0);
      expect(find.text('−${hit.hit}'), findsOneWidget);
    });

    testWidgets('adds the league up so the reader does not', (tester) async {
      await open(
        tester,
        LeagueManagers(table: table(), column: LeagueColumn.transfers),
      );
      final moves = table().managers.fold(0, (a, m) => a + (m.transfers ?? 0));

      expect(
        find.textContaining('The league made $moves transfer'),
        findsOneWidget,
      );
    });
  });

  group('Rank', () {
    testWidgets('groups the digits', (tester) async {
      // ⚠️ Seven digits unseparated are unreadable at a glance, and this column exists to be glanced at.
      await open(
        tester,
        LeagueManagers(table: table(), column: LeagueColumn.rank),
      );

      expect(find.text('3,842,466'), findsOneWidget);
      expect(find.text('41,206'), findsOneWidget);
    });

    testWidgets('says how many squads it stands on', (tester) async {
      // ⭐ *A partial read must never present itself as the whole league* (ADR-215).
      await open(
        tester,
        LeagueManagers(table: table(), column: LeagueColumn.rank),
      );

      // ⚠️ The **whole** sentence. `'3 squad'` was still true when the wording dropped "read" and just
      // said "from 3 squads" — ⭐ *a prefix a mutation still satisfies is not a test of the mutation*,
      // and "read" is the word that makes this a count of what was fetched rather than a league size.
      expect(
        find.text(
          'Overall rank across the game, from ${table().captainsFrom} squads read.',
        ),
        findsOneWidget,
      );
    });
  });

  group('Chips', () {
    testWidgets('names the chip in FPL\'s own words', (tester) async {
      // ⚠️ *An app that renames the game's moves makes the manager translate.*
      await open(
        tester,
        LeagueManagers(table: table(), column: LeagueColumn.chip),
      );

      expect(find.text('Bench Boost'), findsOneWidget);
      expect(find.text('bboost'), findsNothing);
    });

    testWidgets('a manager with no chip gets a dash, not a blank', (
      tester,
    ) async {
      // ⭐ *"No chip" is an answer, and an empty cell looks like a missing one.*
      await open(
        tester,
        LeagueManagers(table: table(), column: LeagueColumn.chip),
      );
      final none = table().managers.where((m) => m.chip == null).length;

      expect(find.text('—'), findsNWidgets(none));
    });
  });

  group('Awards', () {
    testWidgets('the app supplies the title, the server the winner', (
      tester,
    ) async {
      await open(tester, LeagueAwards(table: table()));
      final winner = table().awards.firstWhere(
        (a) => a.kind == 'gameweek_winner',
      );

      expect(find.text('Gameweek winner'), findsOneWidget);
      expect(
        find.text('${winner.manager} — ${winner.value} pts'),
        findsOneWidget,
      );
      // ⚠️ The server must not be sending words — *a client that has to take a sentence apart to lay it
      // out will one day take it apart differently* (ADR-286).
      expect(find.text('Gameweek winner'), findsOneWidget);
    });

    testWidgets('the wasted bench is named as wasted', (tester) async {
      await open(tester, LeagueAwards(table: table()));
      final bench = table().awards.firstWhere((a) => a.kind == 'worst_bench');

      expect(find.text('Worst bench'), findsOneWidget);
      expect(
        find.text('${bench.manager} — ${bench.value} pts left on the bench'),
        findsOneWidget,
      );
    });
  });
}
