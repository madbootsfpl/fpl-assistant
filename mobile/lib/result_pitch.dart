/// A played gameweek, drawn on the pitch (ADR-298, after feedback).
///
/// ⭐⭐⭐ **The first build drew a played week as a list and the owner's reply was immediate** — *"the
/// right swipe into history shows a list rather than a pitch layout."* He is right, and the reason is
/// worth writing down: **the pitch is how this app says "your team".** A list of the same fifteen names
/// with the same fifteen numbers says *"a report about your team"* instead, and the whole point of
/// swiping back is to see the side you picked, in the shape you picked it.
///
/// ⚠️ It reuses [PitchBoard], so every layout decision ADR-253 and ADR-293 paid for applies here without
/// being written twice — *a second copy of a layout is a second place for a bug that was already found
/// once to come back.*
library;

import 'package:flutter/material.dart';

import 'api/models.dart';
import 'brand.dart';
import 'pitch.dart';

/// A past week's eleven and bench, on the green.
class ResultPitch extends StatelessWidget {
  const ResultPitch({required this.result, this.onTapPlayer, super.key});

  final GameweekResult result;

  /// ⭐ Hands back the **whole entry**, not just the player: what he did that week is the one thing the
  /// sheet cannot look up for itself (ADR-299).
  final void Function(GameweekPlayer)? onTapPlayer;

  @override
  Widget build(BuildContext context) => PitchBoard<GameweekPlayer>(
    xi: result.xi,
    bench: result.bench,
    positionOf: (e) => e.player.position,
    card: (entry, width) => _ResultCard(
      entry: entry,
      kit: result.kitFor(entry),
      drawWidth: width,
      onTap: onTapPlayer == null ? null : () => onTapPlayer!(entry),
    ),
  );
}

/// One player's week, on a card the same shape as the live one.
///
/// ⭐ **Same geometry, different contents.** A reader who has learnt the live card has learnt this one:
/// shirt, name, a number in a pill, a line underneath. ⚠️ *Changing the layout as well as the meaning
/// would make the two weeks look like two apps.*
class _ResultCard extends StatelessWidget {
  const _ResultCard({
    required this.entry,
    required this.kit,
    required this.drawWidth,
    this.onTap,
  });

  final GameweekPlayer entry;
  final String kit;
  final double drawWidth;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    behavior: HitTestBehavior.opaque,
    child: SizedBox(
      width: drawWidth,
      // ⚠️ The same box-inside-FittedBox as the live card, and for the same reason: a `FittedBox` hands
      // its child unbounded width, so the child must still be given something to be a fraction of.
      child: FittedBox(
        fit: drawWidth > 70 ? BoxFit.contain : BoxFit.scaleDown,
        child: SizedBox(
          width: 70,
          child: Column(
            children: [
              SizedBox(
                height: 34,
                child: Stack(
                  alignment: Alignment.bottomCenter,
                  clipBehavior: Clip.none,
                  children: [
                    // ⚠️⚠️ **Dimmed when he did not play.** A blank gameweek is not a bad gameweek, and
                    // the shirt is where that reads fastest — ⭐ *before the reader gets to the zero and
                    // has to work out which kind of zero it is.*
                    Opacity(
                      opacity: entry.didPlay ? 1 : 0.38,
                      child: kit.isEmpty
                          ? const Text('👕', style: TextStyle(fontSize: 22))
                          : Image.network(
                              // ⚠️⚠️ **A cross-origin image needs a CORS header on the web, and the two servers we
                              // take images from send none** (ADR-301). CanvasKit fetches the bytes in order to draw
                              // them, so the fetch fails and every kit and mugshot falls back to the 👕 — measured on
                              // the first desktop build, where all fifteen shirts came out identical.
                              //
                              // ⭐ `fallback` hands the URL to a plain `<img>` when the fetch fails, which a browser
                              // displays cross-origin quite happily because it never exposes the pixels to script.
                              // ⚠️ Ignored on mobile, so it costs nothing there.
                              webHtmlElementStrategy:
                                  WebHtmlElementStrategy.fallback,
                              kit,
                              height: 34,
                              errorBuilder: (_, _, _) => const Text(
                                '👕',
                                style: TextStyle(fontSize: 22),
                              ),
                            ),
                    ),
                    if (entry.isCaptain || entry.isViceCaptain)
                      Positioned(
                        top: -2,
                        right: 6,
                        child: _Band(entry.isCaptain ? 'C' : 'V'),
                      ),
                    // ⭐⭐ **The cards, where they cannot be missed** (feedback: *"the list does not have
                    // yellow or red cards"*). A booking is the one event a manager goes looking for and
                    // it was buried in a run-on line of glyphs — ⚠️ *an event you have to read a sentence
                    // to find is an event the screen did not report.*
                    if (entry.redCards > 0 || entry.yellowCards > 0)
                      Positioned(
                        top: -2,
                        left: 4,
                        child: _CardBadge(
                          red: entry.redCards > 0,
                          count: entry.redCards > 0
                              ? entry.redCards
                              : entry.yellowCards,
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 2),
              Text(
                entry.player.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: entry.didPlay ? Colors.white : Colors.white54,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 2),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 8,
                  vertical: 1.5,
                ),
                decoration: BoxDecoration(
                  color: _tint,
                  borderRadius: BorderRadius.circular(Brand.radiusPill),
                ),
                child: Text(
                  // ⚠️⚠️ **A blank gameweek is a dash, not a zero.** The rule the projection pages
                  // already follow — *zero is a score, absence is the absence of one* — and here the two
                  // are genuinely different facts about a real week.
                  entry.didPlay ? '${entry.points}' : '—',
                  style: const TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 2),
              // ⭐ What the points were for, in one line — the card's equivalent of the live card's
              // price-and-opponent strip.
              FittedBox(
                fit: BoxFit.scaleDown,
                child: _Events(entry: entry),
              ),
              // ⭐⭐ **Who it was against** (owner: *"for history GWs, can we see which club player played
              // against"*). The live card has carried its opponent since ADR-235 and the past card had
              // only events — ⚠️ *two points against City and two against Burnley are different weeks,
              // and the column that told them apart was the one missing.*
              if (_opponents.isNotEmpty)
                FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    _opponents,
                    style: const TextStyle(color: Colors.white54, fontSize: 9),
                  ),
                ),
            ],
          ),
        ),
      ),
    ),
  );

