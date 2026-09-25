/// Swiping through the season on My Team (ADR-298).
///
/// ⭐⭐ **Backwards is a rendering job; forwards is a claim about the future**, and the two are drawn
/// differently on purpose. A past week shows what *happened* — FPL's own points, the goals, the cards,
/// who came on. A future week shows what is *projected*, and only as far as the model can stand behind.
///
/// ⚠️⚠️ **Forward stops at +5, and the last page says why** — ⭐ *a boundary with no explanation reads
/// as a bug, and the reason is the most honest thing on the screen.*
library;

import 'package:flutter/material.dart';

import 'api/models.dart';
import 'api/client.dart';
import 'brand.dart';
import 'mugshot.dart';
import 'pitch.dart';

/// How far forward the swipe goes (ADR-298).
///
/// ⚠️ Not a hedge picked to sound cautious: **five is already the answer elsewhere** — the Lab's wildcard
/// and fresh-season modes plan over five, Players ranks on *"xP over 5 GW"*. ⭐ *A new limit that
/// disagrees with the limits already in the product teaches the reader that limits are arbitrary.*
const int kForwardWeeks = 5;

/// One played gameweek, drawn as a list of what each player did.
class PastGameweek extends StatelessWidget {
  const PastGameweek({required this.result, super.key});

  final GameweekResult result;

  @override
  Widget build(BuildContext context) {
    if (!result.played) {
      // ⭐ Named here as well. *"This gameweek has not been played yet"* with no gameweek on it is the
      // same omission in a shorter sentence.
      return _NotYet(gameweek: result.gameweek);
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 20),
      children: [
        // ⚠️⚠️⚠️ **Found on a device, not by a test.** Every number on this page was right and the page
        // never said which week they belonged to — you swiped four times and had no way back to knowing
        // where you were. ⭐ *A screen whose whole purpose is "which week is this?" has to answer it.*
        //
        // ⭐ Said in the same shape the live pitch and the forward pages use — `GW5 · final` against
        // `GW9 · projected` — so the three page types read as one screen rather than three.
        _WeekLine(gameweek: result.gameweek, label: 'final'),
        _Summary(summary: result.summary),
        const SizedBox(height: 10),
        for (final player in result.xi) _PlayerRow(entry: player),
        const Padding(
          padding: EdgeInsets.fromLTRB(2, 16, 2, 6),
          child: Text(
            'BENCH',
            style: TextStyle(
              color: Colors.white38,
              fontSize: 9.5,
              letterSpacing: 2,
            ),
          ),
        ),
        for (final player in result.bench) _PlayerRow(entry: player),
      ],
    );
  }
}

/// Which week you are looking at — ⭐ the one thing a swipe has to keep answering.
class _WeekLine extends StatelessWidget {
  const _WeekLine({required this.gameweek, required this.label});

  final int? gameweek;
  final String label;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(2, 0, 2, 8),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.baseline,
      textBaseline: TextBaseline.alphabetic,
      children: [
        Text(
          'GW${gameweek ?? '—'}',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 15,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(color: Colors.white54, fontSize: 11),
        ),
      ],
    ),
  );
}

/// ⭐ The week's own numbers, as FPL settled them — *recomputing a settled fact is offering a second
/// opinion on it.*
class _Summary extends StatelessWidget {
  const _Summary({required this.summary});

  final GameweekSummary summary;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.fromLTRB(14, 12, 14, 13),
    decoration: BoxDecoration(
      color: Colors.white10,
      borderRadius: BorderRadius.circular(Brand.radiusMd),
    ),
    child: Row(
      children: [
        _Figure(value: '${summary.points ?? '—'}', label: 'Points'),
        _Figure(
          value: summary.overallRank == null
              ? '—'
              : _grouped(summary.overallRank!),
          label: 'Overall rank',
        ),
        _Figure(value: '${summary.benchPoints ?? '—'}', label: 'On the bench'),
        // ⚠️ Only when it cost something. *A row of zeroes is a row nobody reads.*
        if ((summary.hit ?? 0) > 0)
          _Figure(value: '−${summary.hit}', label: 'Hit', warn: true),
        if (summary.chip != null)
          _Figure(
            value: _chipNames[summary.chip] ?? summary.chip!,
            label: 'Chip',
          ),
      ],
    ),
  );
}

const Map<String, String> _chipNames = {
  'bboost': 'Bench Boost',
  '3xc': 'Triple Captain',
  'freehit': 'Free Hit',
  'wildcard': 'Wildcard',
  'manager': 'Assistant',
};

