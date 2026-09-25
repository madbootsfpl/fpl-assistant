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
  final void Function(PlayerSummary)? onTapPlayer;

  @override
  Widget build(BuildContext context) => PitchBoard<GameweekPlayer>(
    xi: result.xi,
    bench: result.bench,
    positionOf: (e) => e.player.position,
    card: (entry, width) => _ResultCard(
      entry: entry,
      kit: result.kitFor(entry),
      drawWidth: width,
      onTap: onTapPlayer == null ? null : () => onTapPlayer!(entry.player),
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
                child: Text(
                  _events,
                  style: const TextStyle(color: Colors.white70, fontSize: 9.5),
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

  /// The week in glyphs — ⭐ the number says how many, this says what for.
  String get _events {
    // ⚠️⚠️⚠️ **Two of these were emoji and rendered as something else entirely on Android.** 🅰 came out
    // as a **white A on a red rounded box** — which on a screen whose other new feature is *red cards* is
    // about the worst possible accident — and 🧤 came out as a shield, the glyph already being used one
    // slot along for a clean sheet.
    //
    // ⭐ *An emoji is a request, not an instruction*: the platform picks the font, and a card 70pt wide
    // has no room to survive a bad guess. ⚽ and 🛡 render correctly and stay; the two that did not are
    // now letters, which cannot be substituted for anything.
    final parts = <String>[
      if (entry.goals > 0) '⚽${entry.goals}',
      if (entry.assists > 0) 'A${entry.assists}',
      if (entry.cleanSheet) '🛡',
      if (entry.saves >= 3) 'SV${entry.saves}',
      if (entry.bonus > 0) '+${entry.bonus}',
    ];
    if (parts.isNotEmpty) return parts.join(' ');
    // ⚠️ Never blank: an empty strip would make the card a different height from its neighbours, which
    // is the grid problem the live card already solved once.
    if (!entry.didPlay) return entry.benched ? 'benched' : 'did not play';
    if (entry.cameOn) return 'came on';
    if (entry.wentOff) return 'auto-sub';
    return '${entry.minutes} mins';
  }
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
