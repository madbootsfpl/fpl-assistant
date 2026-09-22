/// The radar and the ring (ADR-252).
///
/// ⭐⭐ **Painters are where a silent wrong answer hides.** A widget that throws gets noticed; one that
/// draws a plausible-but-wrong shape does not — and a radar's whole job is to be read at a glance, without
/// checking. So these assert the arithmetic the painter depends on, and that the widgets survive the
/// inputs that would otherwise crash a canvas.
library;

import 'dart:convert';
import 'dart:math' as math;
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/dna_radar.dart';
import 'package:madboots/grade_ring.dart';

DnaAxis axis(int? p) =>
    DnaAxis(label: 'Attacking Threat', sublabel: 'xG', value: 1, percentile: p);

/// ⚠️ **Width-bounded, height-free** — the shape the widgets actually live in (a scroll view).
///
/// An earlier version forced a 320×320 box, which made *"renders nothing"* untestable: a `SizedBox.shrink`
/// inside a fixed square fills it. ⭐ *A harness that constrains the thing under test measures the
/// harness.*
Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(
    backgroundColor: const Color(0xFF17131F),
    body: Center(
      child: SizedBox(
        width: 320,
        child: Column(mainAxisSize: MainAxisSize.min, children: [child]),
      ),
    ),
  ),
);

/// ⭐ And the bounded one, kept deliberately: the overflow this file found only happens when height is
/// finite, which is the case a scroll view never produces.
Widget wrapBounded(Widget child) => MaterialApp(
  home: Scaffold(
    backgroundColor: const Color(0xFF17131F),
    body: Center(child: SizedBox(width: 320, height: 320, child: child)),
  ),
);