class _Figure extends StatelessWidget {
  const _Figure({required this.value, required this.label, this.warn = false});

  final String value;
  final String label;
  final bool warn;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FittedBox(
          fit: BoxFit.scaleDown,
          alignment: Alignment.centerLeft,
          child: Text(
            value,
            style: TextStyle(
              color: warn ? Brand.warn : Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        Text(
          label,
          style: const TextStyle(color: Colors.white38, fontSize: 10.5),
        ),
      ],
    ),
  );
}

/// One player's week.
class _PlayerRow extends StatelessWidget {
  const _PlayerRow({required this.entry});

  final GameweekPlayer entry;

  @override
  Widget build(BuildContext context) {
    final p = entry.player;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Mugshot(url: '', name: p.name, size: 26),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        p.name,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13.5,
                        ),
                      ),
                    ),
                    if (entry.isCaptain) const _Band(letter: 'C'),
                    if (entry.isViceCaptain) const _Band(letter: 'V'),
                  ],
                ),
                _Events(entry: entry),
              ],
            ),
          ),
          // ⚠️⚠️ **A blank gameweek is not a zero** — ⭐ *a zero that means "he did not play" must not
          // draw like a zero that means "he played badly."*
          Text(
            entry.didPlay ? '${entry.points}' : '—',
            style: TextStyle(
              color: entry.didPlay ? Colors.white : Colors.white24,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _Band extends StatelessWidget {
  const _Band({required this.letter});

  final String letter;

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(left: 6),
    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
    decoration: BoxDecoration(
      color: Brand.purple,
      borderRadius: BorderRadius.circular(Brand.radiusPill),
    ),
    child: Text(
      letter,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 9,
        fontWeight: FontWeight.w700,
      ),
    ),
  );
}

/// What actually happened, in glyphs — ⭐ *the row above says how many points; this says what for.*
class _Events extends StatelessWidget {
  const _Events({required this.entry});

  final GameweekPlayer entry;

  @override
  Widget build(BuildContext context) {
    final parts = <String>[
      if (entry.goals > 0) '⚽ ${entry.goals}',
      if (entry.assists > 0) '🅰 ${entry.assists}',
      if (entry.cleanSheet) '🛡',
      if (entry.saves > 0) '🧤 ${entry.saves}',
      if (entry.bonus > 0) '+${entry.bonus} bonus',
      // ⭐ The field the owner asked for by name.
      if (entry.yellowCards > 0)
        '🟨${entry.yellowCards > 1 ? ' ${entry.yellowCards}' : ''}',
      if (entry.redCards > 0) '🟥',
      // ⚠️ What the game did, not what was chosen — the bench says the choice.
      if (entry.cameOn) 'came on',
      if (entry.wentOff) 'auto-subbed',
      if (!entry.didPlay) 'did not play',
    ];
    if (parts.isEmpty) {
      return Text(
        '${entry.minutes} mins',
        style: const TextStyle(color: Colors.white38, fontSize: 11),
      );
    }
    return Text(
      parts.join('  ·  '),
      style: const TextStyle(color: Colors.white54, fontSize: 11),
    );
  }
}

/// A gameweek FPL has not published.
class _NotYet extends StatelessWidget {
  const _NotYet({this.gameweek});

  final int? gameweek;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(12, 8, 12, 20),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _WeekLine(gameweek: gameweek, label: 'not played yet'),
        const SizedBox(height: 40),
        const Center(
          child: Text(
            'This gameweek has not been played yet.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white38, height: 1.5),
          ),
        ),
      ],
    ),
  );
}

/// The page past the last forward week — ⭐⭐ **it says why it stops.**
///
/// ⚠️ *A boundary with no explanation reads as a bug*, and the reason is worth more than the page would
/// have been: beyond five gameweeks fixtures move and form is noise, and every other screen in this app
/// carries *"confidence is a heuristic from the signals, not a probability."*
class ForwardEdge extends StatelessWidget {
  const ForwardEdge({super.key});

  @override
  Widget build(BuildContext context) => const Padding(
    padding: EdgeInsets.all(26),
    child: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.trending_flat, color: Colors.white24, size: 30),
          SizedBox(height: 14),
          Text(
            'Five gameweeks is as far as we will guess.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white70,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: 10),
          Text(
            'Beyond that the fixtures still move and form stops predicting '
            'anything — a number that far out would look confident and mean '
            'very little.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white38, fontSize: 12, height: 1.5),
          ),
        ],
      ),
    ),
  );
}

