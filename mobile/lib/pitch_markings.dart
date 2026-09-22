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

  static final Paint _stripe = Paint()..color = Colors.white.withValues(alpha: 0.035);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // Mown stripes, horizontal so they read as depth rather than as columns fighting the card grid.
    const bands = 8;
    for (var i = 0; i < bands; i += 2) {
      canvas.drawRect(Rect.fromLTWH(0, h / bands * i, w, h / bands), _stripe);
    }

    // The touchline, inset so the pitch has a margin rather than bleeding to the card edge.
    const inset = 6.0;
    final field = Rect.fromLTWH(inset, inset, w - inset * 2, h - inset * 2);
    canvas.drawRect(field, _line);

    // ⭐ The halfway line sits at the **midpoint of the card area**, which is where a viewer expects it —
    // not at the midpoint of the widget, which drifts as rows are added.
    final midY = field.center.dy;
    canvas.drawLine(Offset(field.left, midY), Offset(field.right, midY), _line);
    canvas.drawCircle(Offset(field.center.dx, midY), w * 0.115, _line);
    canvas.drawCircle(Offset(field.center.dx, midY), 1.8, _line..style = PaintingStyle.fill);
    _line.style = PaintingStyle.stroke;

    // The penalty area at the top — the keeper's end, since the XI is drawn keeper-first.
    final boxW = w * 0.46;
    final boxH = h * 0.145;
    final sixW = w * 0.22;
    final sixH = h * 0.062;
    void goalEnd(double top, {required bool flip}) {
      final y = flip ? field.bottom - boxH : field.top;
      canvas.drawRect(Rect.fromLTWH(field.center.dx - boxW / 2, y, boxW, boxH), _line);
      final sy = flip ? field.bottom - sixH : field.top;
      canvas.drawRect(Rect.fromLTWH(field.center.dx - sixW / 2, sy, sixW, sixH), _line);
      // The D — only the arc outside the box, which is what makes it read as a penalty area.
      final spotY = flip ? field.bottom - boxH * 0.72 : field.top + boxH * 0.72;
      canvas.drawArc(
        Rect.fromCircle(center: Offset(field.center.dx, spotY), radius: w * 0.105),
        flip ? -3.6 : 0.46,
        flip ? 2.1 : 2.22,
        false,
        _line,
      );
    }

    goalEnd(field.top, flip: false);
    goalEnd(field.bottom, flip: true);
  }

  @override
  bool shouldRepaint(covariant _Markings oldDelegate) => false;
}
