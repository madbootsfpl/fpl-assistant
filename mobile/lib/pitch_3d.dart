/// SPIKE — the pitch in perspective, to your numbers. Not wired into the app by default.
///
/// ⭐⭐⭐ **The pitch is painted flat and then tilted.** Perspective-correct grass, foreshortened
/// markings and a receding horizon all come out of one `Matrix4` — nothing here computes a trapezoid.
/// ⚠️ *I told the owner a tiled turf could not recede with the lines. It can; I was trying to draw a
/// perspective pitch instead of tilting a flat one.*
library;

import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Spike-grade knobs: mutable statics, so a render can sweep them. Real code would not do this.
class Pitch3D {
  /// 🔴🔴 **THE REVERT SWITCH.** Set this to `false` and the app draws the flat 2D grass pitch that
  /// shipped in build 33 — `PitchTurf` and `PitchLines` are still there, still tested, and still
  /// correct. Nothing else has to change and no history has to be rewritten.
  ///
  /// ⭐ *A new look that cannot be turned off is a new look you have to be sure about.* This one can,
  /// which is why it could ship at all. The 2D path is kept alive by its own tests
  /// (`pitch_markings_test.dart`, `the_pitch_is_centred_on_the_team_test.dart`), so it cannot rot
  /// quietly while it waits.
  ///
  /// ⚠️ It is also `const`-free on purpose: a test can flip it, which is how both paths stay covered.
  ///
  /// The build that last shipped without any of this is tagged **`pitch-2d`**.
  static bool on = true;

  // The owner's own numbers, tuned in the preview.
  static const double tilt = 39; // degrees
  static const double dist = 850; // camera distance, px
  static const double shown = 0.83; // of the 105m length
  static const double zoom = 1.41;

  /// ⚠️⚠️ **0 here, where the preview wanted 152.** In the preview the bench floated over the pitch
  /// and `lift` was the room made for it. In the app the board is already `Expanded` **above** the
  /// bench, so the same number is counted twice and leaves a 150px dead band.
  /// ⭐ *A value tuned against one layout is not a value; it is a measurement of that layout.*
  static const double lift = 0;

  /// How much stretched foreground to cut off the bottom of the pitch.
  static const double crop = 110;
  static const double lineA = 0.83;
  static const double tile = 215; // grass tile, px on the flat plane
  static const double shrink = 0.10; // how much a card shrinks with depth
  /// The card width you would like, if the formation allows it.
  static const double wantCardW = 97;

  /// ⚠️⚠️ **The width is not a free choice; the widest row sets it.** Five cards at 97pt need 485px
  /// and a phone row has 382 — they overlap by 103. ⭐ *A five-defender row and a one-forward row must
  /// draw the same card, or the eye reads the wider one as more important* — that is the flat pitch's
  /// own rule (ADR-253's `cardWidthFor`), and it applies here for the same reason.
  /// ⚠️⚠️ **Never below 70pt**, which is the size the flat pitch ships at and therefore the smallest
  /// text known to be readable on a phone. Five of them need 350px of a 382px row, so five defenders
  /// fit with a 5px gap — ⭐ *the constraint was already satisfied by the design card; my first rule
  /// shrank past it by applying the tablet up-scaling factor as a shrink.*
  static const double minCardW = 70;

  /// One width for the whole pitch, set by the most crowded row, with a gap that keeps cards apart.
  static double cardWidthFor(double available, int widestRow) {
    if (widestRow <= 0) return wantCardW;
    final slot = (available - 6 * (widestRow + 1)) / widestRow;
    final want = slot < wantCardW ? slot : wantCardW;
    return want < minCardW ? minCardW : want;
  }

  /// What the last layout settled on — the goal and the keeper read it.
  static double cardW = 82;

  /// Metres from the far goal line.
  ///
  /// ⚠️⚠️ **The keeper was at 4m and half his card sat off the pitch.** Four metres is eleven pixels at
  /// that depth — ⭐ *the far end of a perspective pitch has almost no room in it, and a distance that
  /// reads as generous on a flat pitch is nothing once it recedes.* Computed rather than nudged: a card
  /// clears the goal line from 14m, so the keeper stands at 15 and the rest move down with him.
  static const Map<String, double> rows = {'DEF': 44, 'MID': 68, 'FWD': 86};