  /// ⚠️ **Banded by what the score means, not by a gradient.** A haul, a normal week, a blank — ⭐ *three
  /// readings a manager already has words for*, and the same difficulty-tint language the live card uses.
  Color get _tint {
    // ⭐ The same five-step language the fixture pills use (`difficultyTint`), read in the same
    // direction: green is good news, red is bad. ⚠️ *A second colour scale would make the reader learn
    // the app twice.*
    if (!entry.didPlay) return Colors.black.withValues(alpha: 0.35);
    if (entry.points >= 10) return Brand.good.withValues(alpha: 0.85);
    if (entry.points >= 6) return Brand.good.withValues(alpha: 0.55);
    if (entry.points >= 3) return Colors.black.withValues(alpha: 0.28);
    if (entry.points >= 1) return Brand.warn.withValues(alpha: 0.62);
    return Brand.bad.withValues(alpha: 0.72);
  }

  /// Who he played, in the app's existing `OPP (H)` shorthand.
  ///
  /// ⚠️ A **double gameweek shows both**, separated — *showing one of two is worse than showing neither,
  /// because it looks complete.* ⭐ Blank rather than a placeholder when the club is unknown: the rule
  /// `_recent_rows` set on the server, kept here.
  String get _opponents => [
    for (final m in entry.matches)
      if (m.opponent != null) '${m.opponent} (${m.home ? 'H' : 'A'})',
  ].join(' · ');
}

/// What he did, as icons (owner: *"I prefer the icons used by FFH, football for each goal, a boot for
/// assist etc., bonus point in a coloured circle"*).
///
/// ⭐⭐ **One icon per goal, not a number beside one icon.** Two footballs read as *two goals* before
/// anything is parsed; `⚽2` has to be read. ⚠️ Capped at three, because a hat-trick is the point at which
/// a 70pt card runs out of room and *four of anything is a number again anyway.*
///
/// ⚠️⚠️ **Drawn, not typed.** The first version used emoji and Android substituted its own: 🅰 came out
/// as a white A on a **red** box — on a screen whose other feature is red cards — and 🧤 came out as a
/// shield, the glyph already in use for a clean sheet. ⭐ *An emoji is a request, not an instruction*;
/// these are shapes this app draws itself and no font can reinterpret.
class _Events extends StatelessWidget {
  const _Events({required this.entry});

  final GameweekPlayer entry;

  @override
  Widget build(BuildContext context) {
    final icons = <Widget>[
      for (var i = 0; i < entry.goals && i < 3; i++) const _Ball(),
      for (var i = 0; i < entry.assists && i < 3; i++) const _Boot(),
      if (entry.cleanSheet) const _Sheet(),
      if (entry.saves >= 3) _Pip(text: '${entry.saves}', colour: Brand.purple),
      // ⭐ The bonus in its own coloured circle, which is how FPL itself prints it.
      if (entry.bonus > 0)
        _Pip(text: '${entry.bonus}', colour: const Color(0xFFE59A1B)),
    ];
    if (icons.isEmpty) {
      // ⚠️ Never blank: an empty strip would make the card a different height from its neighbours, which
      // is the grid problem the live card already solved once.
      return Text(
        !entry.didPlay
            ? (entry.benched ? 'benched' : 'did not play')
            : entry.cameOn
            ? 'came on'
            : entry.wentOff
            ? 'auto-sub'
            : '${entry.minutes} mins',
        style: const TextStyle(color: Colors.white70, fontSize: 9.5),
      );
    }
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (final icon in icons)
          Padding(padding: const EdgeInsets.only(right: 2), child: icon),
      ],
    );
  }
}

