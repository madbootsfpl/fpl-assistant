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
  /// 🔴🔴 **OFF. The perspective pitch was tried and reverted** (ADR-333). The app draws the flat 2D
  /// grass pitch — `PitchTurf` and `PitchLines` — which is where the turf (ADR-329), the tuned
  /// markings and the centring fix (ADR-330) all live and all still ship.
  ///
  /// ⚠️⚠️ **It was not a tuning problem.** This layout positions rows at fixed fractions of the board,
  /// so a card has to fit the gap and nothing makes it. The flat pitch divides its space with
  /// `Expanded`, which works for any card height including ones that do not exist yet — and the
  /// season card is 111px against the live card's 80, so it overlapped by construction.
  ///
  /// ⭐⭐⭐ *A layout that has to be told about its content will be wrong about content nobody told it
  /// about* — three surfaces broke that I had never rendered, each behind a green suite.
  ///
  /// Set to `true` to see it again. The last build that shipped it is **1.0.0+35**; the last without
  /// it is tagged **`pitch-2d`**.
  static bool on = false;

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
  /// How much stretched foreground to cut off, **as a share of the board's height**.
  ///
  /// 🔴 It was a flat 110px, which is 22% of a portrait board and **37% of a landscape one** — so
  /// landscape cropped away the half of the pitch the midfield and attack were standing on.
  /// ⚠️ *A pixel budget tuned on one screen is a different design on another.*
  static const double cropShare = 0.22;
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
  /// Where each row stands, as a **fraction of the pitch on show** — not as metres.
  ///
  /// 🔴 **Metres broke landscape completely.** A wide, short board shows far less of the pitch's
  /// length (58m against portrait's 87m), so rows fixed at 44/68/86m put two thirds of the team
  /// past the near edge and off the screen. ⚠️ *A position in metres is a position on a pitch you
  /// have decided how much of to show.*
  /// Where each row sits, as a fraction of the **board's height on screen**.
  ///
  /// 🔴 **Third attempt, and the first that is not a chain of guesses.** Metres broke landscape — a
  /// short board shows 58m where a tall one shows 87, so fixed metres put the attack off-screen.
  /// Fractions of the plane broke both, because the plane runs past the bottom of the screen by
  /// design. ⭐⭐ *Say where it goes on the screen and solve the pitch backwards*: the projection
  /// inverts in closed form, so a row still stands on the grass and still scales with depth, but it
  /// lands where the layout needs it whatever shape the board is.
  static const Map<String, double> rows = {
    'DEF': 0.40,
    'MID': 0.62,
    'FWD': 0.84,
  };

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
    // ⭐⭐ `crop` lengthens the plane **downwards, past the bottom of the screen**, so the stretched
    // foreground is cut off — and because the projected height grows by exactly the same amount the
    // origin moves down, ⚠️ *the goal line does not shift at all.*
    final t = Pitch3D.tilt * math.pi / 180;
    final h = math.max(
      80.0,
      box.height * (1 + Pitch3D.cropShare) - Pitch3D.topGap,
    );
    final den = math.cos(t) * Pitch3D.dist - h * math.sin(t);
    ph = den > 1 ? h * Pitch3D.dist / den : h;
    // 🔴 **At least as wide as the board.** Derived from the height alone the plane came out 188px
    // narrower than a landscape board, leaving the pitch a trapezoid floating in the middle of the
    // screen. ⭐ *How much of the pitch you can show is a consequence of the screen's shape, not a
    // number you get to pick* — so the width binds, and the length falls out of it below.
    pw = math.max(
      ph * Pitch3D.width / (Pitch3D.runOff + Pitch3D.shown * Pitch3D.length),
      box.width,
    );
  } else {
    pw = box.width * Pitch3D.zoom;
    ph = pw * (Pitch3D.shown * Pitch3D.length + Pitch3D.runOff) / Pitch3D.width;
  }
  return (
    pw: pw,
    ph: ph,
    ox: box.width / 2,
    oy: box.height * (1 + Pitch3D.cropShare) - Pitch3D.lift,
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
/// The metres of pitch beyond the goal line that this plane actually shows.
///
/// ⭐ Derived, because the board's shape decides it: a wide short screen shows less of the length.
double shownMetres(
  ({double pw, double ph, double ox, double oy, double m}) p,
) => p.ph / p.m - Pitch3D.runOff;

/// The point on the plane that lands at [screenY] — [project] run backwards.
///
/// ⭐ `y = ly·cos·d / (d − ly·sin)` solves for `ly` in one step, so a row can be asked for by where it
/// should appear and still be a real position on the grass.
double planeYAt(
  ({double pw, double ph, double ox, double oy, double m}) p,
  double screenY,
) {
  final t = Pitch3D.tilt * math.pi / 180;
  final y = screenY - p.oy;
  return y * Pitch3D.dist / (math.cos(t) * Pitch3D.dist + y * math.sin(t));
}

/// Where a row stands on the plane, given where it should sit on the board.
double rowPlaneY(
  ({double pw, double ph, double ox, double oy, double m}) p,
  String position,
  double boardHeight,
) => planeYAt(p, (Pitch3D.rows[position] ?? 0.5) * boardHeight);

/// The advertising band across the back of the run-off, in screen coordinates.
///
/// ⚠️⚠️ **Exposed so the wordmark can be a widget.** It was painted here with a `TextPainter` in one
/// flat purple — ⭐⭐ *a seventh hand-built MADBOOTS, which is the exact thing ADR-312 exists to stop*
/// (MAD in purple, BOOTS in orange, italic, tracking in em). The brand is one widget; a painter that
/// cannot use it must not draw the brand.
Rect hoardingBand(({double pw, double ph, double ox, double oy, double m}) p) {
  final back = project(0, -p.ph);
  final y = p.oy + back.y;
  final half = p.pw * back.k / 2;
  final h = half * 2 * Pitch3D.hoardHeight;
  return Rect.fromLTRB(p.ox - half, y - h, p.ox + half, y);
}

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
  final mouth = p.oy + line.y - goalHeightFor(goalWidthFor(p)) / 2;
  // ⚠️⚠️ **The SHIRT goes in the goal, not the card.** Centring the whole card on the mouth put the
  // bottom of the jersey on the crossbar and the kit above it — the card is ~80pt tall and the kit is
  // only its top 34pt, so its middle is nowhere near its shirt. ⭐ *Aligning a thing by its bounding
  // box aligns the box, and nobody is looking at the box.*
  return mouth + (40 - 17) * (cardW / 70);
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
    final band = hoardingBand(p);
    canvas.drawRect(band, Paint()..color = const Color(0xFF1D1730));
    canvas.drawRect(
      band,
      Paint()
        ..color = Colors.white.withValues(alpha: 0.10)
        ..style = PaintingStyle.stroke,
    );

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