  /// ⭐⭐ **Fill the board, or keep the touchlines — you cannot have both** at this tilt. The portion
  /// of pitch on show is 68m x 87m (aspect 0.78) and a portrait board is almost exactly that shape,
  /// so it fits flat and cannot fit tilted: ⚠️ *tilting shortens the length and never the width.*
  /// `true` zooms until the pitch fills the height and the touchlines leave the frame entirely.
  static const bool fillBoard = true;

  /// ⭐⭐ **Room above the goal line, and it is not decoration.** With the far edge hard against the
  /// top of the board the keeper's card is cut in half — he stands 4m out, which is a few pixels at
  /// that depth. Pushing the goal line down carries **the markings and the far players with it**,
  /// because every row is measured in metres from that line, while the forwards at the near edge
  /// stay where they are. ⚠️ *One number, because they have to move together or the team stops
  /// standing on the pitch.*
  static const double topGap = 44;

  /// The goal, as a share of the pitch's **projected** width at the goal line.
  ///
  /// ⚠️⚠️ **Deliberately not the laws of the game.** A real goal is 7.32m of a 68m pitch — 11% — which
  /// at this depth draws 46px wide and 15px tall, a smudge. Your reference draws it at 23% and
  /// proportionally taller, and it is right to: ⭐ *at the far end of a perspective pitch, real
  /// proportions and legible ones are different things, and the markings are the half that has to
  /// stay real.*
  /// Metres of grass **behind** the goal line, before the hoardings.
  static const double runOff = 14;

  /// The keeper's card, as a share of the goal's height. ⭐⭐ **He stands in the goal, not on the
  /// pitch** — which hands the other three rows the whole playing area back.
  static const double keeperFill = 0.85;

  /// The hoardings, as a share of the goal's height.
  /// ⭐ A share of the **pitch's** width, not the goal's. They were tied, so shrinking the goal
  /// shrank the advertising with it and left a dead band above.
  static const double hoardHeight = 0.055;

  static const double goalWidth = 0.184;

  /// ⚠️ A share of its **own width**, which just fell 20% — so a 40% cut to this ratio would take
  /// 52% off the height. Divided by the width cut to land on the 40% that was asked for.
  static const double goalHeight = 0.41;
  static const bool goal = true;

  static const Color surround = Color(0xFF120E1A);

  static const double length = 105, width = 68;
}

/// Where a point on the plane lands on screen, relative to the plane's bottom-centre.
///
/// ⭐ The same arithmetic the `Matrix4` performs, in closed form — which is what lets the cards be
/// laid out by Flutter while the pitch under them is drawn by the canvas.
({double x, double y, double k}) project(double lx, double ly) {
  final t = Pitch3D.tilt * math.pi / 180;
  final z = ly * math.sin(t);
  final k = Pitch3D.dist / (Pitch3D.dist - z);
  return (x: lx * k, y: ly * math.cos(t) * k, k: k);
}

/// The size of the plane for a given box, and where its bottom-centre sits in it.
({double pw, double ph, double ox, double oy, double m}) planeFor(Size box) {
  double pw, ph;
  if (Pitch3D.fillBoard) {
    // Solve the projection for the plane whose far edge lands on the top of the board.
    final t = Pitch3D.tilt * math.pi / 180;
    // ⭐⭐ `crop` lengthens the plane **downwards, past the bottom of the screen**, so the stretched
    // foreground is cut off — and because the projected height grows by exactly the same amount the
    // origin moves down, ⚠️ *the goal line does not shift at all.*
    final h = math.max(80.0, box.height - Pitch3D.topGap + Pitch3D.crop);
    final den = math.cos(t) * Pitch3D.dist - h * math.sin(t);
    ph = den > 1 ? h * Pitch3D.dist / den : h;
    pw = ph * Pitch3D.width / (Pitch3D.shown * Pitch3D.length + Pitch3D.runOff);
  } else {
    pw = box.width * Pitch3D.zoom;
    ph = pw * (Pitch3D.shown * Pitch3D.length + Pitch3D.runOff) / Pitch3D.width;
  }
  return (
    pw: pw,
    ph: ph,
    ox: box.width / 2,
    oy: box.height - Pitch3D.lift + Pitch3D.crop,
    m: pw / Pitch3D.width,
  );
}

class TiltedPitch extends StatefulWidget {
  const TiltedPitch({super.key});

  @override
  State<TiltedPitch> createState() => _TiltedPitchState();
}