/// A goal.
class _Ball extends StatelessWidget {
  const _Ball();

  @override
  Widget build(BuildContext context) => Container(
    width: 10,
    height: 10,
    decoration: BoxDecoration(
      color: Colors.white,
      shape: BoxShape.circle,
      border: Border.all(color: Colors.black54, width: 1.2),
    ),
  );
}

/// An assist — a boot.
///
/// ⚠️⚠️ **Drawn, because Material has no football boot and the nearest icon was a ball outline** — which
/// on a strip whose first icon is a **ball** is the one shape it must not be. ⭐ *An icon that has to be
/// told apart from the icon beside it is doing less work than the word it replaced.*
///
/// ⭐ A silhouette: ankle, instep, sole. At 11pt the sole's overhang is the whole read.
class _Boot extends StatelessWidget {
  const _Boot();

  @override
  Widget build(BuildContext context) => const SizedBox(
    width: 12,
    height: 11,
    child: CustomPaint(painter: _BootPainter()),
  );
}

class _BootPainter extends CustomPainter {
  const _BootPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    final ink = Paint()..color = const Color(0xFF9FE6B8);

    // ⭐ **Shaft, instep, toe** — the three parts that make a silhouette a boot rather than an L. The
    // first version drew a thin upright and a bar, and at 11pt it read as a corner.
    final boot = Path()
      // Up the back of the ankle and across its top.
      ..moveTo(w * 0.10, h * 0.72)
      ..lineTo(w * 0.10, h * 0.08)
      ..lineTo(w * 0.44, h * 0.08)
      // Down the front of the shaft, then forward along the instep to the toe.
      ..lineTo(w * 0.44, h * 0.40)
      ..lineTo(w * 0.84, h * 0.55)
      // ⭐ The toe is rounded — a square one reads as a box.
      ..quadraticBezierTo(w * 0.99, h * 0.60, w * 0.97, h * 0.72)
      ..close();
    canvas.drawPath(boot, ink);

    // The sole, proud of the boot on both ends — the part that says "football boot".
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(w * 0.04, h * 0.74, w * 0.94, h * 0.18),
        const Radius.circular(1),
      ),
      ink,
    );
  }

  @override
  bool shouldRepaint(covariant _BootPainter oldDelegate) => false;
}

/// A clean sheet.
class _Sheet extends StatelessWidget {
  const _Sheet();

  @override
  Widget build(BuildContext context) =>
      const Icon(Icons.shield, size: 10, color: Color(0xFF8FB8D6));
}

/// A number in a coloured circle — bonus, and saves.
class _Pip extends StatelessWidget {
  const _Pip({required this.text, required this.colour});

  final String text;
  final Color colour;

  @override
  Widget build(BuildContext context) => Container(
    width: 12,
    height: 12,
    alignment: Alignment.center,
    decoration: BoxDecoration(color: colour, shape: BoxShape.circle),
    child: Text(
      text,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 8,
        fontWeight: FontWeight.w700,
        height: 1,
      ),
    ),
  );
}

class _Band extends StatelessWidget {
  const _Band(this.letter);

  final String letter;

  @override
  Widget build(BuildContext context) => Container(
    width: 14,
    height: 14,
    alignment: Alignment.center,
    decoration: const BoxDecoration(
      color: Brand.purple,
      shape: BoxShape.circle,
    ),
    child: Text(
      letter,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 8.5,
        fontWeight: FontWeight.w700,
      ),
    ),
  );
}

/// A booking, drawn as the thing it is.
///
/// ⭐ A coloured rectangle, not an emoji: 🟨 renders at the mercy of the platform's font and comes out
/// grey on some Android builds — ⚠️ *the one event whose whole meaning is its colour.*
class _CardBadge extends StatelessWidget {
  const _CardBadge({required this.red, required this.count});

  final bool red;
  final int count;

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      // ⚠️ **Outlined in white, and half as big again as the first version.** A booking sits on top of a
      // club shirt, so it has no background it can rely on — ⭐ *a yellow rectangle on a yellow kit is a
      // rectangle nobody sees*, and the owner's report was exactly "don't see red or yellow cards".
      Container(
        width: 11,
        height: 15,
        decoration: BoxDecoration(
          color: red ? const Color(0xFFE5343D) : const Color(0xFFF5C518),
          borderRadius: BorderRadius.circular(2),
          border: Border.all(color: Colors.white, width: 1),
          boxShadow: const [
            BoxShadow(color: Colors.black54, blurRadius: 2, spreadRadius: 0.5),
          ],
        ),
      ),
      // ⚠️ Only when there were two — a "1" beside every booking is noise on a 70pt card.
      if (count > 1)
        Padding(
          padding: const EdgeInsets.only(left: 2),
          child: Text(
            '$count',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 8.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
    ],
  );
}
