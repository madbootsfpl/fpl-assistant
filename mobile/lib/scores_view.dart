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
import 'package:url_launcher/url_launcher.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class ScoresView extends StatefulWidget {
  const ScoresView({
    required this.client,
    this.playerIds = const [],
    this.managerId = 0,
    super.key,
  });

  final ServiceClient client;

  /// The manager's squad, for the `yours` line.
  ///
  /// ⭐ Optional: the board draws without it. ⚠️ *A screen that refuses to show the scores until a squad
  /// has loaded is a screen that is blank at the moment someone opens it to check a score.*
  final List<int> playerIds;

  /// ⚠️⚠️ **Required for a week already played.** [playerIds] is the squad held *now*; a past gameweek was
  /// played by a different one, and joining one to the other invents a past — ⭐ *the owner saw Calafiori
  /// and Haaland credited with points in a week he held Gabriel and Calvert-Lewin.*
  final int managerId;

  @override
  State<ScoresView> createState() => _ScoresViewState();
}

class _ScoresViewState extends State<ScoresView> {
  late Future<GameweekScores> _future = _load();

  Future<GameweekScores> _load() => widget.client.gameweekScores(
    playerIds: widget.playerIds,
    managerId: widget.managerId,
  );

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
            for (final m in week.matches) _MatchCard(match: m, week: week),
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
  const _MatchCard({required this.match, required this.week});

  final MatchScore match;
  final GameweekScores week;

  @override
  Widget build(BuildContext context) {
    final mine = match.yours;
    final home = [
      for (final a in mine)
        if (a.player?.team == match.home) a,
    ];
    final away = [
      for (final a in mine)
        if (a.player?.team == match.away) a,
    ];
    final points = mine.fold<int>(0, (sum, a) => sum + a.points);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: Brand.darkPanel,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _Side(
                  club: week.club(match.home),
                  appearances: home,
                  alignEnd: false,
                ),
              ),
              _Scoreline(match: match),
              Expanded(
                child: _Side(
                  club: week.club(match.away),
                  appearances: away,
                  alignEnd: true,
                ),
              ),
            ],
          ),
          // ⚠️⚠️ **Nothing is said twice.** The first version listed your players under the clubs and
          // again in a "Your fantasy impact" row — ⭐ *the same names, no new fact, and the repetition is
          // what pushed every name into an ellipsis.* The names live upstairs; only the total is here.
          if (mine.isNotEmpty || match.highlights != null) ...[
            const SizedBox(height: 10),
            const Divider(height: 1, color: Color(0x14FFFFFF)),
            const SizedBox(height: 8),
            // ⚠️⚠️ **Each on its own line, after two attempts at sharing one.** Side by side, the total
            // overflowed the card by 27 px; constrained with `Flexible` the link was squeezed to 114 px
            // for 267 px of words. ⭐ *A row that needs a compromise from both children is a row with one
            // child too many* — and the label cannot shrink, because naming the destination is the point.
            if (mine.isNotEmpty)
              Align(
                alignment: Alignment.centerRight,
                child: _Total(points: points),
              ),
            if (match.highlights != null)
              Align(
                alignment: Alignment.centerLeft,
                child: _Highlights(url: match.highlights!),
              ),
          ],
        ],
      ),
    );
  }
}

/// One club of a fixture — crest, name, and your players' **names**, nothing more.
///
/// ⭐⭐ **No "Your player" tag.** Every name in this block is already yours, so the words said nothing and
/// cost the width that truncated the names themselves. ⚠️ *A label that is true of everything on screen
/// is not a label.*
class _Side extends StatelessWidget {
  const _Side({
    required this.club,
    required this.appearances,
    required this.alignEnd,
  });

  final Club club;
  final List<MatchAppearance> appearances;
  final bool alignEnd;

  /// `João Pedro ⚽⚽ · Raya` — goals as the one event compact enough to earn its place.
  String get _names => [
    for (final a in appearances)
      '${a.player?.name ?? 'Your player'}${'⚽' * a.goals}',
  ].join(' · ');