class _TiltedPitchState extends State<TiltedPitch> {
  ui.Image? _grass;

  @override
  void initState() {
    super.initState();
    turf()
        .then((i) {
          if (mounted) setState(() => _grass = i);
        })
        .catchError((Object _) {});
  }

  @override
  Widget build(BuildContext context) =>
      CustomPaint(painter: _Plane(_grass), size: Size.infinite);
}

Future<ui.Image>? _req;
Future<ui.Image> turf() => _req ??= () async {
  final d = await rootBundle.load('assets/pitch-grass.webp');
  return (await (await ui.instantiateImageCodec(
    d.buffer.asUint8List(),
  )).getNextFrame()).image;
}();

/// The height the goal is drawn at, as a share of its own width.
///
/// ⚠️⚠️ **No longer derived from the keeper's card.** It was, and that made the goal enormous: the card
/// had to fit *inside* it, so a bigger card meant a bigger goal. ⭐ *The goal is a thing on the pitch
/// with its own size; the keeper stands in front of it, as a player does.*
double goalHeightFor(double goalW) => goalW * Pitch3D.goalHeight;

/// The middle of the goal mouth: where the keeper's card is centred.
///
/// ⭐⭐ **The keeper does not stand on the pitch.** He stands in the goal, which is the one place on
/// this view with room to spare — and it hands a whole row back to the outfield.
double goalWidthFor(
  ({double pw, double ph, double ox, double oy, double m}) p,
) => p.pw * project(0, -p.ph + Pitch3D.runOff * p.m).k * Pitch3D.goalWidth;

/// Where the keeper's card is centred.
///
/// ⭐ Level with the middle of the goal mouth. ⚠️ He is no longer scaled to fit inside it — the goal
/// is its own size now, and a keeper standing in front of a goal is taller than the crossbar is a
/// perfectly ordinary thing to see.
double keeperCentre(
  ({double pw, double ph, double ox, double oy, double m}) p,
  double cardW,
) {
  final line = project(0, -p.ph + Pitch3D.runOff * p.m);
  return p.oy + line.y - goalHeightFor(goalWidthFor(p)) / 2;
}

class _Plane extends CustomPainter {
  _Plane(this.grass);
  final ui.Image? grass;

  @override
  void paint(Canvas canvas, Size size) {
    // ⭐ The surround: everything outside the touchlines. The grass no longer fills the screen, so
    // something has to, and it is the app's own ground rather than more green.
    canvas.drawRect(Offset.zero & size, Paint()..color = Pitch3D.surround);

    final p = planeFor(size);
    canvas.save();
    canvas.translate(p.ox, p.oy);
    canvas.transform(
      (Matrix4.identity()
            ..setEntry(3, 2, -1 / Pitch3D.dist)
            ..rotateX(Pitch3D.tilt * math.pi / 180))
          .storage,
    );
    _flat(canvas, p.pw, p.ph, p.m);
    canvas.restore();

    // ⭐ The goal stands **up** out of the plane, so it is drawn after the tilt is undone: its posts
    // are vertical on screen, not vertical on the pitch.
    if (Pitch3D.goal) _goal(canvas, p);
  }

