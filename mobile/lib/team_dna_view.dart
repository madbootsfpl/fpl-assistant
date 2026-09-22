/// Team DNA — what kind of side is this? (ADR-247)
///
/// ⭐⭐ **A club's fingerprint, not a player's**, and that is the choice. *What kind of player is he?* is
/// already answered twice — the expanding card (ADR-237) and Boot Battle (ADR-236). *Is this attack
/// actually any good?* decides between two players from different sides, and the app could not answer it.
///
/// ⭐ **Bars, where the web draws a radar.** A radar needs width a phone does not have, and eight labels
/// around a circle on a 390pt screen are unreadable. The numbers are identical; the shape is the one that
/// survives the screen. ⚠️ *Porting a layout is not the same as porting a view.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'dna_bars.dart';
import 'dna_radar.dart';
import 'grade_ring.dart';
import 'help_dot.dart';

class TeamDnaView extends StatefulWidget {
  const TeamDnaView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<TeamDnaView> createState() => _TeamDnaViewState();
}

class _TeamDnaViewState extends State<TeamDnaView> {
  late final Future<List<ClubDna>> _clubs = widget.client.teamDna(
    playerIds: [
      ...widget.team.analysis.xi.map((p) => p.id),
      ...widget.team.analysis.bench.map((p) => p.id),
    ],
  );

  /// ⭐ Off by default. *A default that narrows the answer is a default that hides something* — the table
  /// is the league, and yours is a lens over it.
  bool _mineOnly = false;

  /// ⭐ One comparison at a time, held here rather than in each row — two rows each comparing against
  /// something else would be two answers to one question.
  ClubDna? _against;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<ClubDna>>(
    future: _clubs,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Center(
            child: SelectableText(
              friendlyError(snapshot.error),
              style: const TextStyle(color: Colors.white70, height: 1.55),
            ),
          ),
        );
      }
      final all = snapshot.data!;
      final shown = _mineOnly ? all.where((c) => c.yours).toList() : all;

      return ListView(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 22),
        children: [
          Row(
            children: [
              Expanded(
                child: Row(
                  children: [
                    Flexible(
                      child: Text(
                        '${all.length} clubs by percentile rank',
                        style: const TextStyle(
                          color: Colors.white38,
                          fontSize: 11,
                        ),
                      ),
                    ),
                    // ⭐ "Percentile" is the word that makes every bar on this screen readable, and it
                    // is also the one a reader is most likely to take as a score.
                    const HelpDot('percentile', size: 12),
                  ],
                ),
              ),
              GestureDetector(
                onTap: () => setState(() => _mineOnly = !_mineOnly),
                behavior: HitTestBehavior.opaque,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: _mineOnly ? Brand.purple : Colors.white10,
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
                  ),
                  child: Text(
                    'Mine',
                    style: TextStyle(
                      color: _mineOnly ? Colors.white : Colors.white54,
                      fontSize: 11.5,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          for (final club in shown)
            _Club(
              club: club,
              others: all.where((o) => o.team != club.team).toList(),
              against: _against?.team == club.team ? null : _against,
              onCompare: (other) => setState(() => _against = other),
            ),
        ],
      );
    },
  );
}

class _Club extends StatefulWidget {
  const _Club({
    required this.club,
    required this.others,
    required this.against,
    required this.onCompare,
  });

  final ClubDna club;

  /// Everyone else, for the compare picker. ⭐ No new endpoint: all twenty clubs already arrived.
  final List<ClubDna> others;

  /// The club being compared against, or null. ⚠️ Held by the parent so opening a second club does not
  /// leave two comparisons running against each other.
  final ClubDna? against;
  final void Function(ClubDna?) onCompare;

  @override
  State<_Club> createState() => _ClubState();
}

