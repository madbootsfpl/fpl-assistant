/// The markings sit on the team, not on the screen (ADR-330).
///
/// 🔴 **Reported from a landscape phone** — *"the pitch is off centre in landscape mode. This is not
/// new."* `PitchLines` used to be wrapped around the whole board, and the board contains the bench, so
/// the halfway line and the centre circle centred on a box the players did not fill.
///
/// ⚠️⚠️ **Measured before it was fixed: 53px out in landscape, and 132px in portrait** — the larger of the
/// two being the one nobody reported, because a pitch running off the bottom of the screen reads as a
/// pitch continuing, while a bench drawn beside it gives the eye a straight edge to measure against.
///
/// ⭐ *A defect visible in one orientation and invisible in the other is still one defect.*
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/pitch.dart';
import 'package:madboots/pitch_3d.dart';
import 'package:madboots/pitch_markings.dart';

typedef Player = ({String pos, int id});

const _xi = <Player>[
  (pos: 'GK', id: 0),
  (pos: 'DEF', id: 1),
  (pos: 'DEF', id: 2),
  (pos: 'DEF', id: 3),
  (pos: 'DEF', id: 4),
  (pos: 'MID', id: 5),
  (pos: 'MID', id: 6),
  (pos: 'MID', id: 7),
  (pos: 'MID', id: 8),
  (pos: 'FWD', id: 9),
  (pos: 'FWD', id: 10),
];
const _bench = <Player>[
  (pos: 'GK', id: 100),
  (pos: 'DEF', id: 101),
  (pos: 'MID', id: 102),
  (pos: 'FWD', id: 103),
];

/// Where the centre circle actually lands, in the coordinates of the whole screen.
Offset centreCircle(WidgetTester tester) {
  final box = tester.getRect(find.byType(PitchLines));
  final paint = tester.widget<CustomPaint>(
    find
        .descendant(
          of: find.byType(PitchLines),
          matching: find.byType(CustomPaint),
        )
        .first,
  );
  final spy = _CircleSpy();
  paint.painter!.paint(spy, box.size);
  // ⭐ The centre circle is the only large circle the painter draws: the three spots are under 2pt.
  final circle = spy.circles.firstWhere((c) => c.radius > 5);
  return box.topLeft + circle.centre;
}

/// The middle of the eleven, **averaged by row and not by player**.
///
/// ⚠️⚠️ *This is the measure, and my first one was wrong.* Averaging all eleven cards weights the answer
/// by how many stand in each row — 1 · 4 · 4 · 2 — which pulls it 17px toward the middle rows and reports
/// a centred pitch as 17px out. ⭐ Every row is `Expanded` and every row is `spaceEvenly`, so the centre
/// of the playing area is the mean of the four **row** centres.
Offset teamCentre(WidgetTester tester) {
  var sum = Offset.zero;
  var rows = 0;
  for (final position in const ['GK', 'DEF', 'MID', 'FWD']) {
    final men = _xi.where((p) => p.pos == position);
    var row = Offset.zero;
    for (final p in men) {
      row += tester.getRect(find.byKey(ValueKey('card${p.id}'))).center;
    }
    sum += row / men.length.toDouble();
    rows++;
  }
  return sum / rows.toDouble();
}

Future<void> pumpBoard(WidgetTester tester, Size size) async {
  // ⚠️⚠️ **The test window is 800x600 by default, and a `SizedBox` wider than it is silently clamped.**
  // The landscape case asked for 802 and was handed 800 — ⭐ *a test that names a shape it was not given
  // is testing the default surface under another name.*
  await tester.binding.setSurfaceSize(size);
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: SizedBox(
          width: size.width,
          height: size.height,
          // ⚠️ Turf on the outside, exactly as `PitchView` has it: the green runs behind the bench
          // (ADR-253) and only the paint is confined to the playing area.
          child: PitchTurf(
            child: PitchBoard<Player>(
              xi: _xi,
              bench: _bench,
              positionOf: (p) => p.pos,
              card: (p, width) => SizedBox(
                key: ValueKey('card${p.id}'),
                width: width,
                height: 56,
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  // 🔴 **These pin the 2D pitch, which is now the revert path** (ADR-331). `Pitch3D.on = false` is the
  // one switch back to what build 33 shipped, and a switch nothing tests is a switch nobody can trust.
  setUp(() => Pitch3D.on = false);
  tearDown(() => Pitch3D.on = true);

  // The reported shape, and the one it hid in.
  for (final shape in const {
    'landscape': Size(802, 527),
    'portrait': Size(390, 760),
  }.entries) {
    testWidgets('the markings are centred on the team in ${shape.key}', (
      tester,
    ) async {
      await pumpBoard(tester, shape.value);

      final circle = centreCircle(tester);
      final team = teamCentre(tester);

      expect(
        (circle.dx - team.dx).abs(),
        lessThan(1.0),
        reason:
            'in ${shape.key} the centre circle is ${(circle.dx - team.dx).toStringAsFixed(1)}px '
            'horizontally away from the middle of the eleven',
      );
      expect(
        (circle.dy - team.dy).abs(),
        lessThan(1.0),
        reason:
            'in ${shape.key} the centre circle is ${(circle.dy - team.dy).toStringAsFixed(1)}px '
            'vertically away from the middle of the eleven',
      );
    });
  }

  testWidgets('the grass still runs behind the bench', (tester) async {
    // ⚠️ The other half of ADR-330, and the reason the fix is not simply "shrink the green".
    // ADR-253 gave the pitch the whole area on purpose — ⭐ *a pitch that stops two thirds of the way
    // down reads as a web page with a picture on it.*
    const size = Size(802, 527);
    await pumpBoard(tester, size);

    expect(tester.getSize(find.byType(PitchTurf)), size);
    expect(
      tester.getRect(find.byType(PitchLines)).width,
      lessThan(size.width),
      reason: 'the paint reaches as wide as the grass, so the bench sits on bare markings',
    );
  });
}

class _CircleSpy implements Canvas {
  final circles = <({Offset centre, double radius})>[];

  @override
  void drawCircle(Offset c, double radius, Paint paint) =>
      circles.add((centre: c, radius: radius));

  @override
  noSuchMethod(Invocation invocation) => null;
}
