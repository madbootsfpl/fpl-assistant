/// The scores — every match of a gameweek, and your own players in them (ADR-346).
///
/// ⭐⭐ **The `yours` line is the whole reason this is not a livescore app.** A scoreline is a commodity;
/// *"your João Pedro scored twice, 13 pts"* is not, and it is the only version of this screen worth
/// building.
///
/// ⚠️⚠️ **Two states that look identical and are not**, both handled here rather than left to the reader:
///
/// * `0-0` versus **not kicked off** — a goalless draw has a score, an unplayed match has none. Decided by
///   `started`, never by the number.
/// * an empty `yours` versus **we do not know yet** — scores publish before player history does, so after
///   full time the score is known and nobody's week is. `yoursKnown` is what tells them apart, and
///   ⭐ *an empty list on its own claims the wrong one.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class ScoresView extends StatefulWidget {
  const ScoresView({
    required this.client,
    this.playerIds = const [],
    super.key,
  });

  final ServiceClient client;

  /// The manager's squad, for the `yours` line.
  ///
  /// ⭐ Optional: the board draws without it. ⚠️ *A screen that refuses to show the scores until a squad
  /// has loaded is a screen that is blank at the moment someone opens it to check a score.*
  final List<int> playerIds;

  @override
  State<ScoresView> createState() => _ScoresViewState();
}

class _ScoresViewState extends State<ScoresView> {
  late Future<GameweekScores> _future = _load();

  Future<GameweekScores> _load() =>
      widget.client.gameweekScores(playerIds: widget.playerIds);

  @override
  Widget build(BuildContext context) => FutureBuilder<GameweekScores>(
    future: _future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SelectableText(
                friendlyError(snapshot.error),
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => setState(() => _future = _load()),
                child: const Text('Try again'),
              ),
            ],
          ),
        );
      }

      final week = snapshot.data!;
      if (week.gameweek == null || week.matches.isEmpty) {
        // ⭐ A season that has not started is a fact, not a failure.
        return const Center(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text(
              'No matches yet.',
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
          ),
        );
      }

      return RefreshIndicator(
        onRefresh: () async {
          final next = _load();
          setState(() => _future = next);
          await next;
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
          children: [
            _Heading(week: week),
            for (final m in week.matches)
              _MatchCard(match: m, yoursKnown: week.yoursKnown),
          ],
        ),
      );
    },
  );
}

class _Heading extends StatelessWidget {
  const _Heading({required this.week});

  final GameweekScores week;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(2, 2, 2, 10),
    child: Row(
      children: [
        Text(
          'Gameweek ${week.gameweek}',
          style: const TextStyle(
            color: Brand.darkText,
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(width: 8),
        // ⭐ Says it is live rather than implying it. ⚠️ *A screen that refreshes silently leaves the
        // reader unsure whether a 0-0 is the current score or a stale one.*
        if (week.live) const _Chip(text: 'LIVE', colour: Color(0xFFE05A4E)),
        const Spacer(),
        // ⚠️⚠️ The honest state when scores have landed and history has not — see the library note.
        // ⭐ `Flexible` + ellipsis rather than a bare `Text`: with the LIVE chip beside it this row
        // **overflowed at 472 px** — caught by a widget test, and it would have been a yellow-and-black
        // stripe on a narrow phone in front of a tester.
        if (!week.yoursKnown)
          const Flexible(
            child: Text(
              'your players not in yet',
              textAlign: TextAlign.right,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: Colors.white38, fontSize: 11),
            ),
          ),
      ],
    ),
  );
}

class _MatchCard extends StatelessWidget {
  const _MatchCard({required this.match, required this.yoursKnown});

