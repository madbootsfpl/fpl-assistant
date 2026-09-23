/// Boot Battle — two players side by side (ADR-110/236).
///
/// ⭐⭐ **It lives inside the transfer card, not on a page of its own.** The web app has had this since
/// ADR-110, on the Players page, as a destination you navigate to — and a screen that suggests
/// `Groß → Belloumi` and cannot show you the two of them is sending you to another room to answer the
/// question it just raised.
///
/// ⚠️ **No verdict.** ADR-197 gave the DNA comparison none on purpose, and the same reasoning holds: a
/// count of stats won is a *headline*, not a recommendation. The engine already made a recommendation —
/// this is the working behind it.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'mugshot.dart';

/// ⭐⭐⭐ **Colour is identity here, not victory — and on the web it is the other way round.**
///
/// The web's Boot Battle tints the winning value teal and leaves the loser grey **on a white card**, where
/// grey is perfectly legible. On this near-black ground that same choice made the losing side, its form
/// row and its projection line all but invisible — ⚠️ *the owner could not read the page.*
///
/// So each player owns a colour throughout, and **winning a stat is shown by weight and a marker**. A
/// reader can follow one player down the page, and nobody disappears for losing.
const Color aColour = Brand.purpleLight;
const Color bColour = Brand.accentTeal;

class BootBattleView extends StatelessWidget {
  const BootBattleView({required this.future, super.key});

  final Future<BootBattle> future;

  @override
  Widget build(BuildContext context) => FutureBuilder<BootBattle>(
    future: future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Padding(
          padding: EdgeInsets.symmetric(vertical: 22),
          child: Center(
            child: SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ),
        );
      }
      if (snapshot.hasError) {
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: Text(
            friendlyError(snapshot.error),
            style: const TextStyle(
              color: Colors.white54,
              fontSize: 11,
              height: 1.45,
            ),
          ),
        );
      }
      final battle = snapshot.data!;
      final (aWins, bWins) = battle.tally;

      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _Band(),
          const SizedBox(height: 10),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _Head(contender: battle.a, colour: aColour, wins: aWins),
              ),
              // ⭐ The tally between them, and still deliberately quiet: it is a count of stats, not a
              // verdict (ADR-197). ⚠️ It was `white38` on near-black and effectively invisible.
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Column(
                  children: [
                    const SizedBox(height: 14),
                    Text(
                      '$aWins–$bWins',
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const Text(
                      'stats won',
                      style: TextStyle(color: Colors.white38, fontSize: 8.5),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: _Head(
                  contender: battle.b,
                  colour: bColour,
                  wins: bWins,
                  alignEnd: true,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _Form(a: battle.a, b: battle.b),
          const SizedBox(height: 10),
          _Run(battle: battle),
          const SizedBox(height: 8),
          for (final row in battle.rows) _Row(row: row),
        ],
      );
    },
  );
}

/// The last five gameweeks, as tiles. ⭐ The Hub's presentation, and a good one: a row of numbers reads as
/// a *trend* in a way a season average never does.
class _Form extends StatelessWidget {
  const _Form({required this.a, required this.b});

  final Contender a;
  final Contender b;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      const Align(
        alignment: Alignment.centerLeft,
        child: Text(
          'LAST 5',
          style: TextStyle(
            color: Colors.white54,
            fontSize: 9.5,
            letterSpacing: 1,
          ),
        ),
      ),
      const SizedBox(height: 4),
      // ⚠️⚠️ **One row used to be `white10` on near-black** — dark grey boxes on a dark ground, which is
      // what the owner could not read. Each row now carries its player's colour at a usable alpha, so
      // neither disappears and the pair is legible as a pair.
      // ⭐ Keyed so a test can ask each row what colour it actually drew. ⚠️ A mutation putting one row
      // back to a dark grey box survived a contrast test that only inspected **text** — *the boxes were
      // half the thing the owner could not read.*
      _FormRow(key: const Key('form-a'), contender: a, colour: aColour),
      const SizedBox(height: 3),
      _FormRow(key: const Key('form-b'), contender: b, colour: bColour),
    ],
  );
}

class _FormRow extends StatelessWidget {
  const _FormRow({required this.contender, required this.colour, super.key});

