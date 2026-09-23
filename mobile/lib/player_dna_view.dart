/// Player DNA — what kind of player is he? (ADR-250)
///
/// ⭐⭐ **Ranked within his position, never across the league.** A defender's attacking threat and a
/// forward's are not the same question; one scale across incomparable roles flatters and punishes by
/// position. The screen says which pool he was ranked in, because ⚠️ *a percentile is only as meaningful
/// as the field it was measured in.*
///
/// ⭐ Opens on your own fifteen — *the players you are already deciding about* — with the whole board a
/// search away.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'dna_bars.dart';
import 'dna_radar.dart';
import 'help_dot.dart';
import 'mugshot.dart';

class PlayerDnaView extends StatefulWidget {
  const PlayerDnaView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<PlayerDnaView> createState() => _PlayerDnaViewState();
}

class _PlayerDnaViewState extends State<PlayerDnaView> {
  int? _picked;
  Future<PlayerDna>? _dna;

  @override
  void initState() {
    super.initState();
    // ⭐ Straight into the captain's fingerprint. An empty picker is a screen that asks a question before
    // it has said anything — and the captain is the pick a manager is least willing to be wrong about.
    final opening =
        widget.team.captainId ?? widget.team.analysis.xi.firstOrNull?.id;
    if (opening != null) _pick(opening);
  }

  void _pick(int id) => setState(() {
    _picked = id;
    _dna = widget.client.playerDna(id);
  });

  List<PlayerSummary> get _mine => [
    ...widget.team.analysis.xi,
    ...widget.team.analysis.bench,
  ];

  @override
  Widget build(BuildContext context) {
    // ⚠️ **Your fifteen only, for now.** A search across all 481 was half-written here and cut: it needs
    // the board fetched, which is a second round trip on a screen that already makes one — and the
    // question *"what kind of player is he?"* is asked about someone you are deciding on. ⭐ *Shipping the
    // half that works beats a picker that loads twice to answer the same question.* 📌 Search is owed
    // when this screen can be reached from the Players tab.
    final options = _mine;

    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 22),
      children: [
        SizedBox(
          height: 34,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: [
              for (final p in options)
                Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: GestureDetector(
                    onTap: () => _pick(p.id),
                    behavior: HitTestBehavior.opaque,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 7,
                      ),
                      decoration: BoxDecoration(
                        color: _picked == p.id ? Brand.purple : Colors.white10,
                        borderRadius: BorderRadius.circular(Brand.radiusPill),
                      ),
                      child: Text(
                        p.name,
                        style: TextStyle(
                          color: _picked == p.id
                              ? Colors.white
                              : Colors.white54,
                          fontSize: 12.5,
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (_dna == null)
          const Padding(
            padding: EdgeInsets.all(24),
            child: Center(
              child: Text(
                'Pick a player.',
                style: TextStyle(color: Colors.white38),
              ),
            ),
          )
        else
          FutureBuilder<PlayerDna>(
            future: _dna,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.all(28),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError) {
                return Padding(
                  padding: const EdgeInsets.all(16),
                  child: SelectableText(
                    friendlyError(snapshot.error),
                    style: const TextStyle(color: Colors.white70, height: 1.55),
                  ),
                );
              }
              return PlayerFingerprint(dna: snapshot.data!);
            },
          ),
      ],
    );
  }
}

/// A player's fingerprint — ⭐ **public, because it is now shown in two places** (ADR-277): its own
/// screen, and under the stats when a row is expanded in Players.
///
/// ⚠️ `showHeader` is false there: the card above it has already named him, and *a screen that names a
/// player twice has two headings and one subject.*
class PlayerFingerprint extends StatelessWidget {
  const PlayerFingerprint({
    required this.dna,
    this.showHeader = true,
    super.key,
  });

  final PlayerDna dna;
  final bool showHeader;

  @override
  Widget build(BuildContext context) {
    if (dna.unranked != null) {
      // ⭐ Say why. An empty radar reads as "this player is bad at everything", which is a claim nobody
      // made.
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Text(
          'No fingerprint for ${dna.player.name} — ${dna.unranked}.',
          style: const TextStyle(color: Colors.white54, height: 1.5),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (showHeader)
          Row(
            children: [
              Mugshot(url: dna.photo, name: dna.player.name, size: 40),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  dna.player.name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Text(
                '${dna.player.position} · ${dna.player.team} · '
                '£${dna.player.price.toStringAsFixed(1)}m',
                style: const TextStyle(color: Colors.white54, fontSize: 12),
              ),
            ],
          ),
        Row(
          children: [
            Flexible(
              child: Text(
                // ⚠️⚠️ **The field, not just the place in it.** "84th" alone invites over-reading; early
                // in a season the pool can be ten players, and a reader has to be able to see that.
                'Percentile among ${dna.poolSize} '
                '${dna.player.position} with ${dna.minMinutes}+ minutes',
                style: const TextStyle(color: Colors.white38, fontSize: 11),
              ),
            ),
            const HelpDot('percentile', size: 12),
          ],
        ),
        if (dna.lowMinutes)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              // ⭐ Ranked anyway, and captioned — rather than excluded, which would lose a player a
              // manager is actively considering (ADR-118).
              '⚠ He is below ${dna.minMinutes} minutes himself, so read the shape with care.',
              style: const TextStyle(
                color: Brand.warn,
                fontSize: 11,
                height: 1.4,
              ),
            ),
          ),
        const SizedBox(height: 12),
        // ⭐ The same pairing as the club page: the radar for the shape, the bars for the numbers.
        DnaRadar(
          series: [
            (label: dna.player.name, colour: Brand.purpleLight, axes: dna.axes),
          ],
        ),
        const SizedBox(height: 8),
        DnaBars(axes: dna.axes),
        if (dna.insights.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'WHAT STANDS OUT',
            style: TextStyle(
              color: Colors.white38,
              fontSize: 10,
              letterSpacing: 1,
            ),
          ),
          for (final insight in dna.insights)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                '${dnaMark(insight.kind)}  ${insight.text}',
                style: TextStyle(
                  color: dnaColour(insight.kind),
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ),
        ],
      ],
    );
  }
}