  final MatchScore match;
  final bool yoursKnown;

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 8),
    padding: const EdgeInsets.fromLTRB(14, 11, 14, 11),
    decoration: BoxDecoration(
      color: Brand.darkPanel,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                match.home,
                textAlign: TextAlign.right,
                style: const TextStyle(
                  color: Brand.darkText,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: _Scoreline(match: match),
            ),
            Expanded(
              child: Text(
                match.away,
                style: const TextStyle(
                  color: Brand.darkText,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        if (match.yours.isNotEmpty) ...[
          const SizedBox(height: 9),
          for (final a in match.yours) _YourLine(appearance: a),
        ] else if (yoursKnown && match.started) ...[
          const SizedBox(height: 7),
          const Text(
            'none of yours',
            style: TextStyle(color: Colors.white24, fontSize: 11),
          ),
        ],
      ],
    ),
  );
}

/// The score, or the kick-off time when there is not one yet.
///
/// ⚠️⚠️ **Never prints a zero for a match that has not started.** `0-0` and *"no score yet"* are opposite
/// facts, and `started` is the only field that distinguishes them.
class _Scoreline extends StatelessWidget {
  const _Scoreline({required this.match});

  final MatchScore match;

  @override
  Widget build(BuildContext context) {
    if (!match.started || !match.hasScore) {
      return Text(
        _kickoff(match.kickoffTime) ?? 'v',
        style: const TextStyle(color: Colors.white38, fontSize: 12.5),
      );
    }
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '${match.homeScore}–${match.awayScore}',
          style: const TextStyle(
            color: Brand.darkText,
            fontSize: 17,
            fontWeight: FontWeight.w800,
            fontFeatures: [FontFeature.tabularFigures()],
          ),
        ),
        if (!match.finished && match.minutes != null)
          Text(
            "${match.minutes}'",
            style: const TextStyle(color: Color(0xFFE05A4E), fontSize: 10.5),
          ),
      ],
    );
  }

  /// `2026-10-10T11:30:00Z` → `11:30`. ⚠️ Null rather than a guess when it cannot be read — ⭐ *a made-up
  /// kick-off time is worse than none, because a reader would plan around it.*
  static String? _kickoff(String? iso) {
    if (iso == null) return null;
    final at = DateTime.tryParse(iso)?.toLocal();
    if (at == null) return null;
    final h = at.hour.toString().padLeft(2, '0');
    final m = at.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }
}

class _YourLine extends StatelessWidget {
  const _YourLine({required this.appearance});

  final MatchAppearance appearance;

  @override
  Widget build(BuildContext context) {
    final name = appearance.player?.name ?? 'Your player';
    final bits = <String>[
      if (appearance.goals > 0)
        '${appearance.goals} goal${appearance.goals == 1 ? '' : 's'}',
      if (appearance.assists > 0)
        '${appearance.assists} assist${appearance.assists == 1 ? '' : 's'}',
      if (appearance.bonus > 0) '+${appearance.bonus} bonus',
      // ⭐ Minutes only when they are the story: a man who played the whole game needs no note, one who
      // came on for nine minutes does. ⚠️ *A line that states the unremarkable buries the remarkable.*
      if (appearance.minutes == 0)
        'did not play'
      else if (appearance.minutes < 60)
        "${appearance.minutes}'",
    ];
    return Padding(
      padding: const EdgeInsets.only(top: 3),
      child: Row(
        children: [
          Container(
            width: 3,
            height: 13,
            margin: const EdgeInsets.only(right: 8),
            decoration: BoxDecoration(
              color: Brand.madOnDark,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Expanded(
            child: Text(
              bits.isEmpty ? name : '$name — ${bits.join(', ')}',
              style: const TextStyle(color: Brand.darkMuted, fontSize: 12.5),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Text(
            '${appearance.points} pts',
            style: const TextStyle(
              color: Brand.darkText,
              fontSize: 12.5,
              fontWeight: FontWeight.w700,
              fontFeatures: [FontFeature.tabularFigures()],
            ),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.text, required this.colour});

  final String text;
  final Color colour;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
    decoration: BoxDecoration(
      color: colour.withValues(alpha: 0.18),
      borderRadius: BorderRadius.circular(99),
      border: Border.all(color: colour.withValues(alpha: 0.5)),
    ),
    child: Text(
      text,
      style: TextStyle(
        color: colour,
        fontSize: 10,
        fontWeight: FontWeight.w800,
        letterSpacing: 0.5,
      ),
    ),
  );
}
