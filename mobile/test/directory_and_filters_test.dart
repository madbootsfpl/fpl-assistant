/// More is a directory, and a hidden filter says what it is set to (ADR-238).
///
/// ⭐⭐ **These are widget tests because the claims are about what a reader sees.** "Every entry explains
/// itself" and "the chip states its value" cannot be checked by looking at the model layer — ADR-238's whole
/// argument is that a directory holds more than a menu *because of the sentences*, and a test that did not
/// read the rendered text would leave that argument unguarded.
///
/// ⚠️ **The player rows are the committed sample, not a fixture written here** — same rule as
/// `api_models_test.dart`. A hand-made board would let a filter test pass against prices no player has.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/more_view.dart';
import 'package:madboots/players_view.dart';
import 'package:madboots/settings_view.dart';

String sampleText(String name) {
  final file = File('../spikes/018-flutter-read-slice/api-samples/$name.json');
  if (!file.existsSync()) {
    throw StateError(
      'missing ${file.absolute.path} — run regenerate_samples.py',
    );
  }
  return file.readAsStringSync();
}

/// ⭐ A client whose transport is the committed sample: the real `players()` parsing runs, so a test that
/// passes here is a test the shipping code path passes.
ServiceClient sampleClient() => ServiceClient(
  baseUrl: 'http://test',
  client: MockClient((request) async {
    if (request.url.path.endsWith('/players')) {
      return http.Response(
        sampleText('players'),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    }
    return http.Response('{}', 404);
  }),
);

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(backgroundColor: const Color(0xFF17131F), body: child),
);

void main() {
  _moreIsADirectory();
  _settingsOwnsItsState();
  _filtersStateTheirValue();
}

