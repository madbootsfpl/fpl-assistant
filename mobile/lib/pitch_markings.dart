/// The pitch the players stand on (ADR-223).
///
/// ⭐ **Painted, not an image.** Markings drawn as vectors scale to any phone without a second asset, cost
/// nothing to download, and — the part that matters — the lines can be positioned *relative to the card
/// rows*, so a five-defender formation and a three-defender one both look like a football pitch rather
/// than like a background someone laid players on top of.
///
/// ⚠️ **Deliberately faint.** The markings are orientation, not content: the eye must land on the xP number
/// first. ADR-135 is this project's record of what happens when a surface is over-densified, and a pitch
/// drawn at full contrast competes with every card on it.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

class PitchMarkings extends StatelessWidget {
  const PitchMarkings({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: const BoxDecoration(
      // ⭐ Banded rather than flat — a mown-stripe gradient reads as grass at a glance, and it is two
      // colours rather than an image.
      gradient: LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0xFF419462), Color(0xFF34754E)],
      ),
    ),
    child: CustomPaint(
      painter: _Markings(),
      // ⚠️ `isComplex` off and no animation: this repaints only when the pitch resizes.
      child: child,
    ),
  );
}

class _Markings extends CustomPainter {
  /// White at 22% — visible as geometry, never as a thing to read.
  static final Paint _line = Paint()
    ..color = Colors.white.withValues(alpha: 0.22)
    ..style = PaintingStyle.stroke
    ..strokeWidth = 1.4;

  static final Paint _spot = Paint()
    ..color = Colors.white.withValues(alpha: 0.22);
  static final Paint _stripe = Paint()
    ..color = Colors.white.withValues(alpha: 0.035);

  /// The penalty arc, **computed rather than guessed**.
  ///
  /// ⚠️⚠️ **This is the bug the owner saw as "distortion".** The first version passed literal start and
  /// sweep angles — `0.46`, `2.22` — chosen because they looked about right on one screen size. They are
  /// not a property of the drawing; they are a property of the *phone it was drawn on*, so on any other
  /// aspect ratio the D swept most of a circle and cut through the cards.
  ///
  /// ⭐ The real rule: an arc of radius [r] about the penalty spot, showing **only the part outside the
  /// penalty area**. Where the arc crosses the box edge is `asin((edge − spot) / r)` — so the angles fall
  /// out of the geometry and are correct at every size.
  static void _penaltyArc(
    Canvas canvas,
    Offset spot,
    double r,
    double edgeY, {
    required bool bulgeDown,
  }) {
    final ratio = (edgeY - spot.dy) / r;
    // |ratio| >= 1 means the box edge lies beyond the arc entirely — nothing to draw, and drawing anyway is
    // how a stray curve appears across the pitch.
    if (ratio.abs() >= 1) return;
    final crossing = math.asin(ratio);
    final rect = Rect.fromCircle(center: spot, radius: r);
    if (bulgeDown) {
      canvas.drawArc(rect, crossing, math.pi - 2 * crossing, false, _line);
    } else {
      canvas.drawArc(
        rect,
        math.pi - crossing,
        math.pi + 2 * crossing,
        false,
        _line,
      );
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // Mown stripes, horizontal so they read as depth rather than as columns fighting the card grid.
    const bands = 8;
    for (var i = 0; i < bands; i += 2) {
      canvas.drawRect(Rect.fromLTWH(0, h / bands * i, w, h / bands), _stripe);
    }

    const inset = 6.0;
    final field = Rect.fromLTWH(inset, inset, w - inset * 2, h - inset * 2);
    canvas.drawRect(field, _line);

    // The halfway line and centre circle.
    //
    // ⭐ The circle's radius is taken from the **pitch's own proportions**, not from its width alone: a real
    // centre circle is 9.15 m on a 68 m pitch, and clamping to a share of the *shorter* axis keeps it a
    // circle that fits rather than one that swallows the midfield on a narrow phone.
    final midY = field.center.dy;
    final radius = math.min(w * 0.125, h * 0.11);
    canvas.drawLine(Offset(field.left, midY), Offset(field.right, midY), _line);
    canvas.drawCircle(Offset(field.center.dx, midY), radius, _line);
    canvas.drawCircle(Offset(field.center.dx, midY), 1.8, _spot);

    // Penalty areas. Proportions are the real ones: the box is 40.3 m of a 68 m width (59%) and 16.5 m of a
    // 105 m length (16%); the six-yard box 18.3 m × 5.5 m; the spot 11 m out.
    final boxW = field.width * 0.56;
    final boxH = field.height * 0.155;
    final sixW = field.width * 0.26;
    final sixH = field.height * 0.058;
    final spotOut = field.height * 0.105;
    // ⚠️⚠️⚠️ **The same radius as the centre circle, and that is the laws of the game, not a trick**
    // (owner: *"in landscape mode, the 12 yard semi circles encroach the centre circle"*). Both are
    // **9.15 m**. This was `field.width * 0.13`, which is about right on a portrait phone — where width
    // is ~0.6 of height — and enormous on a landscape tablet, where it is nearly twice it.
    //
    // ⭐ *The fix is to stop deriving one real distance two different ways.* The centre circle already
    // clamps against both axes for exactly this reason; the D now reads the answer rather than
    // recomputing it from the one axis that does not constrain it.
    final arcR = radius;
    final cx = field.center.dx;

    for (final atTop in [true, false]) {
      final boxTop = atTop ? field.top : field.bottom - boxH;
      canvas.drawRect(Rect.fromLTWH(cx - boxW / 2, boxTop, boxW, boxH), _line);

      final sixTop = atTop ? field.top : field.bottom - sixH;
      canvas.drawRect(Rect.fromLTWH(cx - sixW / 2, sixTop, sixW, sixH), _line);

      final spotY = atTop ? field.top + spotOut : field.bottom - spotOut;
      canvas.drawCircle(Offset(cx, spotY), 1.6, _spot);
      _penaltyArc(
        canvas,
        Offset(cx, spotY),
        arcR,
        atTop ? field.top + boxH : field.bottom - boxH,
        bulgeDown: atTop,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _Markings oldDelegate) => false;
}
