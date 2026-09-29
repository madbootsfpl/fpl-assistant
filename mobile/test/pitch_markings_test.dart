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

import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
            child: const PitchLines(child: SizedBox.expand()),
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

CustomPainter painterIn(WidgetTester tester) => tester
    .widgetList<CustomPaint>(find.byType(CustomPaint))
    .map((w) => w.painter)
    .whereType<CustomPainter>()
    .first;

Future<void> pumpPitch(WidgetTester tester) => tester.pumpWidget(
  const MaterialApp(
    home: Scaffold(
      body: SizedBox(
        width: 390,
        height: 760,
        child: PitchTurf(child: SizedBox.expand()),
      ),
    ),
  ),
);

/// The colour the painter actually puts on the middle of the pitch.
Future<({int r, int g, int b, int a})> centrePixel(
  WidgetTester tester,
  CustomPainter painter,
) async {
  const size = Size(390, 760);
  final recorder = ui.PictureRecorder();
  painter.paint(Canvas(recorder), size);
  // ⚠️ `runAsync`: rasterising is real work and the test binding's fake clock will not do it.
  final bytes = await tester.runAsync(() async {
    final image = await recorder.endRecording().toImage(390, 760);
    return image.toByteData(format: ui.ImageByteFormat.rawRgba);
  });
  // A point off the halfway line and outside the centre circle, so no marking is sampled.
  const x = 80, y = 250;
  final o = (y * 390 + x) * 4;
  return (
    r: bytes!.getUint8(o),
    g: bytes.getUint8(o + 1),
    b: bytes.getUint8(o + 2),
    a: bytes.getUint8(o + 3),
  );
}

void main() {
  // ⚠️ The decoded turf is cached for the life of the process, so one test resolving it would otherwise
  // decide what the next one sees.
  setUp(resetTurfForTest);

  group('the turf (ADR-329)', () {
    testWidgets('the pitch is green before the turf arrives', (tester) async {
      // ⭐⭐ **The asset is late by definition** — it is decoded off a future, and the first frame is drawn
      // before it lands. ⚠️ *A pitch that waits for its image is a pitch that flashes empty*, and on a
      // cold start that blank is the first thing anyone sees.
      //
      // ⚠️⚠️ **This asserted that *something* filled the pitch, and passed with the background deleted.**
      // The top light is itself a full-size rect, so a spy counting rectangles saw it and was satisfied.
      // ⭐ *A test that watches the calls cannot tell a background from a film laid over one* — so this
      // one reads the pixel.
      await pumpPitch(tester);

      final pixel = await centrePixel(tester, painterIn(tester));

      expect(pixel.a, 255, reason: 'the cold pitch is see-through');
      expect(
        pixel.g,
        greaterThan(math.max(pixel.r, pixel.b)),
        reason: 'the cold pitch is not green: $pixel',
      );
    });

    testWidgets('the painter repaints once the turf lands', (tester) async {
      // 🔴 **`shouldRepaint` returned a flat `false` for the whole of this widget's life**, which was right
      // while it drew nothing but geometry. ⭐ *A painter that never repaints cannot show an image it did
      // not have when it was built* — so the grass would decode, be handed over, and never appear.
      await pumpPitch(tester);
      final cold = painterIn(tester);

      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 500)),
      );
      await tester.pump();
      final warm = painterIn(tester);

      expect(
        warm.shouldRepaint(cold),
        isTrue,
        reason: 'the turf arrived and the pitch did not redraw',
      );
    });

    test('the turf is declared, and is the size the tiling assumes', () async {
      TestWidgetsFlutterBinding.ensureInitialized();
      // ⚠️ Declared in `pubspec.yaml`, not merely present on disk: an undeclared asset is missing at
      // runtime and the failure is a silent fallback to the gradient.
      final data = await rootBundle.load('assets/pitch-grass.webp');
      final codec = await ui.instantiateImageCodec(data.buffer.asUint8List());
      final image = (await codec.getNextFrame()).image;

      expect(image.width, image.height, reason: 'the tile must be square to repeat');
      expect(image.width, 512);
    });
  });

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
