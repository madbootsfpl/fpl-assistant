/// The perspective pitch keeps its promises at every shape (ADR-331).
///
/// ⭐⭐⭐ **These are the owner's own constraints, written down as tests**, and they are here rather than
/// in a preview because a preview shows one formation on one screen. *Five defenders must fit · five
/// midfielders must fit · every card's text stays readable · the keeper is never cut off · no card
/// overlaps another.*
///
/// ⚠️⚠️ Each one caught something while it was being written: 97pt cards overlapped by 6px in a
/// four-row and 103px in a five-row, and the forwards' price line was cut by the bench in one
/// formation and clear in another. ⭐ *A layout that is right for one card size is not a layout; it is
/// a coincidence.*
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/pitch.dart';
import 'package:madboots/pitch_3d.dart';

/// The sample squad, re-shaped. ⭐ Edits the JSON so the fifteen, the prices and the fixtures stay
/// real and only the shape under test changes.
MyTeam teamShaped(String formation) {
  final json = jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>;
  final counts = formation.split('-').map(int.parse).toList();
  final want = <String>[
    'GK',
    ...List.filled(counts[0], 'DEF'),
    ...List.filled(counts[1], 'MID'),
    ...List.filled(counts[2], 'FWD'),
  ];
  final xi = (json['analysis'] as Map<String, dynamic>)['xi'] as List;
  for (var i = 0; i < xi.length && i < want.length; i++) {
    (xi[i] as Map<String, dynamic>)['position'] = want[i];
  }
  return MyTeam.fromJson(json);
}

Future<List<Rect>> cardsFor(
  WidgetTester tester,
  String formation,
  Size size,
) async {
  await tester.binding.setSurfaceSize(size);
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: SizedBox(
          width: size.width,
          height: size.height,
          child: PitchView(
            team: teamShaped(formation),
            mode: PitchMode.nextGw,
            onMode: (_) {},
            onTapPlayer: (_) {},
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  // Every price line on the pitch — the last thing drawn on a card, so it is the one that gets
  // clipped first if anything is going to be.
  return tester
      .widgetList<Text>(find.byType(Text))
      .where((t) => (t.data ?? '').startsWith('£'))
      .map((t) => tester.getRect(find.byWidget(t)))
      .toList();
}

const formations = ['4-4-2', '5-4-1', '3-5-2', '3-4-3', '5-3-2'];

/// ⚠️ A big phone and a **small** one. The bench and the header cost the same on both, so a short
/// screen leaves the pitch far less room — ⭐ *a layout only tested on the roomiest phone is a layout
/// tested where it cannot fail.*
const screens = {'390x760': Size(390, 760), '360x640': Size(360, 640)};

void main() {
  for (final shape in formations) {
    testWidgets('$shape: no card overlaps another', (tester) async {
      final cards = await cardsFor(tester, shape, const Size(390, 760));
      expect(cards.length, greaterThan(10));
      for (var i = 0; i < cards.length; i++) {
        for (var j = i + 1; j < cards.length; j++) {
          expect(
            cards[i].overlaps(cards[j]),
            isFalse,
            reason: '$shape: ${cards[i]} overlaps ${cards[j]}',
          );
        }
      }
    });

    testWidgets('$shape: every card is drawn inside the screen', (
      tester,
    ) async {
      // ⚠️ Covers the keeper, who is placed in the goal mouth rather than on the pitch, and the
      // forwards, whose price line was cut by the bench before the rows were clamped.
      final cards = await cardsFor(tester, shape, const Size(390, 760));
      for (final r in cards) {
        expect(
          r.top,
          greaterThanOrEqualTo(0),
          reason: '$shape: $r off the top',
        );
        expect(
          r.bottom,
          lessThanOrEqualTo(760),
          reason: '$shape: $r off the bottom',
        );
        expect(
          r.left,
          greaterThanOrEqualTo(0),
          reason: '$shape: $r off the left',
        );
        expect(
          r.right,
          lessThanOrEqualTo(390),
          reason: '$shape: $r off the right',
        );
      }
    });
  }

  for (final shape in formations) {
    testWidgets('$shape: no card runs into the bench', (tester) async {
      // ⚠️⚠️ **The screen-bounds test above passed with the clamp deleted**, because the bench is
      // inside the screen — a forward's price line can be swallowed by the panel and still be "on
      // screen". ⭐ *A bound that is not the thing you care about is a bound that agrees with the bug.*
      for (final screen in screens.entries) {
        final cards = await cardsFor(tester, shape, screen.value);
        final bench = tester.getRect(find.text('BENCH')).top;
        for (final r in cards.where((r) => r.top < bench)) {
          expect(
            r.bottom,
            lessThanOrEqualTo(bench),
            reason:
                '$shape on ${screen.key}: a card at $r crosses into the bench at $bench',
          );
        }
      }
    });
  }

  test('a card never draws smaller than the size that ships flat', () {
    // ⭐⭐ **70pt is not a preference; it is the smallest text known to be readable here**, because it
    // is what the flat pitch has always drawn. ⚠️ An earlier rule shrank to 66pt — smaller than
    // anything ever shipped — by applying the tablet *up*-scaling factor as a shrink.
    for (final widest in [3, 4, 5, 6]) {
      expect(
        Pitch3D.cardWidthFor(382, widest),
        greaterThanOrEqualTo(Pitch3D.minCardW),
        reason: 'a row of $widest drew below the design card',
      );
    }
  });

  test('five in a row fit a phone, with a gap', () {
    final w = Pitch3D.cardWidthFor(382, 5);
    expect(w * 5, lessThan(382), reason: 'five cards do not fit');
    expect((382 - w * 5) / 6, greaterThan(1), reason: 'five cards touch');
  });

  test('the revert switch is real', () {
    // 🔴 The one lever back to build 33's flat pitch. ⚠️ *A switch nothing asserts is a switch nobody
    // can trust when they need it.*
    expect(
      Pitch3D.on,
      isTrue,
      reason: 'the 3D pitch should be the default now',
    );
    Pitch3D.on = false;
    expect(Pitch3D.on, isFalse);
    Pitch3D.on = true;
  });
}
