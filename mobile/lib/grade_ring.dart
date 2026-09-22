/// The grade as a ring — ⭐ the web's own landing mark, on a phone (ADR-252).
///
/// ⭐⭐ **The arc is the score and the letter is the reading.** A number alone makes a reader work out
/// whether 83 is good; a letter alone throws away the distance between a low A and a high one. Together
/// they answer *how good* and *how close to the next one* in a glance, which is what a landing mark is for.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'brand.dart';

/// How far round the ring a score goes, in radians.
///
/// ⭐⭐ **A function, so a test can assert the number instead of watching for an exception.** A mutation
/// that removed the clamp survived a widget test that only checked nothing threw — ⚠️ *an arc of 500% does
/// not throw, it just draws something untrue.*
double gradeArcSweep(int score) => 2 * math.pi * (score.clamp(0, 100) / 100);

class GradeRing extends StatelessWidget {
  const GradeRing({
    required this.grade,
    required this.score,
    this.size = 62,
    super.key,
  });

  final String grade;
  final int score;
  final double size;

  static Color colourFor(String grade) => switch (grade) {
    'A+' || 'A' => Brand.good,
    'B' => Brand.purpleLight,
    'C' => Brand.warn,
    _ => Brand.bad,
  };

  @override
  Widget build(BuildContext context) => SizedBox(
    width: size,
    height: size,
    child: CustomPaint(
      painter: _RingPainter(score: score, colour: colourFor(grade)),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              grade,
              style: TextStyle(
                color: colourFor(grade),
                fontSize: size * 0.28,
                fontWeight: FontWeight.w800,
                height: 1,
              ),
            ),
            Text(
              '$score/100',
              style: TextStyle(
                color: Colors.white38,
                fontSize: size * 0.13,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

class _RingPainter extends CustomPainter {
  _RingPainter({required this.score, required this.colour});

  final int score;
  final Color colour;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final stroke = size.width * 0.1;
    final inset = rect.deflate(stroke / 2);

    canvas.drawArc(
      inset,
      0,
      2 * math.pi,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = stroke
        ..color = Colors.white10,
    );
    canvas.drawArc(
      inset,
      // ⭐ From twelve o'clock, clockwise — the direction every progress ring a reader has ever seen goes.
      -math.pi / 2,
      gradeArcSweep(score),
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = stroke
        ..strokeCap = StrokeCap.round
        ..color = colour,
    );
  }

  @override
  bool shouldRepaint(_RingPainter old) =>
      old.score != score || old.colour != colour;
}