void _moreIsADirectory() {
  group('More is a directory', () {
    Widget more({int managerId = 2885974, int freeTransfers = 2}) => wrap(
      MoreView(
        managerId: managerId,
        freeTransfers: freeTransfers,
        onOpenChips: () {},
        onOpenTeamDna: () {},
        onOpenPlayerDna: () {},
        onOpenSignals: () {},
        onOpenSettings: () {},
        onOpenTicker: () {},
        onOpenFeedback: () {},
        onOpenHelp: () {},
      ),
    );

    /// ⚠️⚠️ **A tall viewport, because the list now runs past a phone's fold.** A `ListView` does not
    /// build off-screen children, so adding one row silently took the last row out of every test that
    /// looked for it — ⭐ *a test that cannot see a widget reports the same failure as one that is not
    /// there.*
    void tall(WidgetTester tester) {
      tester.view.physicalSize = const Size(500, 2400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
    }

    /// Every directory row, read **from the widget**.
    ///
    /// ⭐⭐ **Derived, not listed.** This was a hand-written list of seven names, so a new row was covered
    /// by nothing until someone remembered to add it — the same failure that let an illegal import
    /// through `_CORE` for the whole life of a package (ADR-261). ⚠️ *A hand-maintained list does not
    /// grow when the thing it describes does.*
    List<String> rowNames(WidgetTester tester) => [
      for (final row in find.byType(InkWell).evaluate())
        (tester
                .widgetList<Text>(
                  find.descendant(
                    of: find.byWidget(row.widget),
                    matching: find.byType(Text),
                  ),
                )
                .first
                .data ??
            ''),
    ];

    testWidgets('every entry explains itself', (tester) async {
      tall(tester);
      await tester.pumpWidget(more());

      final names = rowNames(tester);
      // ⚠️ A guard that finds nothing must fail loudly rather than pass vacuously.
      expect(
        names.length,
        greaterThanOrEqualTo(8),
        reason: 'rows did not render',
      );
      expect(names, contains('Fixture ticker'));

      // ⭐ For each row, a sentence long enough to be an explanation rather than a label. ⚠️ Asserting
      // only that the names render would pass on a bare menu — the thing ADR-238 replaced.
      for (final name in names) {
        final row = find.ancestor(
          of: find.text(name),
          matching: find.byType(InkWell),
        );
        expect(
          row,
          findsOneWidget,
          reason: '$name should be a tappable directory row',
        );

        final texts = tester
            .widgetList<Text>(
              find.descendant(of: row, matching: find.byType(Text)),
            )
            .map((t) => t.data ?? '')
            .where((s) => s != name)
            .toList();
        expect(texts, isNotEmpty, reason: '$name has no description');
        expect(
          texts.first.length,
          greaterThan(40),
          reason: '$name has a label, not a description: "${texts.first}"',
        );
      }
    });

    testWidgets('every entry is reachable and lands somewhere', (tester) async {
      tall(tester);
      final opened = <String>[];
      await tester.pumpWidget(
        wrap(
          MoreView(
            managerId: 1,
            freeTransfers: 1,
            onOpenChips: () => opened.add('Chips'),
            onOpenTeamDna: () => opened.add('Team DNA'),
            onOpenPlayerDna: () => opened.add('Player DNA'),
            onOpenSignals: () => opened.add('Signals'),
            onOpenSettings: () => opened.add('Settings'),
            onOpenTicker: () => opened.add('Fixture ticker'),
            onOpenFeedback: () => opened.add('Tell us something'),
            onOpenHelp: () => opened.add('Help & videos'),
          ),
        ),
      );

      final names = rowNames(tester);
      for (final name in names) {
        await tester.tap(find.text(name));
        await tester.pump();
      }

      // ⚠️ A directory whose rows all fire the *same* callback would satisfy "every row is tappable".
      // ⭐ Each row must land somewhere **different**, and on the destination its own name promises.
      expect(
        opened.toSet().length,
        names.length,
        reason: 'two rows share a destination',
      );
      expect(opened.toSet(), containsAll(names));
    });

    testWidgets('the Settings row states its current value', (tester) async {
      // ⚠️ Settings is the last row, so it went below the fold the moment the directory gained one.
      tall(tester);
      await tester.pumpWidget(more(managerId: 2885974, freeTransfers: 2));
      expect(find.textContaining('Manager 2885974'), findsOneWidget);
      expect(find.textContaining('2 free transfers'), findsOneWidget);

      // ⭐ Singular, because "1 free transfers" is the kind of thing a tester screenshots.
      await tester.pumpWidget(more(freeTransfers: 1));
      expect(find.textContaining('1 free transfer ·'), findsOneWidget);
    });
  });
}

void _settingsOwnsItsState() {
  testWidgets('Settings redraws its own stepper', (tester) async {
    // ⚠️⚠️ **This is the bug the split introduced.** On a pushed route the parent's `freeTransfers` is
    // captured at push time, so a stepper reading it from the constructor tells the parent and redraws
    // nothing — the highlight stays put and the screen looks broken while working perfectly.
    final told = <int>[];
    await tester.pumpWidget(
      wrap(
        SettingsView(
          team: MyTeam.fromJson(
            jsonDecode(sampleText('my-team')) as Map<String, dynamic>,
          ),
          managerId: 1,
          freeTransfers: 1,
          onManagerId: (_) {},
          onFreeTransfers: told.add,
          baseUrl: 'http://test',
          onServer: (_) async {},
        ),
      ),
    );

    Color colourOf(int n) {
      final box = tester.widget<Container>(
        find.ancestor(of: find.text('$n'), matching: find.byType(Container)),
      );
      return ((box.decoration as BoxDecoration?)?.color) ??
          const Color(0x00000000);
    }

    final off = colourOf(3);
    await tester.tap(find.text('3'));
    await tester.pump();

    expect(told, [3], reason: 'the parent still has to hear about it');
    expect(
      colourOf(3),
      isNot(off),
      reason: 'the tapped number did not light up',
    );
  });
}

void _filtersStateTheirValue() {
  group('a hidden filter states its value', () {
    Future<void> openPlayers(WidgetTester tester) async {
      await tester.pumpWidget(
        wrap(PlayersView(client: sampleClient(), owned: const {})),
      );
      await tester.pumpAndSettle();
    }

    testWidgets('it says "any" before it says nothing', (tester) async {
      await openPlayers(tester);
      // ⭐ Not `findsNothing` on a price — the claim is that the chip *reports* the unset state, which a
      // chip labelled plain "Price" would fail while looking fine.
      expect(find.textContaining('any'), findsOneWidget);
    });

    testWidgets('picking a price changes both the chip and the board', (
      tester,
    ) async {
      await openPlayers(tester);
      final all = find.textContaining('players, best first');
      expect(all, findsOneWidget);

      await tester.tap(find.textContaining('Price'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Under £6.0m'));
      await tester.pumpAndSettle();

      expect(
        find.textContaining('under £6.0m'),
        findsWidgets,
        reason: 'the chip must carry the value now that the options are hidden',
      );
      // ⚠️ The count line proves the filter *ran*; the chip alone would pass on a label that lies.
      expect(all, findsNothing);
      expect(find.textContaining(' of '), findsOneWidget);
    });

    testWidgets('an empty board names the filters that emptied it', (
      tester,
    ) async {
      await openPlayers(tester);
      await tester.enterText(find.byType(TextField), 'zzzznobody');
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining('Price'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Under £5.0m'));
      await tester.pumpAndSettle();

      // ⭐ "Nobody matches that" makes a reader hunt for what "that" was.
      final empty = tester
          .widgetList<Text>(find.textContaining('Nobody matches'))
          .map((t) => t.data!)
          .single;
      expect(empty, contains('zzzznobody'));
      expect(empty, contains('under £5.0m'));
    });

    testWidgets('dismissing the picker leaves the filter alone', (
      tester,
    ) async {
      await openPlayers(tester);
      await tester.tap(find.textContaining('Price'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Under £6.0m'));
      await tester.pumpAndSettle();

      await tester.tap(find.textContaining('Price'));
      await tester.pumpAndSettle();
      // ⚠️⚠️ **`null` is a legitimate answer here** — "any price" and "you tapped outside" pop the same
      // value unless the sheet uses a sentinel. Without one, a dismissal silently clears the filter.
      await tester.tapAt(const Offset(200, 40));
      await tester.pumpAndSettle();

      expect(
        find.textContaining('under £6.0m'),
        findsWidgets,
        reason: 'a dismissal must not be read as "any price"',
      );
    });

    testWidgets('"Any price" clears it', (tester) async {
      await openPlayers(tester);
      await tester.tap(find.textContaining('Price'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Under £6.0m'));
      await tester.pumpAndSettle();

      await tester.tap(find.textContaining('Price'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Any price'));
      await tester.pumpAndSettle();

      expect(find.textContaining('any'), findsOneWidget);
      expect(find.textContaining('players, best first'), findsOneWidget);
    });
  });
}
