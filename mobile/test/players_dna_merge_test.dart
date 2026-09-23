// Player DNA, merged under the stats in Players (ADR-277).
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/more_view.dart';
import 'package:madboots/player_dna_view.dart';

String sample(String name) =>
    File('../spikes/018-flutter-read-slice/api-samples/$name.json')
        .readAsStringSync();

PlayerDna dna() => PlayerDna.fromJson(
  jsonDecode(sample('player-dna')) as Map<String, dynamic>,
);

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(
    backgroundColor: Brand.ink,
    body: SingleChildScrollView(child: child),
  ),
);

/// ⚠️ `MoreView` is **itself a `ListView`**, so the scrolling `wrap` above nests two unbounded
/// scrollables and the framework asserts. ⭐ *A test helper that suits one widget is not a test helper.*
Widget bare(Widget child) => MaterialApp(
  home: Scaffold(backgroundColor: Brand.ink, body: child),
);

void main() {
  group('PlayerFingerprint', () {
    testWidgets('on its own screen it names the player', (tester) async {
      await tester.pumpWidget(wrap(PlayerFingerprint(dna: dna())));
      await tester.pumpAndSettle();
      expect(find.text(dna().player.name), findsOneWidget);
    });

    // ⚠️ Inside the Players card the name is already above it — a screen that names a player twice has
    // two headings and one subject.
    testWidgets('inside a card it does not name him again', (tester) async {
      await tester.pumpWidget(
        wrap(PlayerFingerprint(dna: dna(), showHeader: false)),
      );
      await tester.pumpAndSettle();
      expect(find.text(dna().player.name), findsNothing);
    });

    testWidgets('the axes are drawn either way', (tester) async {
      for (final header in [true, false]) {
        await tester.pumpWidget(
          wrap(PlayerFingerprint(dna: dna(), showHeader: header)),
        );
        await tester.pumpAndSettle();
        // ⭐ The bars carry the axis labels; losing them would leave a radar with no key.
        expect(
          find.text(dna().axes.first.label),
          findsWidgets,
          reason: 'axes missing with showHeader=$header',
        );
      }
    });

    testWidgets(
      'an unranked player says why, rather than showing an empty shape',
      (tester) async {
        final raw = jsonDecode(sample('player-dna')) as Map<String, dynamic>;
        final unranked = PlayerDna.fromJson({
          ...raw,
          'unranked': 'he has not played enough minutes',
        });
        await tester.pumpWidget(wrap(PlayerFingerprint(dna: unranked)));
        await tester.pumpAndSettle();

        // ⚠️ An empty radar reads as "this player is bad at everything", a claim nobody made.
        expect(
          find.textContaining('not played enough minutes'),
          findsOneWidget,
        );
      },
    );
  });

  group('the More directory', () {
    testWidgets('no longer offers Player DNA', (tester) async {
      tester.view.physicalSize = const Size(420, 2400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        bare(
          MoreView(
            managerId: 1,
            freeTransfers: 1,
            onOpenChips: () {},
            onOpenTeamDna: () {},
            onOpenSignals: () {},
            onOpenSettings: () {},
            onOpenLab: () {},
            onOpenLeagues: () {},
            onOpenTicker: () {},
            onOpenFeedback: () {},
            onOpenHelp: () {},
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Player DNA'), findsNothing);
      // ⭐ And the club-level one stays: they are different questions about different subjects.
      expect(find.text('Team DNA'), findsOneWidget);
    });
  });
}