String _grouped(int n) {
  final s = '$n';
  final out = StringBuffer();
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) out.write(',');
    out.write(s[i]);
  }
  return out.toString();
}

/// My Team as a walk through the season (ADR-298).
///
/// ⭐⭐⭐ **One page per gameweek, with the live pitch in the middle.** Backwards is history — FPL's own
/// points for every week already played. Forwards is a projection, and it stops at [kForwardWeeks].
///
/// ⚠️⚠️ **The index arithmetic is the whole risk in this widget, so it is one function and it is tested.**
/// `page → gameweek` is `page + 1`, which makes GW1 page 0 and puts the live pitch at `current - 1`.
/// ⭐ *An off-by-one here does not crash — it silently shows the wrong week's team, which is the one bug
/// class this screen cannot survive.*
class SeasonPages extends StatefulWidget {
  const SeasonPages({
    required this.team,
    required this.client,
    required this.mode,
    required this.onMode,
    required this.onTapPlayer,
    this.footer,
    super.key,
  });

  final MyTeam team;
  final ServiceClient client;
  final PitchMode mode;
  final ValueChanged<PitchMode> onMode;
  final void Function(PlayerSummary) onTapPlayer;

  /// ⚠️ Drawn on the **live** page only. Applying a plan is an act on the squad you own today; offering
  /// the button under GW3's result would be offering to change the past.
  final Widget? footer;

  /// How many pages a season with `current` as the live gameweek has.
  ///
  /// ⭐ Every played week, the live one, [kForwardWeeks] ahead, and one page that explains the edge.
  static int pageCount(int current) => current + kForwardWeeks + 1;

  /// The live page's index — ⭐ the page the walk opens on.
  static int livePage(int current) => current - 1;

  @override
  State<SeasonPages> createState() => _SeasonPagesState();
}

class _SeasonPagesState extends State<SeasonPages> {
  late final int _current = widget.team.gameweek ?? 1;
  late final PageController _pages = PageController(
    initialPage: SeasonPages.livePage(_current),
  );

  /// ⚠️⚠️ **Fetched per page, cached by the client, never prefetched.** A season in October is nine past
  /// weeks; loading them on arrival would put nine round trips in front of a screen whose first job is to
  /// draw today's team. ⭐ *A swipe is a request — the user asking is the cheapest possible trigger.*
  final Map<int, Future<GameweekResult>> _results = {};

  @override
  void dispose() {
    _pages.dispose();
    super.dispose();
  }

  Future<GameweekResult> _result(int gameweek) => _results.putIfAbsent(
    gameweek,
    () => widget.client.gameweekResult(widget.team.managerId, gameweek),
  );

  @override
  Widget build(BuildContext context) => PageView.builder(
    controller: _pages,
    itemCount: SeasonPages.pageCount(_current),
    itemBuilder: (context, page) {
      final gameweek = page + 1;
      if (gameweek < _current) return _Past(future: _result(gameweek));
      if (gameweek == _current) {
        return PitchView(
          team: widget.team,
          mode: widget.mode,
          onMode: widget.onMode,
          onTapPlayer: widget.onTapPlayer,
          footer: widget.footer,
        );
      }
      if (gameweek <= _current + kForwardWeeks) {
        // ⭐ The same squad, a different week — ⚠️ *not a predicted transfer*. What the engine can say is
        // what these fifteen are projected to do; who you will own in four weeks is not a projection, it
        // is a guess about your own future decisions.
        return PitchView(
          team: widget.team,
          mode: widget.mode,
          onMode: widget.onMode,
          onTapPlayer: widget.onTapPlayer,
          gameweek: gameweek,
        );
      }
      return const ForwardEdge();
    },
  );
}

/// A past page, while its week is in the air.
class _Past extends StatelessWidget {
  const _Past({required this.future});

  final Future<GameweekResult> future;

  @override
  Widget build(BuildContext context) => FutureBuilder<GameweekResult>(
    future: future,
    builder: (context, snap) {
      if (snap.hasError) {
        // ⚠️ Named, not swallowed. A page that silently shows nothing is indistinguishable from a
        // gameweek where nothing happened.
        return Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: Text(
              'Could not load this gameweek.\n${snap.error}',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white38, height: 1.5),
            ),
          ),
        );
      }
      if (!snap.hasData) {
        return const Center(
          child: SizedBox(
            width: 22,
            height: 22,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        );
      }
      return PastGameweek(result: snap.data!);
    },
  );
}
