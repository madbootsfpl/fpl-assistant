/// The pitch the players stand on (ADR-223), on real turf (ADR-329).
///
/// ⭐ **Markings painted, not an image.** Drawn as vectors they scale to any phone without a second
/// asset, and — the part that matters — the lines can be positioned *relative to the card rows*, so a
/// five-defender formation and a three-defender one both look like a football pitch rather than like a
/// background someone laid players on top of.
///
/// ⭐⭐ **The grass, by contrast, *is* an image**, and that is the whole point of ADR-329: a gradient can
/// say "green", and only a photograph says "grass". ⚠️ It is the one thing here a vector cannot do, so it
/// is the one thing that earns an asset.
///
/// ⚠️ **The markings are orientation, not content**: the eye must land on the xP number first. ADR-135 is
/// this project's record of what happens when a surface is over-densified.
///
/// ⭐⭐⭐ **The grass and the lines are two widgets, and that is the whole of ADR-330.** [PitchTurf] fills
/// whatever box it is given — the green runs behind the bench, which is ADR-253 and still right. [PitchLines]
/// is laid out over **the playing area only**, because that is where the team stands.
///
/// 🔴 They were one widget, so the markings centred on the box *including* the bench while the players
/// centred on the box *without* it: **53px out in landscape, 132px in portrait.** ⚠️ *On a real pitch the
/// grass runs past the touchline and the paint does not* — one widget could not say that, so it said
/// something false in both orientations.
library;

import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// The turf, decoded once for the life of the app.
///
/// ⚠️ **A `Future`, held statically, not an image held statically.** Every pitch in the app asks for the
/// same one, and the second asker must join the first request rather than start a second decode —
/// ⭐ *a cache keyed on "have I finished yet" races with itself; one keyed on the request does not.*
Future<ui.Image>? _turfRequest;

Future<ui.Image> _turf() => _turfRequest ??= () async {
  final data = await rootBundle.load('assets/pitch-grass.webp');
  final codec = await ui.instantiateImageCodec(data.buffer.asUint8List());
  return (await codec.getNextFrame()).image;
}();

/// ⚠️ Visible for tests that need the pitch drawn without waiting on an asset.
@visibleForTesting
void resetTurfForTest() => _turfRequest = null;

/// The grass. ⭐ Fills its box completely — it is the surface, not the pitch.
class PitchTurf extends StatefulWidget {
  const PitchTurf({required this.child, super.key});

  final Widget child;

  @override
  State<PitchTurf> createState() => _PitchTurfState();
}

class _PitchTurfState extends State<PitchTurf> {
  ui.Image? _grass;

  @override
  void initState() {
    super.initState();
    // ⭐⭐ **The pitch draws immediately and the turf arrives late.** Until it does, `_Markings` paints the
    // gradient this widget shipped with — ⚠️ *a pitch that waits for an image is a pitch that flashes
    // empty*, and on a cold start that is the first thing anyone sees.
    _turf()
        .then((image) {
          if (mounted) setState(() => _grass = image);
        })
        .catchError((Object _) {
          // A missing or corrupt asset must not take the pitch down: the gradient is a complete answer.
        });
  }

  @override
  Widget build(BuildContext context) => CustomPaint(
    painter: _Turf(_grass),
    // ⚠️ `isComplex` off and no animation: this repaints only when the pitch resizes, or once, when the
    // turf lands.
    child: widget.child,
  );
}

class _Turf extends CustomPainter {
  _Turf(this.grass);

  /// Null until the asset decodes, and after any failure to.
  final ui.Image? grass;

  static final Paint _stripe = Paint()
    ..color = Colors.white.withValues(alpha: 0.035);

  /// The pitch under the turf, and the whole pitch when there is no turf.
  static const Color _base = Color(0xFF146B30);

  /// One mown band is `height / _bands`, and every other one is painted.
  static const int _bands = 6;

  /// How big one tile of the turf is drawn, in logical pixels.
  ///
  /// ⭐ Chosen on the phone and left alone on the tablet: the blades are a real size, so scaling the tile
  /// with the screen would make a tablet's grass look like a lawn seen from lower down.
  static const double _tile = 180;