  final Contender contender;
  final Color colour;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      for (final game in contender.recent)
        Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 1.5),
            padding: const EdgeInsets.symmetric(vertical: 4),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: colour.withValues(alpha: 0.22),
              border: Border.all(color: colour.withValues(alpha: 0.5)),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Column(
              children: [
                Text(
                  '${game.points}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                // ⚠️ Minutes, because **ten points off the bench is not ten points from a starter** —
                // a form line without them flatters a substitute.
                Text(
                  // ⚠️ `white24` on this ground is a smudge. The minutes are the reason the points above
                  // them mean anything — *ten points off the bench is not ten points from a starter.*
                  "${game.minutes}'",
                  style: const TextStyle(color: Colors.white54, fontSize: 8),
                ),
              ],
            ),
          ),
        ),
      if (contender.recent.isEmpty)
        const Expanded(
          child: Text(
            'no games yet',
            style: TextStyle(color: Colors.white38, fontSize: 10),
          ),
        ),
    ],
  );
}

/// The projected run, drawn as two lines. ⭐ The one thing a stat grid cannot show: *where this is going*.
class _Run extends StatelessWidget {
  const _Run({required this.battle});

  final BootBattle battle;

  @override
  Widget build(BuildContext context) {
    final weeks = battle.gameweeks;
    if (weeks.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Align(
          alignment: Alignment.centerLeft,
          child: Text(
            'PROJECTED',
            style: TextStyle(
              color: Colors.white54,
              fontSize: 9.5,
              letterSpacing: 1,
            ),
          ),
        ),
        const SizedBox(height: 4),
        SizedBox(
          height: 46,
          child: CustomPaint(
            painter: _RunPainter(
              a: [for (final gw in weeks) battle.a.player.byGameweek[gw] ?? 0],
              b: [for (final gw in weeks) battle.b.player.byGameweek[gw] ?? 0],
            ),
            child: const SizedBox.expand(),
          ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            for (final gw in weeks)
              Text(
                'GW$gw',
                // ⚠️ The axis of the chart above it. At `white24` the reader could see two lines and not
                // which weeks they covered.
                style: const TextStyle(color: Colors.white54, fontSize: 8.5),
              ),
          ],
        ),
      ],
    );
  }
}

class _RunPainter extends CustomPainter {
  _RunPainter({required this.a, required this.b});

  final List<double> a;
  final List<double> b;

  @override
  void paint(Canvas canvas, Size size) {
    if (a.length < 2) return;
    // ⭐ **Both lines share one scale.** Normalising each to its own maximum would draw two flat lines and
    // call it a comparison — the whole point is which is higher.
    final peak = [...a, ...b].fold<double>(1, (m, v) => v > m ? v : m);

    void line(List<double> values, Color colour, double width) {
      final path = Path();
      for (var i = 0; i < values.length; i++) {
        final x =
            size.width * (values.length == 1 ? 0.5 : i / (values.length - 1));
        final y = size.height - (values[i] / peak) * size.height * 0.9 - 2;
        i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
      }
      canvas.drawPath(
        path,
        Paint()
          ..color = colour
          ..style = PaintingStyle.stroke
          ..strokeWidth = width
          ..strokeCap = StrokeCap.round,
      );
    }

    // ⚠️⚠️ **`white30` was the problem.** A 30%-white line on a near-black ground is a smudge, and the
    // owner's screenshot shows exactly that: one projection visible, the other barely there — on a chart
    // whose entire job is to compare two.
    //
    // ⭐ Both lines now carry their player's colour, at the same weight. *A comparison where one side is
    // harder to see is not a comparison.*
    line(a, aColour, 2.2);
    line(b, bColour, 2.2);
  }

  @override
  bool shouldRepaint(covariant _RunPainter old) => old.a != a || old.b != b;
}

class _Row extends StatelessWidget {
  const _Row({required this.row});