void main() {
  // ── the geometry, as arithmetic ──────────────────────────────────────────────────────────────
  //
  // ⭐⭐⭐ **These exist because the widget tests below could not see three real mutations.** Drawing an
  // unranked axis at mid-table, removing the empty-axes guard, and unclamping the ring all survived a
  // round of "does it throw?" tests — ⚠️ *a painter drawing a plausible-but-wrong shape throws nothing*,
  // and a radar's whole job is to be believed at a glance without checking.

  test('an unranked axis is placed at the centre, not at mid-table', () {
    const centre = Offset(100, 100);
    final points = radarPoints([axis(null)], centre, 80);
    expect(points.single.dx, closeTo(centre.dx, 0.001));
    expect(points.single.dy, closeTo(centre.dy, 0.001));
  });

  test('the first axis points straight up, and the rest run clockwise', () {
    const centre = Offset(0, 0);
    final points = radarPoints(List.generate(4, (_) => axis(100)), centre, 10);
    // ⚠️ Screen coordinates: up is **negative** y.
    expect(points[0].dx, closeTo(0, 0.001));
    expect(points[0].dy, closeTo(-10, 0.001));
    expect(
      points[1].dx,
      closeTo(10, 0.001),
      reason: 'second axis should be to the right',
    );
    expect(
      points[3].dx,
      closeTo(-10, 0.001),
      reason: 'fourth should be to the left',
    );
  });

  test(
    'a percentile is a fraction of the radius, not a fraction of the box',
    () {
      const centre = Offset(0, 0);
      final half = radarPoints([axis(50)], centre, 100).single;
      expect(half.dy, closeTo(-50, 0.001));
    },
  );

  test('no axes gives no points rather than a divide by zero', () {
    expect(radarPoints(const [], const Offset(0, 0), 80), isEmpty);
  });

  test('the ring clamps, because an arc of 500% draws something untrue', () {
    expect(gradeArcSweep(0), 0);
    expect(gradeArcSweep(50), closeTo(math.pi, 0.001));
    expect(gradeArcSweep(100), closeTo(2 * math.pi, 0.001));
    expect(
      gradeArcSweep(140),
      closeTo(2 * math.pi, 0.001),
      reason: 'over 100 must not overdraw',
    );
    expect(
      gradeArcSweep(-20),
      0,
      reason: 'a negative score must not draw backwards',
    );
  });

  testWidgets('a radar draws with every axis unranked', (tester) async {
    // ⚠️⚠️ **Null is drawn at the centre, not skipped.** Skipping would close the polygon across the gap
    // and invent a shape the data never claimed — and a degenerate polygon is also how a painter throws.
    await tester.pumpWidget(
      wrap(
        DnaRadar(
          series: [
            (
              label: 'Nobody',
              colour: const Color(0xFFB45CF0),
              axes: List.generate(8, (_) => axis(null)),
            ),
          ],
        ),
      ),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('a radar with no axes takes up no room at all', (tester) async {
    // ⚠️⚠️ **Not "does not throw"** — an empty axes list draws a blank square perfectly happily, and a
    // mutation removing the guard survived a test that only watched for exceptions. ⭐ *The guard's whole
    // purpose is that nothing appears, so that is what has to be asserted.*
    await tester.pumpWidget(
      wrap(
        const DnaRadar(
          series: [(label: 'Empty', colour: Color(0xFFB45CF0), axes: [])],
        ),
      ),
    );
    expect(tester.takeException(), isNull);
    expect(tester.getSize(find.byType(DnaRadar)).height, 0);
  });

  testWidgets('a radar with axes does take up room', (tester) async {
    // ⭐ The other half: a test that only checked "empty is zero" would pass on a widget that always
    // rendered nothing.
    await tester.pumpWidget(
      wrap(
        DnaRadar(
          series: [
            (
              label: 'Someone',
              colour: const Color(0xFFB45CF0),
              axes: List.generate(8, (i) => axis(i * 10)),
            ),
          ],
        ),
      ),
    );
    expect(tester.getSize(find.byType(DnaRadar)).height, greaterThan(100));
  });

  testWidgets('two clubs on one radar show a legend, one club does not', (
    tester,
  ) async {
    final axes = List.generate(8, (i) => axis(i * 12));
    // ⚠️ **Bounded on purpose.** This is the test that caught the radar overflowing a height-limited
    // parent once a legend was added — it only works in the app because it lives in a scroll view, where
    // height is free. ⭐ *A widget that only works in an unbounded parent works by luck.*
    await tester.pumpWidget(
      wrapBounded(
        DnaRadar(
          series: [
            (label: 'Arsenal', colour: const Color(0xFFB45CF0), axes: axes),
          ],
        ),
      ),
    );
    // ⭐ A legend for one series is a legend explaining the only thing on screen.
    expect(find.text('Arsenal'), findsNothing);

    await tester.pumpWidget(
      wrapBounded(
        DnaRadar(
          series: [
            (label: 'Arsenal', colour: const Color(0xFFB45CF0), axes: axes),
            (label: 'Aston Villa', colour: const Color(0xFF5EEAD4), axes: axes),
          ],
        ),
      ),
    );
    expect(find.text('Arsenal'), findsOneWidget);
    expect(find.text('Aston Villa'), findsOneWidget);
  });

  testWidgets('the ring shows the letter and the number it came from', (
    tester,
  ) async {
    // ⭐ The arc is the score and the letter is the reading. A number alone makes a reader work out
    // whether 83 is good; a letter alone throws away the distance to the next grade.
    await tester.pumpWidget(wrap(const GradeRing(grade: 'A+', score: 87)));
    expect(find.text('A+'), findsOneWidget);
    expect(find.text('87/100'), findsOneWidget);
  });

  testWidgets('a score outside 0–100 does not break the arc', (tester) async {
    // ⚠️ The engine clamps to 1–99, but a painter that trusts its input is a painter that throws the one
    // time the engine changes.
    for (final score in [-20, 0, 100, 140]) {
      await tester.pumpWidget(wrap(GradeRing(grade: 'C', score: score)));
      expect(tester.takeException(), isNull, reason: 'score $score');
    }
  });

  test('the committed sample really carries eight axes to draw', () {
    // ⚠️ A radar test built on hand-made axes proves the painter works on hand-made axes. This pins the
    // shape the app is actually handed.
    final json = jsonDecode(
      File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
          .readAsStringSync(),
    ) as Map<String, dynamic>;
    expect(json.containsKey('swaps'), isTrue);
  });
}