  /// The grass, then the two lighting layers that sit **under** the markings.
  ///
  /// ⭐ Lifted whole from the owner's own mockup, vignette and top light included. *The photograph alone
  /// looks like wallpaper; it is the lighting over it that makes it a place with a middle and edges.*
  void _paintTurf(Canvas canvas, double w, double h) {
    final full = Rect.fromLTWH(0, 0, w, h);

    if (grass == null) {
      // ⚠️ The gradient the pitch shipped with, kept as the answer for a cold frame or a failed decode.
      canvas.drawRect(
        full,
        Paint()
          ..shader = const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF419462), Color(0xFF34754E)],
          ).createShader(full),
      );
    } else {
      canvas.drawRect(full, Paint()..color = _base);
      final scale = _tile / grass!.width;
      canvas.drawRect(
        full,
        Paint()
          ..shader = ImageShader(
            grass!,
            TileMode.repeated,
            TileMode.repeated,
            Matrix4.diagonal3Values(scale, scale, 1).storage,
            filterQuality: FilterQuality.low,
          ),
      );
    }

    // Vignette: an ellipse as wide as the pitch and 85% as tall, centred a little above the middle.
    // ⚠️ Drawn through a scaled canvas rather than as a circular gradient — *a radial gradient given one
    // radius cannot be an ellipse*, and the shape is what keeps the darkening off the corners only.
    final rx = w, ry = h * 0.85;
    canvas.save();
    canvas.translate(w * 0.5, h * 0.35);
    canvas.scale(1, ry / rx);
    canvas.drawRect(
      Rect.fromLTRB(-w * 2, -h * 2 / (ry / rx), w * 2, h * 2 / (ry / rx)),
      Paint()
        ..shader = const RadialGradient(
          colors: [
            Color(0x00001405),
            Color(0x00001405),
            Color(0x40001405),
            Color(0x8C000F05),
          ],
          stops: [0, 0.45, 0.75, 1],
        ).createShader(Rect.fromCircle(center: Offset.zero, radius: rx)),
    );
    canvas.restore();

    // Top light — ⭐ dimmed to 0.65 of the mockup's, on the owner's own reading of it.
    canvas.drawRect(
      full,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color(0x0AFFFFFF),
            Color(0x00FFFFFF),
            Color(0x00000000),
            Color(0x19000000),
          ],
          stops: [0, 0.3, 0.7, 1],
        ).createShader(full),
    );
  }

  @override
  void paint(Canvas canvas, Size size) {
    _paintTurf(canvas, size.width, size.height);

    // Mown stripes, horizontal so they read as depth rather than as columns fighting the card grid.
    // ⭐ They belong to the grass, not to the pitch: a mower does not stop at the touchline.
    for (var i = 0; i < _bands; i += 2) {
      canvas.drawRect(
        Rect.fromLTWH(
          0,
          size.height / _bands * i,
          size.width,
          size.height / _bands,
        ),
        _stripe,
      );
    }
  }

  /// ⚠️ Repaints once, when the turf lands. *A painter that never repaints cannot show an image it did
  /// not have when it was built.*
  @override
  bool shouldRepaint(covariant _Turf oldDelegate) => oldDelegate.grass != grass;
}

/// The white markings, laid out over **the playing area** — never over the bench.
///
/// ⭐⭐ *The grass runs past the touchline; the paint does not.* [PitchBoard] gives this the same box the
/// eleven divide between them, so the halfway line falls through the middle of the team rather than
/// through the middle of the screen.
class PitchLines extends StatelessWidget {
  const PitchLines({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) =>
      CustomPaint(painter: _Lines(), child: child);
}

class _Lines extends CustomPainter {
  /// ⚠️⚠️ **0.42, where this was 0.22 for most of the app's life** (ADR-329). Not a change of mind about
  /// how loud the markings should be: at 0.22 they were tuned against a flat two-stop gradient, and a
  /// photograph of grass has texture of its own at roughly that contrast. ⭐ *A line drawn faintly over a
  /// flat colour reads as a line; the same line over noise reads as more noise.*
  static final Paint _line = Paint()
    ..color = Colors.white.withValues(alpha: 0.42)
    ..style = PaintingStyle.stroke
    ..strokeWidth = 1.4;

  static final Paint _spot = Paint()
    ..color = Colors.white.withValues(alpha: 0.42);

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

    const inset = 6.0;
    final field = Rect.fromLTWH(inset, inset, w - inset * 2, h - inset * 2);
    canvas.drawRect(field, _line);

    // The halfway line and centre circle.
    //
    // ⭐ The circle's radius is taken from the **pitch's own proportions**, not from its width alone: a real
    // centre circle is 9.15 m on a 68 m pitch, and clamping to a share of the *shorter* axis keeps it a
    // circle that fits rather than one that swallows the midfield on a narrow phone.
    final midY = field.center.dy;
    final radius = math.min(w * 0.13, h * 0.11);
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
  bool shouldRepaint(covariant _Lines oldDelegate) => false;
}