  final CompareRow row;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 2.5),
    child: Row(
      children: [
        Expanded(
          child: Text(
            row.a,
            style: TextStyle(
              // ⚠️⚠️ **`white38` for the losing value was the third contrast failure.** Every stat he
              // lost read as a smudge — on the grid that is most of the page.
              //
              // ⭐ His colour when he wins, plain white when he does not: *losing a stat should not make
              // the number unreadable*, and the weight already carries the result.
              color: row.winner == 'a' ? aColour : Colors.white70,
              fontSize: 12.5,
              fontWeight: row.winner == 'a' ? FontWeight.w700 : FontWeight.w400,
            ),
          ),
        ),
        Expanded(
          flex: 2,
          child: Text(
            row.label,
            textAlign: TextAlign.center,
            // ⚠️ The label is what tells you *what* the two numbers are. At `white24` it was the
            // faintest thing in the row it explains.
            style: const TextStyle(color: Colors.white54, fontSize: 10.5),
          ),
        ),
        Expanded(
          child: Text(
            row.b,
            textAlign: TextAlign.right,
            style: TextStyle(
              color: row.winner == 'b' ? bColour : Colors.white70,
              fontSize: 12.5,
              fontWeight: row.winner == 'b' ? FontWeight.w700 : FontWeight.w400,
            ),
          ),
        ),
      ],
    ),
  );
}

/// The MADBOOTS band — ⭐ **the web's own lockup, and its own word for this screen** (ADR-258).
///
/// The owner: *"we had it branded as Boot Battle on the desktop app, can we use that language."* He is
/// right, and it is not decoration: ⚠️ *a feature with two names is two features to anyone who has to be
/// told which is which.* `player_card.py` has titled it **Boot Battle** since the wave-3 feedback.
class _Band extends StatelessWidget {
  const _Band();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
    decoration: BoxDecoration(
      color: Colors.white10,
      borderRadius: BorderRadius.circular(Brand.radiusMd),
    ),
    child: Row(
      children: [
        const Image(
          image: AssetImage('assets/madboots-badge.png'),
          width: 16,
          height: 16,
          filterQuality: FilterQuality.medium,
        ),
        const SizedBox(width: 6),
        const Text.rich(
          TextSpan(
            children: [
              TextSpan(
                text: 'MAD',
                style: TextStyle(
                  color: Brand.purpleLight,
                  fontWeight: FontWeight.w700,
                ),
              ),
              TextSpan(
                text: 'BOOTS',
                style: TextStyle(color: Brand.orange),
              ),
            ],
          ),
          style: TextStyle(fontSize: 10.5, letterSpacing: .3),
        ),
        const Spacer(),
        const Text(
          'BOOT BATTLE',
          style: TextStyle(
            color: Colors.white,
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.2,
          ),
        ),
      ],
    ),
  );
}

/// One side's header — ⭐ photo, name, the facts, in **his** colour (ADR-258).
///
/// ⚠️ The colour is repeated on his form row, his projection line and his winning values, so a reader can
/// follow one player down the page without re-reading which side is which.
class _Head extends StatelessWidget {
  const _Head({
    required this.contender,
    required this.colour,
    required this.wins,
    this.alignEnd = false,
  });

  final Contender contender;
  final Color colour;
  final int wins;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    final p = contender.player;
    final photo = Mugshot(url: contender.photo, name: p.name, size: 38);
    final text = Column(
      crossAxisAlignment: alignEnd
          ? CrossAxisAlignment.end
          : CrossAxisAlignment.start,
      children: [
        Text(
          p.name,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          textAlign: alignEnd ? TextAlign.right : TextAlign.left,
          style: TextStyle(
            color: colour,
            fontSize: 14,
            fontWeight: FontWeight.w700,
          ),
        ),
        Text(
          '${p.team} · £${p.price.toStringAsFixed(1)}m',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(color: Colors.white54, fontSize: 10.5),
        ),
        Text(
          '${p.xp.toStringAsFixed(1)} xP',
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );

    return Row(
      // ⭐ Mirrored, so the two headers face each other across the tally rather than both reading
      // left-to-right into the middle of the screen.
      mainAxisAlignment: alignEnd
          ? MainAxisAlignment.end
          : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: alignEnd
          ? [Flexible(child: text), const SizedBox(width: 8), photo]
          : [photo, const SizedBox(width: 8), Flexible(child: text)],
    );
  }
}