class _ClubState extends State<_Club> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    final c = widget.club;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: () => setState(() => _open = !_open),
            borderRadius: BorderRadius.circular(Brand.radiusMd),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 10, 10),
              child: Row(
                children: [
                  _Grade(grade: c.grade),
                  const SizedBox(width: 11),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              c.name,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            if (c.yours) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 1,
                                ),
                                decoration: BoxDecoration(
                                  border: Border.all(
                                    color: Brand.purpleLight,
                                    width: 1,
                                  ),
                                  borderRadius: BorderRadius.circular(
                                    Brand.radiusPill,
                                  ),
                                ),
                                child: const Text(
                                  'yours',
                                  style: TextStyle(
                                    color: Brand.purpleLight,
                                    fontSize: 9,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                        if (c.insights.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Text(
                              // ⭐ The strongest one, closed. The rest are behind the tap — a list of four
                              // observations per club, twenty times over, is a wall.
                              c.insights.first.text,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                color: Colors.white38,
                                fontSize: 11,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  Icon(
                    _open ? Icons.expand_less : Icons.expand_more,
                    size: 19,
                    color: Colors.white24,
                  ),
                ],
              ),
            ),
          ),
          if (_open)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: GradeRing(grade: c.grade, score: c.score),
                  ),
                  const SizedBox(height: 6),
                  // ⭐⭐ **Radar AND bars**, as the web does. A radar answers *is this a balanced side or
                  // a lopsided one?* at a glance and cannot tell you 74; the bars can and cannot show you
                  // the shape. ⚠️ *Picking one would answer half the question and look like a decision.*
                  DnaRadar(
                    series: [
                      (label: c.name, colour: Brand.purpleLight, axes: c.axes),
                      if (widget.against != null)
                        (
                          label: widget.against!.name,
                          colour: Brand.accentTeal,
                          axes: widget.against!.axes,
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  _CompareBar(
                    club: c,
                    others: widget.others,
                    against: widget.against,
                    onPick: widget.onCompare,
                  ),
                  const SizedBox(height: 8),
                  DnaBars(axes: c.axes),
                  if (c.fixtures.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    _Fixtures(fixtures: c.fixtures, form: c.form),
                  ],
                  if (c.keyPlayers.players.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    _KeyPlayers(key_: c.keyPlayers),
                  ],
                  if (c.insights.length > 1) const SizedBox(height: 6),
                  for (final insight in c.insights.skip(1))
                    Padding(
                      padding: const EdgeInsets.only(top: 3),
                      child: Text(
                        '${dnaMark(insight.kind)}  ${insight.text}',
                        style: TextStyle(
                          color: dnaColour(insight.kind),
                          fontSize: 11.5,
                          height: 1.4,
                        ),
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// A letter in a box — ⭐ the grade FPL managers already speak in, not a number they would have to learn.
class _Grade extends StatelessWidget {
  const _Grade({required this.grade});

  final String grade;

  @override
  Widget build(BuildContext context) => Container(
    width: 34,
    height: 30,
    alignment: Alignment.center,
    decoration: BoxDecoration(
      color: switch (grade) {
        'A+' || 'A' => Brand.good,
        'B' => Brand.purple,
        'C' => Brand.warn,
        _ => Brand.bad,
      },
      borderRadius: BorderRadius.circular(Brand.radiusSm),
    ),
    child: Text(
      grade,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 13,
        fontWeight: FontWeight.w800,
      ),
    ),
  );
}

/// Where the club is going, and how it has been going (ADR-251).
///
/// ⭐ Tinted by difficulty, because the number 4 means nothing until it is a colour — and the run is the
/// thing a manager is actually buying when he buys a player from this club.
class _Fixtures extends StatelessWidget {
  const _Fixtures({required this.fixtures, required this.form});

  final List<Fixture> fixtures;
  final List<({int gameweek, String result})> form;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Text(
        'NEXT SIX',
        style: TextStyle(
          color: Colors.white38,
          fontSize: 9.5,
          letterSpacing: 1,
        ),
      ),
      const SizedBox(height: 4),
      Row(
        children: [
          for (final f in fixtures)
            Expanded(
              child: Container(
                margin: const EdgeInsets.only(right: 3),
                padding: const EdgeInsets.symmetric(vertical: 4),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: _tint(f.difficulty),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Column(
                  children: [
                    Text(
                      // ⚠️ Upper case home, lower case away — the convention the last-five boxes already
                      // use, so a reader who has learned one has learned the other.
                      f.venue == 'H'
                          ? f.opponent.toUpperCase()
                          : f.opponent.toLowerCase(),
                      maxLines: 1,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 9.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      'GW${f.gameweek ?? '—'}',
                      style: const TextStyle(
                        color: Colors.white54,
                        fontSize: 7.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
      if (form.isNotEmpty) ...[
        const SizedBox(height: 6),
        Row(
          children: [
            const Text(
              'FORM',
              style: TextStyle(
                color: Colors.white38,
                fontSize: 9.5,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(width: 7),
            for (final r in form)
              Container(
                width: 17,
                height: 17,
                margin: const EdgeInsets.only(right: 3),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: switch (r.result) {
                    'W' => Brand.good,
                    'D' => Colors.white24,
                    _ => Brand.bad,
                  },
                  shape: BoxShape.circle,
                ),
                child: Text(
                  r.result,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
          ],
        ),
      ],
    ],
  );

  /// ⚠️ Difficulty 1–5, and **null is neutral** rather than easy: an unknown fixture is not a good one.
  static Color _tint(int? difficulty) => switch (difficulty) {
    1 || 2 => Brand.good.withValues(alpha: 0.55),
    3 => Colors.white10,
    4 => Brand.warn.withValues(alpha: 0.45),
    5 => Brand.bad.withValues(alpha: 0.55),
    _ => Colors.white10,
  };
}

/// Who to buy from this club (ADR-251).
///
/// ⚠️⚠️ **The season is named when it is not this one.** The ranking needs ~900 minutes, so until about
/// GW10 this is *last* season's table (ADR-126) — ⭐ *a table from a different season that does not say so
/// is the most quietly wrong thing on a page.*
class _KeyPlayers extends StatelessWidget {
  const _KeyPlayers({required this.key_});

  final KeyPlayers key_;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        key_.season == null ? 'WORTH OWNING' : 'WORTH OWNING · ${key_.season}',
        style: const TextStyle(
          color: Colors.white38,
          fontSize: 9.5,
          letterSpacing: 1,
        ),
      ),
      if (key_.season != null)
        const Padding(
          padding: EdgeInsets.only(top: 2, bottom: 2),
          child: Text(
            'Ranking needs ~900 minutes, so this season’s table fills from about GW10.',
            style: TextStyle(color: Colors.white24, fontSize: 10, height: 1.35),
          ),
        ),
      const SizedBox(height: 3),
      for (final p in key_.players)
        Padding(
          padding: const EdgeInsets.only(top: 3),
          child: Row(
            children: [
              SizedBox(
                width: 34,
                child: Text(
                  p.position,
                  style: const TextStyle(color: Colors.white38, fontSize: 10),
                ),
              ),
              Expanded(
                child: Text(
                  p.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
              ),
              _Stat(label: 'xGI', value: p.xgi90.toStringAsFixed(2)),
              _Stat(label: 'pts', value: p.pts90.toStringAsFixed(1)),
              _Stat(label: 'own', value: '${p.owned.toStringAsFixed(1)}%'),
            ],
          ),
        ),
    ],
  );
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: 52,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          value,
          style: const TextStyle(color: Colors.white70, fontSize: 11),
        ),
        Text(
          label,
          style: const TextStyle(color: Colors.white24, fontSize: 7.5),
        ),
      ],
    ),
  );
}

/// Compare this club with another — ⭐ **no new endpoint**: all twenty arrived in the first fetch, so the
/// comparison is a choice rather than a request (ADR-252).
class _CompareBar extends StatelessWidget {
  const _CompareBar({
    required this.club,
    required this.others,
    required this.against,
    required this.onPick,
  });

  final ClubDna club;
  final List<ClubDna> others;
  final ClubDna? against;
  final void Function(ClubDna?) onPick;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(
        child: Text(
          against == null
              ? 'Compare with…'
              : '${club.name} vs ${against!.name}',
          style: const TextStyle(color: Colors.white54, fontSize: 11.5),
        ),
      ),
      if (against != null)
        TextButton(
          onPressed: () => onPick(null),
          style: TextButton.styleFrom(
            foregroundColor: Colors.white38,
            padding: const EdgeInsets.symmetric(horizontal: 8),
            minimumSize: const Size(0, 28),
          ),
          child: const Text('Clear', style: TextStyle(fontSize: 11.5)),
        ),
      TextButton(
        onPressed: () async {
          final picked = await showModalBottomSheet<ClubDna>(
            context: context,
            backgroundColor: Brand.ink,
            isScrollControlled: true,
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
            ),
            builder: (sheet) => SafeArea(
              child: ListView(
                shrinkWrap: true,
                children: [
                  const Padding(
                    padding: EdgeInsets.fromLTRB(20, 16, 20, 6),
                    child: Text(
                      'Compare with',
                      style: TextStyle(color: Colors.white, fontSize: 14.5),
                    ),
                  ),
                  for (final other in others)
                    ListTile(
                      dense: true,
                      // ⭐ The grade travels into the picker: choosing who to compare against is itself a
                      // judgement, and a bare list of twenty names gives a reader nothing to make it with.
                      leading: GradeRing(
                        grade: other.grade,
                        score: other.score,
                        size: 34,
                      ),
                      title: Text(
                        other.name,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13.5,
                        ),
                      ),
                      onTap: () => Navigator.of(sheet).pop(other),
                    ),
                ],
              ),
            ),
          );
          if (picked != null) onPick(picked);
        },
        style: TextButton.styleFrom(
          backgroundColor: Brand.purple,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          minimumSize: const Size(0, 30),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(Brand.radiusSm),
          ),
        ),
        child: const Text('Pick', style: TextStyle(fontSize: 11.5)),
      ),
    ],
  );
}
