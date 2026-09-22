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
                    width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
              ),
            );
          }
          if (snapshot.hasError) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Text(friendlyError(snapshot.error),
                  style: const TextStyle(color: Colors.white54, fontSize: 11, height: 1.45)),
            );
          }
          final battle = snapshot.data!;
          final (aWins, bWins) = battle.tally;

          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: Text(battle.a.player.name,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: Colors.white54, fontSize: 11.5, fontWeight: FontWeight.w600)),
                  ),
                  // ⭐ The tally is a headline, deliberately small: it is a count of stats, not a verdict.
                  Text('$aWins–$bWins',
                      style: const TextStyle(color: Colors.white38, fontSize: 10.5)),
                  Expanded(
                    child: Text(battle.b.player.name,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.right,
                        style: const TextStyle(
                            color: Colors.white, fontSize: 11.5, fontWeight: FontWeight.w600)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              _Form(a: battle.a, b: battle.b),
              const SizedBox(height: 8),
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
            child: Text('LAST 5',
                style: TextStyle(color: Colors.white24, fontSize: 9, letterSpacing: 1)),
          ),
          const SizedBox(height: 4),
          _FormRow(contender: a, dim: true),
          const SizedBox(height: 3),
          _FormRow(contender: b, dim: false),
        ],
      );
}

class _FormRow extends StatelessWidget {
  const _FormRow({required this.contender, required this.dim});

  final Contender contender;
  final bool dim;

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
                  color: dim ? Colors.white10 : Brand.purple.withValues(alpha: 0.35),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Column(
                  children: [
                    Text('${game.points}',
                        style: TextStyle(
                            color: dim ? Colors.white60 : Colors.white,
                            fontSize: 11.5,
                            fontWeight: FontWeight.w700)),
                    // ⚠️ Minutes, because **ten points off the bench is not ten points from a starter** —
                    // a form line without them flatters a substitute.
                    Text("${game.minutes}'",
                        style: const TextStyle(color: Colors.white24, fontSize: 7.5)),
                  ],
                ),
              ),
            ),
          if (contender.recent.isEmpty)
            const Expanded(
              child: Text('no games yet',
                  style: TextStyle(color: Colors.white24, fontSize: 10)),
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
          child: Text('PROJECTED',
              style: TextStyle(color: Colors.white24, fontSize: 9, letterSpacing: 1)),
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
              Text('GW$gw', style: const TextStyle(color: Colors.white24, fontSize: 8)),
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
        final x = size.width * (values.length == 1 ? 0.5 : i / (values.length - 1));
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

    line(a, Colors.white30, 1.6);
    line(b, Brand.accentTeal, 2.2);
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
              child: Text(row.a,
                  style: TextStyle(
                      // ⭐ The winner is tinted, not ticked: a column of ticks reads as a scorecard, and
                      // this is a reading, not a result.
                      color: row.winner == 'a' ? Brand.accentTeal : Colors.white38,
                      fontSize: 12,
                      fontWeight: row.winner == 'a' ? FontWeight.w700 : FontWeight.w400)),
            ),
            Expanded(
              flex: 2,
              child: Text(row.label,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white24, fontSize: 10)),
            ),
            Expanded(
              child: Text(row.b,
                  textAlign: TextAlign.right,
                  style: TextStyle(
                      color: row.winner == 'b' ? Brand.accentTeal : Colors.white38,
                      fontSize: 12,
                      fontWeight: row.winner == 'b' ? FontWeight.w700 : FontWeight.w400)),
            ),
          ],
        ),
      );
}