  @override
  Widget build(BuildContext context) {
    final crest = club.badge.isEmpty
        ? const SizedBox(width: 24, height: 24)
        : Image.network(
            club.badge,
            width: 24,
            height: 24,
            // ⚠️ A crest that fails to load leaves a hole, not an exception.
            errorBuilder: (_, _, _) => const SizedBox(width: 24, height: 24),
          );
    final text = Column(
      crossAxisAlignment: alignEnd
          ? CrossAxisAlignment.end
          : CrossAxisAlignment.start,
      children: [
        Text(
          club.name,
          textAlign: alignEnd ? TextAlign.right : TextAlign.left,
          style: const TextStyle(
            color: Brand.darkText,
            fontSize: 14.5,
            fontWeight: FontWeight.w600,
          ),
        ),
        if (appearances.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 2),
            // ⭐ Wraps rather than truncates: three names on one side is normal, and an ellipsis there
            // hides the very thing the card is for.
            child: Text(
              _names,
              textAlign: alignEnd ? TextAlign.right : TextAlign.left,
              style: const TextStyle(color: Brand.darkMuted, fontSize: 11.5),
            ),
          ),
      ],
    );
    final children = alignEnd
        ? [Flexible(child: text), const SizedBox(width: 8), crest]
        : [crest, const SizedBox(width: 8), Flexible(child: text)];
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: alignEnd
          ? MainAxisAlignment.end
          : MainAxisAlignment.start,
      children: children,
    );
  }
}

/// What the match was worth to you. ⭐ One number, because the names are already above it.
/// A link to the club's own highlights video (ADR-347).
///
/// ⚠️⚠️ **It says where it goes.** `test_help_link.py` exists in this repo because *tapping a row and
/// landing in another app is a surprise unless it was announced* — so the label names YouTube rather than
/// saying "Highlights" and hoping.
///
/// ⭐ Drawn only when a link exists. Most matches have none for a few hours after full time, and a greyed
/// button that never becomes available is worse than no button.
class _Highlights extends StatelessWidget {
  const _Highlights({required this.url});

  final String url;

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: () async {
      final ok = await launchUrl(
        Uri.parse(url),
        mode: LaunchMode.externalApplication,
      ).catchError((_) => false);
      if (ok || !context.mounted) return;
      // ⚠️ Reports a failure rather than doing nothing — ⭐ *a tap that silently does nothing teaches the
      // reader the app is broken, and they are right.*
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Could not open the video')));
    },
    borderRadius: BorderRadius.circular(8),
    child: const Padding(
      padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.play_circle_outline, size: 15, color: Brand.madOnDark),
          SizedBox(width: 5),
          Text(
            'Highlights on YouTube',
            style: TextStyle(color: Brand.madOnDark, fontSize: 11.5),
          ),
        ],
      ),
    ),
  );
}

class _Total extends StatelessWidget {
  const _Total({required this.points});

  final int points;

  @override
  Widget build(BuildContext context) => Row(
    // ⚠️⚠️ **`min`, because this Row now lives inside another Row.** Without it this one expands to fill
    // and overflows the card by 27 px beside the highlights link — ⭐ *a widget that was fine as a
    // Column's only child is not automatically fine as a Row's second one.*
    mainAxisSize: MainAxisSize.min,
    mainAxisAlignment: MainAxisAlignment.end,
    crossAxisAlignment: CrossAxisAlignment.baseline,
    textBaseline: TextBaseline.alphabetic,
    children: [
      Text(
        // ⚠️ `pt` at one. "1 pts" is the kind of thing a reader notices and nobody fixes.
        '$points ${points == 1 ? 'pt' : 'pts'}',
        style: const TextStyle(
          color: Color(0xFF6FD79A),
          fontSize: 15.5,
          fontWeight: FontWeight.w800,
          fontFeatures: [FontFeature.tabularFigures()],
        ),
      ),
      const SizedBox(width: 5),
      // ⭐ "this match", never "gameweek total": `player_history` is keyed by fixture, so it was earned
      // here — the mock-up this came from footnoted the opposite because its source could not say so.
      const Text(
        'this match',
        style: TextStyle(color: Colors.white38, fontSize: 11),
      ),
    ],
  );
}

class _Scoreline extends StatelessWidget {
  const _Scoreline({required this.match});

  final MatchScore match;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 10),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (!match.started || !match.hasScore)
          Text(
            _kickoff(match.kickoffTime) ?? 'v',
            style: const TextStyle(color: Colors.white38, fontSize: 13),
          )
        else
          Text(
            '${match.homeScore} – ${match.awayScore}',
            style: const TextStyle(
              color: Brand.darkText,
              fontSize: 19,
              fontWeight: FontWeight.w800,
              fontFeatures: [FontFeature.tabularFigures()],
            ),
          ),
        if (match.status.isNotEmpty)
          Text(
            match.status,
            style: TextStyle(
              // ⭐ A match still running is the one thing on this card worth a colour.
              color: match.finished ? Colors.white38 : const Color(0xFFE05A4E),
              fontSize: 10.5,
            ),
          ),
      ],
    ),
  );

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
