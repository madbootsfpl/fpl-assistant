/// The eight axes as a radar — ⭐ **shape at a glance, with the bars underneath carrying the numbers**
/// (ADR-252).
///
/// ⭐⭐ **Why both.** A radar is very good at one thing — *is this a balanced side or a lopsided one?* —
/// and poor at another: you cannot read 74 off a vertex. The web draws both for that reason, and the phone
/// now does too. ⚠️ *Picking one would answer half the question and look like a decision.*
///
/// ⭐ Two clubs can share one radar, which is what makes comparison a **shape** rather than a table of
/// differences — the thing a reader takes in without counting.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'api/models.dart';

/// One outline on the radar.
typedef RadarSeries = ({String label, Color colour, List<DnaAxis> axes});

/// Straight up for the first axis, then clockwise — ⭐ the order the engine lists them in, so the shape
/// means the same thing here as on the web.
Offset radarVertex(Offset centre, double r, int i, int n) {
  final angle = -math.pi / 2 + (2 * math.pi * i / n);
  return Offset(
    centre.dx + r * math.cos(angle),
    centre.dy + r * math.sin(angle),
  );
}

/// Where one club's outline touches, for a given centre and radius.
///
/// ⭐⭐⭐ **Pulled out of the painter so it can be asserted on.** Three mutations survived a first round of
/// widget tests — an unranked axis drawn at mid-table, the empty-axes guard removed, the ring unclamped —
/// because those tests only checked that nothing *threw*. ⚠️ **A painter drawing a plausible-but-wrong
/// shape throws nothing**, and a radar's whole job is to be believed at a glance without checking. *The
/// geometry had to become arithmetic before a test could see it.*
///
/// ⚠️ **Null is placed at the centre, not skipped.** Skipping closes the polygon across the gap and
/// invents a shape; the centre says "nothing here", which is what null means.
List<Offset> radarPoints(List<DnaAxis> axes, Offset centre, double radius) => [
  for (var i = 0; i < axes.length; i++)
    radarVertex(
      centre,
      radius * ((axes[i].percentile ?? 0) / 100),
      i,
      axes.length,
    ),
];

class DnaRadar extends StatelessWidget {
  const DnaRadar({required this.series, super.key});

  final List<RadarSeries> series;

  @override
  Widget build(BuildContext context) {
    if (series.isEmpty || series.first.axes.isEmpty) {
      return const SizedBox.shrink();
    }
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // ⚠️⚠️ **`Flexible`, not a bare `AspectRatio`.** Square-on-full-width plus a legend is taller
        // than a height-bounded parent, and it overflowed the moment a second club added the legend —
        // caught by a widget test in a 320×320 box, never by the app, because there it lives in a
        // scroll view where height is free. ⭐ *A widget that only works in an unbounded parent works by
        // luck until someone puts it somewhere else.*
        Flexible(
          child: AspectRatio(
            // ⚠️ Square, so the web and the polygon stay regular. A stretched radar reads as a lopsided
            // team, which is a claim the data did not make.
            aspectRatio: 1,
            child: CustomPaint(
              painter: _RadarPainter(series: series),
              child: const SizedBox.expand(),
            ),
          ),
        ),
        if (series.length > 1)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (final s in series) ...[
                  Container(
                    width: 10,
                    height: 10,
                    margin: const EdgeInsets.only(right: 5, left: 10),
                    decoration: BoxDecoration(
                      color: s.colour,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  Text(
                    s.label,
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                ],
              ],
            ),
          ),
      ],
    );
  }
}

class _RadarPainter extends CustomPainter {
  _RadarPainter({required this.series});

  final List<RadarSeries> series;

  /// ⭐ Room for the labels, which sit **outside** the web. Drawing them on top of it is how a radar
  /// becomes unreadable at this size.
  static const double _labelRoom = 46;

  @override
  void paint(Canvas canvas, Size size) {
    final axes = series.first.axes;
    final n = axes.length;
    final centre = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2 - _labelRoom;
    if (radius <= 0) return;

    // ── the web ──
    final web = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..color = Colors.white12;
    for (final ring in [0.25, 0.5, 0.75, 1.0]) {
      canvas.drawPath(_polygon(centre, radius * ring, n), web);
    }
    for (var i = 0; i < n; i++) {
      canvas.drawLine(centre, radarVertex(centre, radius, i, n), web);
    }

    // ── each club ──
    for (final s in series) {
      final points = radarPoints(s.axes, centre, radius);
      final path = Path()..addPolygon(points, true);
      canvas.drawPath(
        path,
        Paint()
          ..style = PaintingStyle.fill
          ..color = s.colour.withValues(alpha: series.length > 1 ? 0.22 : 0.28),
      );
      canvas.drawPath(
        path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..color = s.colour,
      );
      for (final p in points) {
        canvas.drawCircle(p, 2.6, Paint()..color = s.colour);
      }
    }

    // ── the labels ──
    for (var i = 0; i < n; i++) {
      _label(canvas, centre, radius, i, n, axes[i].label);
    }
  }

  Path _polygon(Offset centre, double r, int n) => Path()
    ..addPolygon([
      for (var i = 0; i < n; i++) radarVertex(centre, r, i, n),
    ], true);

  /// ⭐ Straight up for the first axis, then clockwise — the order the engine lists them in, so the shape
  /// means the same thing here as on the web.

  void _label(
    Canvas canvas,
    Offset centre,
    double r,
    int i,
    int n,
    String text,
  ) {
    final at = radarVertex(centre, r + 16, i, n);
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: const TextStyle(color: Colors.white54, fontSize: 9, height: 1.2),
      ),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
      maxLines: 2,
    )..layout(maxWidth: _labelRoom * 1.7);

    // ⚠️ Anchored by which side of the circle it is on: a label centred on its vertex overlaps the web on
    // the left and right, where there is least room.
    final dx = at.dx < centre.dx - 4
        ? -painter.width
        : at.dx > centre.dx + 4
        ? 0.0
        : -painter.width / 2;
    canvas.drawParagraphOffset(
      painter,
      Offset(at.dx + dx, at.dy - painter.height / 2),
    );
  }

  @override
  bool shouldRepaint(_RadarPainter old) => old.series != series;
}

extension on Canvas {
  void drawParagraphOffset(TextPainter painter, Offset at) =>
      painter.paint(this, at);
}
