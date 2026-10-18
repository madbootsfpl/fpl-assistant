/// The match-event glyphs: a football, a boot, and the disc they sit on (ADR-360).
///
/// ⚠️⚠️ **Drawn, not typed, and that is the whole point.** The first version of these used emoji and
/// Android substituted its own: 🅰 came out as a white A on a **red** box — on a screen whose other
/// feature is red cards — and 🧤 came out as a shield, the glyph already in use for a clean sheet.
/// ⭐ *An emoji is a request, not an instruction*; these are shapes this app draws itself and no font can
/// reinterpret them.
///
/// ⭐⭐ Extracted from `result_pitch.dart` so the Scores card can use the same marks (ADR-360). The pitch
/// drew them and the scores line used `'⚽' * goals` in a **string** — two glyphs for one fact, one of
/// them substitutable. ⚠️ *A second copy of a shape is a second thing to get wrong.*
library;

import 'package:flutter/material.dart';

import 'brand.dart';

class EventDisc extends StatelessWidget {
  const EventDisc({required this.child, super.key});

  static const double size = 13;

  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
    width: size,
    height: size,
    alignment: Alignment.center,
    decoration: const BoxDecoration(
      color: Brand.eventDisc,
      shape: BoxShape.circle,
    ),
    child: child,
  );
}

/// A goal.
class EventBall extends StatelessWidget {
  const EventBall({super.key});

  @override
  Widget build(BuildContext context) => const EventDisc(
    child: SizedBox(
      width: 9,
      height: 9,
      child: CustomPaint(painter: BallPainter()),
    ),
  );
}

/// ⚠️⚠️ **The old goal icon was a plain ring**, and the bonus and saves pips beside it are also circles —
/// so at 13pt *a goal and a bonus point were the same shape.* ⭐ A pattern is the whole difference between
/// a football and a circle, and three marks are the fewest that carry it at this size.
class BallPainter extends CustomPainter {
  const BallPainter();

  /// The glyph is drawn in a 24×24 space and scaled, so the proportions hold at any size.
  static Offset _p(Size s, double x, double y) =>
      Offset(s.width * x / 24, s.height * y / 24);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawCircle(
      Offset(size.width / 2, size.height / 2),
      size.width / 2,
      Paint()..color = Brand.eventGlyph,
    );
    final ink = Paint()..color = Brand.eventMark;

    // The centre panel — a pentagon, which is what makes it a football and not a dot.
    canvas.drawPath(
      Path()
        ..moveTo(_p(size, 12, 6.1).dx, _p(size, 12, 6.1).dy)
        ..lineTo(_p(size, 16.2, 9.2).dx, _p(size, 16.2, 9.2).dy)
        ..lineTo(_p(size, 14.6, 14.2).dx, _p(size, 14.6, 14.2).dy)
        ..lineTo(_p(size, 9.4, 14.2).dx, _p(size, 9.4, 14.2).dy)
        ..lineTo(_p(size, 7.8, 9.2).dx, _p(size, 7.8, 9.2).dy)
        ..close(),
      ink,
    );

    // ⚠️ Three **short** marks at the rim, not spokes to the centre: long ones read as a propeller, which
    // is what the first attempt looked like at this size.
    for (final corners in const [
      [
        [10.4, 1.1],
        [13.6, 1.1],
        [13.1, 4.5],
        [10.9, 4.5],
      ],
      [
        [20.9, 9.4],
        [21.9, 12.5],
        [19.2, 13.9],
        [18.3, 11.8],
      ],
      [
        [3.1, 9.4],
        [2.1, 12.5],
        [4.8, 13.9],
        [5.7, 11.8],
      ],
    ]) {
      final path = Path()
        ..moveTo(
          _p(size, corners[0][0], corners[0][1]).dx,
          _p(size, corners[0][0], corners[0][1]).dy,
        );
      for (final c in corners.skip(1)) {
        path.lineTo(_p(size, c[0], c[1]).dx, _p(size, c[0], c[1]).dy);
      }
      canvas.drawPath(path..close(), ink);
    }
  }

  @override
  bool shouldRepaint(covariant BallPainter oldDelegate) => false;
}

/// An assist — a boot.
///
/// ⚠️⚠️ **Drawn, because Material has no football boot and the nearest icon was a ball outline** — which
/// on a strip whose first icon is a **ball** is the one shape it must not be. ⭐ *An icon that has to be
/// told apart from the icon beside it is doing less work than the word it replaced.*
///
/// ⭐ A silhouette: ankle, instep, sole. At 9pt the sole's overhang is the whole read. ⚠️ It used to be
/// **mint on the pitch's green** — the lowest-contrast pairing on the card — and is white on the disc now.
class EventBoot extends StatelessWidget {
  const EventBoot({super.key});

  @override
  Widget build(BuildContext context) => const EventDisc(
    child: SizedBox(
      width: 9,
      height: 8,
      child: CustomPaint(painter: BootPainter()),
    ),
  );
}

class BootPainter extends CustomPainter {
  const BootPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    final ink = Paint()..color = Brand.eventGlyph;

    // ⭐ **Shaft, instep, toe** — the three parts that make a silhouette a boot rather than an L. The
    // first version drew a thin upright and a bar, and at 11pt it read as a corner.
    final boot = Path()
      // Up the back of the ankle and across its top.
      ..moveTo(w * 0.12, h * 0.70)
      ..lineTo(w * 0.12, h * 0.10)
      ..lineTo(w * 0.46, h * 0.10)
      // Down the front of the shaft, then forward along the instep to the toe.
      ..lineTo(w * 0.46, h * 0.40)
      ..lineTo(w * 0.84, h * 0.55)
      // ⭐ The toe is rounded — a square one reads as a box.
      ..quadraticBezierTo(w * 0.99, h * 0.60, w * 0.97, h * 0.70)
      ..close();
    canvas.drawPath(boot, ink);

    // The sole, proud of the boot on both ends — the part that says "football boot".
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(w * 0.04, h * 0.72, w * 0.94, h * 0.20),
        const Radius.circular(1),
      ),
      ink,
    );
  }

  @override
  bool shouldRepaint(covariant BootPainter oldDelegate) => false;
}

/// A clean sheet.