  /// The pitch, drawn top-down with its **near edge at the origin**. The plane starts `runOff`
  /// metres behind the goal line, so there is grass beyond it before the hoardings.
  void _flat(Canvas canvas, double pw, double ph, double m) {
    final field = Rect.fromLTWH(-pw / 2, -ph, pw, ph);
    canvas.save();
    canvas.clipRect(field);

    if (grass != null) {
      canvas.drawRect(field, Paint()..color = const Color(0xFF146B30));
      final k = Pitch3D.tile / grass!.width;
      canvas.drawRect(
        field,
        Paint()
          ..shader = ImageShader(
            grass!,
            TileMode.repeated,
            TileMode.repeated,
            Matrix4.diagonal3Values(k, k, 1).storage,
            filterQuality: FilterQuality.low,
          ),
      );
    } else {
      canvas.drawRect(
        field,
        Paint()
          ..shader = const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF419462), Color(0xFF34754E)],
          ).createShader(field),
      );
    }

    final line = Paint()
      ..color = Colors.white.withValues(alpha: Pitch3D.lineA)
      ..style = PaintingStyle.stroke
      ..strokeWidth = math.max(1.6, 0.12 * m);
    final solid = Paint()
      ..color = Colors.white.withValues(alpha: Pitch3D.lineA);

    // ⭐ Zero is the goal line, and the plane now starts `runOff` metres behind it.
    double y(double metres) => -ph + (Pitch3D.runOff + metres) * m;

    canvas.drawLine(Offset(field.left, y(0)), Offset(field.right, y(0)), line);
    canvas.drawLine(
      Offset(field.left, y(0)),
      Offset(field.left, field.bottom),
      line,
    );
    canvas.drawLine(
      Offset(field.right, y(0)),
      Offset(field.right, field.bottom),
      line,
    );
    canvas.drawRect(
      Rect.fromLTWH(-40.32 / 2 * m, y(0), 40.32 * m, 16.5 * m),
      line,
    );
    canvas.drawRect(
      Rect.fromLTWH(-18.32 / 2 * m, y(0), 18.32 * m, 5.5 * m),
      line,
    );
    canvas.drawCircle(Offset(0, y(11)), math.max(1.8, 0.16 * m), solid);

    final a = math.asin((16.5 - 11) / 9.15);
    canvas.drawArc(
      Rect.fromCircle(center: Offset(0, y(11)), radius: 9.15 * m),
      a,
      math.pi - 2 * a,
      false,
      line,
    );

    if (Pitch3D.shown * Pitch3D.length > Pitch3D.length / 2) {
      canvas.drawLine(
        Offset(field.left, y(52.5)),
        Offset(field.right, y(52.5)),
        line,
      );
      canvas.drawCircle(Offset(0, y(52.5)), 9.15 * m, line);
      canvas.drawCircle(Offset(0, y(52.5)), math.max(1.8, 0.16 * m), solid);
    }
    canvas.restore();
  }

  void _goal(
    Canvas canvas,
    ({double pw, double ph, double ox, double oy, double m}) p,
  ) {
    final w = goalWidthFor(p);
    final h = goalHeightFor(w);

    // The hoardings stand on the back edge of the run-off, facing the camera.
    final back = project(0, -p.ph);
    final backY = p.oy + back.y;
    final backHalf = p.pw * back.k / 2;
    final hoard = backHalf * 2 * Pitch3D.hoardHeight;
    final band = Rect.fromLTRB(
      p.ox - backHalf,
      backY - hoard,
      p.ox + backHalf,
      backY,
    );
    canvas.drawRect(band, Paint()..color = const Color(0xFF1D1730));
    canvas.drawRect(
      band,
      Paint()
        ..color = Colors.white.withValues(alpha: 0.10)
        ..style = PaintingStyle.stroke,
    );

    // ⭐ The brand goes on the hoardings, which is where a ground puts it.
    final label = TextPainter(
      text: TextSpan(
        text: 'MADBOOTS',
        style: TextStyle(
          color: const Color(0xFFB45CF0),
          fontFamily: 'Roboto',
          fontSize: hoard * 0.44,
          fontWeight: FontWeight.w700,
          letterSpacing: hoard * 0.10,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    canvas.save();
    canvas.clipRect(band);
    for (
      var x = band.left + 10;
      x < band.right;
      x += label.width + hoard * 1.2
    ) {
      label.paint(canvas, Offset(x, band.center.dy - label.height / 2));
    }
    canvas.restore();

    // The goal, standing on the goal line.
    final line = project(0, -p.ph + Pitch3D.runOff * p.m);
    final cy = p.oy + line.y;
    final l = p.ox - w / 2, r = p.ox + w / 2, top = cy - h;

    final net = Paint()
      ..color = Colors.white.withValues(alpha: 0.18)
      ..strokeWidth = 1;
    for (var i = 1; i < 8; i++) {
      final x = l + w * i / 8;
      canvas.drawLine(Offset(x, top), Offset(x, cy), net);
    }
    for (var i = 1; i < 5; i++) {
      final yy = top + h * i / 5;
      canvas.drawLine(Offset(l, yy), Offset(r, yy), net);
    }

    canvas.drawPath(
      Path()
        ..moveTo(l, cy)
        ..lineTo(l, top)
        ..lineTo(r, top)
        ..lineTo(r, cy),
      Paint()
        ..color = Colors.white.withValues(alpha: 0.92)
        ..style = PaintingStyle.stroke
        ..strokeWidth = math.max(2, 0.2 * p.m)
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(covariant _Plane old) => old.grass != grass;
}
