/// The pitch is drawn to the laws of the game, at any shape (owner feedback).
///
/// ⭐⭐⭐ **Reported from a landscape tablet:** *"the 12 yard semi circles encroach the centre circle."*
/// The penalty arc's radius was derived from the pitch's **width** while the box it belongs to was
/// derived from its **height** — about right on a portrait phone, where width is ~0.6 of height, and
/// enormous on a landscape tablet, where it is nearly twice it.
///
/// ⚠️ *A marking whose size comes from the axis that does not constrain it is right on the shape you drew
/// it against and wrong on every other one.*
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/pitch_markings.dart';

/// Every circle and arc the painter draws, at a given size.
Future<List<({Offset centre, double radius, bool isArc})>> circlesAt(
  WidgetTester tester,
  Size size,
) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: Center(
          child: SizedBox(
            width: size.width,
            height: size.height,
            child: const PitchMarkings(child: SizedBox.expand()),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();

  final found = <({Offset centre, double radius, bool isArc})>[];
  final canvas = _Spy(found);
  final painter = tester
      .widgetList<CustomPaint>(find.byType(CustomPaint))
      .map((w) => w.painter)
      .whereType<CustomPainter>()
      .first;
  painter.paint(canvas, size);
  return found;
}

void main() {
  testWidgets('the D never reaches the centre circle, at any shape', (
    tester,
  ) async {
    // ⚠️ Portrait **and** landscape. The bug shipped because only one shape was ever drawn against.
    for (final size in const [
      Size(390, 760), // phone, portrait
      Size(800, 1000), // tablet, portrait
      Size(1280, 700), // tablet, landscape — the reported case
      Size(760, 390), // phone, landscape — the worst case ADR-293 found
    ]) {
      final shapes = await circlesAt(tester, size);
      final circles = shapes.where((s) => !s.isArc && s.radius > 5).toList();
      final arcs = shapes.where((s) => s.isArc).toList();
      expect(circles, isNotEmpty, reason: 'no centre circle at $size');
      expect(arcs, isNotEmpty, reason: 'no penalty arc at $size');

      final centre = circles.first;
      for (final arc in arcs) {
        // ⭐ The gap between the two, measured: an arc whose own circle overlaps the centre circle's is
        // the defect, whatever the aspect ratio.
        final gap = (arc.centre - centre.centre).distance;
        expect(
          gap,
          greaterThan(arc.radius + centre.radius),
          reason:
              'at $size the D (r=${arc.radius.toStringAsFixed(1)}) overlaps the '
              'centre circle (r=${centre.radius.toStringAsFixed(1)}) — they are '
              '${gap.toStringAsFixed(1)}pt apart',
        );
      }
    }
  });

  testWidgets(
    'the D and the centre circle are the same size — both are 9.15m',
    (tester) async {
      // ⭐⭐ **Not a coincidence and not a shortcut: the laws of the game give both the same radius.** Pinned
      // so nobody re-derives one of them from an axis again — ⚠️ *which is exactly how this broke.*
      for (final size in const [Size(390, 760), Size(1280, 700)]) {
        final shapes = await circlesAt(tester, size);
        final centre = shapes.firstWhere((s) => !s.isArc && s.radius > 5);
        final arc = shapes.firstWhere((s) => s.isArc);
        expect(arc.radius, closeTo(centre.radius, 0.01), reason: 'at $size');
      }
    },
  );
}

/// Records the circles and arcs a painter asks for.
class _Spy implements Canvas {
  _Spy(this._found);

  final List<({Offset centre, double radius, bool isArc})> _found;

  @override
  void drawCircle(Offset c, double radius, Paint paint) {
    _found.add((centre: c, radius: radius, isArc: false));
  }

  @override
  void drawArc(
    Rect rect,
    double startAngle,
    double sweepAngle,
    bool useCenter,
    Paint paint,
  ) {
    _found.add((centre: rect.center, radius: rect.width / 2, isArc: true));
  }

  // ⭐ Everything else is a no-op: this spy exists to record two shapes, not to render a pitch.
  @override
  noSuchMethod(Invocation invocation) => null;
}
