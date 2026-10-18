/// The scores — every match of a gameweek, and your own players in them (ADR-346).
///
/// ⭐⭐ **The `yours` line is the whole reason this is not a livescore app.** A scoreline is a commodity;
/// *"your João Pedro scored twice, 13 pts"* is not, and it is the only version of this screen worth
/// building.
///
/// ⚠️⚠️ **Three pairs of states that look identical and are not**, all handled here rather than left to
/// the reader:
///
/// * `0-0` versus **not kicked off** — a goalless draw has a score, an unplayed match has none. Decided by
///   `started`, never by the number.
/// * an empty `yours` versus **we do not know yet** — scores publish before player history does, so after
///   full time the score is known and nobody's week is. `yoursKnown` is what tells them apart, and
///   ⭐ *an empty list on its own claims the wrong one.*
/// * **no highlights yet** versus **none there will ever be** — GW1–GW5 pre-date ADR-357, and the clubs'
///   fifteen-entry feeds had long moved on. ⚠️ *A silent gap reads as a bug*, so an old week says so.
///
/// ⭐ The week bar reaches back to GW1 and forward five (ADR-360): backwards shows the squad that
/// **actually** played it, forwards shows who of yours is involved. 📌 Five is not a new number —
/// `analyse`, `board`, `dead_slot` and `explain` all already default to a five-gameweek horizon.
library;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'event_icons.dart';

/// ⭐ How far past the current week the bar goes — the house horizon, not a new one (ADR-360).
/// ⚠️ Fixtures run to GW38, but *"which of your players are in it"* uses the squad held **today**, and
/// thirty weeks out that is a guess dressed as a fact.
const int kForwardWeeks = 5;

/// ⭐ Before this week the clubs' feeds had moved on before ADR-357 taught the pipeline to look, so no
/// amount of waiting produces a link.
const int kFirstWeekWithHighlights = 6;

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
  /// ⭐ `0` means *"you choose"* — the server takes the live week, else the last one played. The bar only
  /// takes over once the first answer has said which week that was.
  int _asked = 0;

  /// The week the server chose on its own. ⚠️⚠️ Remembered from the **first** answer only: re-anchoring
  /// on every load would let the forward limit walk itself one week at a time, five past wherever you
  /// happened to browse to.
  int? _anchor;

  late Future<GameweekScores> _future = _load();

  Future<GameweekScores> _load() => widget.client.gameweekScores(
    playerIds: widget.playerIds,
    managerId: widget.managerId,
    gameweek: _asked,
  );

  void _go(int week) => setState(() {
    _asked = week;
    _future = _load();
  });

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
      _anchor ??= week.gameweek;

      return RefreshIndicator(
        onRefresh: () async {
          final next = _load();
          setState(() => _future = next);
          await next;
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
          children: [
            _Heading(week: week, anchor: _anchor ?? week.gameweek!, onGo: _go),
            for (final m in week.matches)
              _MatchCard(key: ValueKey(m.fixture), match: m, week: week),
            if (week.gameweek! < kFirstWeekWithHighlights)
              const _NoHighlights(),
          ],
        ),
      );
    },
  );
}

/// `‹ Gameweek 7 ›`, the LIVE chip, and the honest note about `yours` (ADR-360).
class _Heading extends StatelessWidget {
  const _Heading({
    required this.week,
    required this.anchor,
    required this.onGo,
  });

  final GameweekScores week;
  final int anchor;
  final void Function(int) onGo;

  /// ⚠️ Clamped at 38 as well as at the horizon — ⭐ *the season ends before the horizon does.*
  int get _last => (anchor + kForwardWeeks).clamp(1, 38);

  @override
  Widget build(BuildContext context) {
    final gw = week.gameweek ?? 0;
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 2, 2, 10),
      child: Column(
        children: [
          Row(
            children: [
              IconButton(
                onPressed: gw > 1 ? () => onGo(gw - 1) : null,
                icon: const Icon(Icons.chevron_left, size: 22),
                color: Brand.madOnDark,
                disabledColor: Colors.white24,
                tooltip: 'Previous gameweek',
                visualDensity: VisualDensity.compact,
              ),
              Expanded(
                child: Text(
                  'Gameweek $gw',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Brand.darkText,
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              IconButton(
                onPressed: gw < _last ? () => onGo(gw + 1) : null,
                icon: const Icon(Icons.chevron_right, size: 22),
                color: Brand.madOnDark,
                disabledColor: Colors.white24,
                tooltip: 'Next gameweek',
                visualDensity: VisualDensity.compact,
              ),
            ],
          ),
          Row(
            children: [
              // ⭐ Says it is live rather than implying it. ⚠️ *A screen that refreshes silently leaves
              // the reader unsure whether a 0-0 is the current score or a stale one.*
              if (week.live)
                const _Chip(text: 'LIVE', colour: Color(0xFFE05A4E)),
              const Spacer(),
              // ⚠️⚠️ The honest state when scores have landed and history has not — see the library note.
              // ⭐ `Flexible` + ellipsis rather than a bare `Text`: with the LIVE chip beside it this row
              // **overflowed at 472 px**, caught by a widget test.
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
        ],
      ),
    );
  }
}

/// ⚠️ Said out loud, because a missing row reads as a bug (ADR-360).
class _NoHighlights extends StatelessWidget {
  const _NoHighlights();

  @override
  Widget build(BuildContext context) => const Padding(
    padding: EdgeInsets.fromLTRB(6, 8, 6, 0),
    child: Text(
      'No highlights this far back — the clubs’ feeds had moved on before we started matching them.',
      style: TextStyle(color: Colors.white38, fontSize: 11, height: 1.5),
    ),
  );
}

/// One match: a summary that always shows, and one dropdown holding the rest (ADR-360).
///
/// ⭐⭐ **Nothing appears in both halves.** The first rebuild of this screen put the same names in two
/// places and the owner's verdict was *"its duplicated and not well laid out"* — so the scorers live in
/// the summary and the dropdown holds only what the summary does not say.
class _MatchCard extends StatefulWidget {
  const _MatchCard({required this.match, required this.week, super.key});

  final MatchScore match;
  final GameweekScores week;

  @override
  State<_MatchCard> createState() => _MatchCardState();
}

class _MatchCardState extends State<_MatchCard> {
  bool _open = false;

  MatchScore get m => widget.match;
  GameweekScores get week => widget.week;

  /// ⭐ Nothing to open when nothing happened — ⚠️ *a chevron that reveals an empty box is a lie about
  /// there being more.*
  bool get _hasMore =>
      m.events.cards.isNotEmpty ||
      m.bonusRace.isNotEmpty ||
      m.highlights != null ||
      m.yours.any((y) => y.played);

  @override
  Widget build(BuildContext context) {
    final mine = <int>{
      for (final y in m.yours)
        if (y.player != null) y.player!.id,
    };
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Brand.darkPanel,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: _hasMore ? () => setState(() => _open = !_open) : null,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 6),
              child: Column(
                children: [
                  _Scoreline(match: m, week: week),
                  _Summary(match: m, week: week, mine: mine),
                  if (_hasMore)
                    Icon(
                      _open ? Icons.expand_less : Icons.expand_more,
                      size: 18,
                      color: _open ? Brand.madOnDark : Colors.white24,
                    ),
                ],
              ),
            ),
          ),
          if (_open)
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
              child: _Dropdown(match: m, week: week, mine: mine),
            ),
        ],
      ),
    );
  }
}

/// `BRE 1 – 2 LIV`, and the state underneath it.
class _Scoreline extends StatelessWidget {
  const _Scoreline({required this.match, required this.week});

  final MatchScore match;
  final GameweekScores week;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            match.home,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 13.5,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(width: 12),
          Text(
            // ⚠️⚠️ **A fixture with no score shows its kick-off, never `0 – 0`** (ADR-346).
            match.hasScore ? '${match.homeScore} – ${match.awayScore}' : 'v',
            style: const TextStyle(
              color: Brand.darkText,
              fontSize: 22,
              fontWeight: FontWeight.w800,
              fontFeatures: [FontFeature.tabularFigures()],
            ),
          ),
          const SizedBox(width: 12),
          Text(
            match.away,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 13.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
      const SizedBox(height: 3),
      Text(
        match.status.isNotEmpty
            ? match.status
            : (_kickoff(match.kickoffTime) ?? ''),
        style: TextStyle(
          // ⭐ A match still running is the one thing on this card worth a colour.
          color: match.started && !match.finished
              ? const Color(0xFFE05A4E)
              : Colors.white38,
          fontSize: 11,
        ),
      ),
    ],
  );

  /// `2026-10-10T11:30:00Z` → `Sat 11:30`, in the reader's own clock. ⚠️ Null rather than a guess when it
  /// cannot be read — ⭐ *a made-up kick-off time is worse than none, because a reader would plan around
  /// it.*
  static String? _kickoff(String? iso) {
    if (iso == null) return null;
    final at = DateTime.tryParse(iso)?.toLocal();
    if (at == null) return null;
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    final h = at.hour.toString().padLeft(2, '0');
    final m = at.minute.toString().padLeft(2, '0');
    return '${days[at.weekday - 1]} $h:$m';
  }
}

/// Scorers on top, assists beneath — **as two lists**, one row each (ADR-360).
///
/// ⚠️⚠️ **Never paired.** FPL publishes goals and assists and links them to nothing: Brentford's pairing
/// was forced, one goal and one assist, and Liverpool's was not — which of Wirtz and Barcola set up which
/// of Munoz and Isak is not in the data. ⭐⭐ *Pairing two sorted lists is the ADR-351 mistake.*
///
/// ⭐ The assists sit in their **own row** so both sides begin on the same line however many goals each
/// scored; a long list wraps inside its own half rather than pushing the other side down.
class _Summary extends StatelessWidget {
  const _Summary({required this.match, required this.week, required this.mine});

  final MatchScore match;
  final GameweekScores week;
  final Set<int> mine;

  List<EventEntry> _side(List<EventEntry> all, String short) => [
    for (final e in all)
      if (week.person(e.player)?.team == short) e,
  ];

  @override
  Widget build(BuildContext context) {
    final hg = _side(match.events.goals, match.home);
    final ag = _side(match.events.goals, match.away);
    final ha = _side(match.events.assists, match.home);
    final aa = _side(match.events.assists, match.away);
    final lining = [
      for (final y in match.yours)
        if (!y.played) y,
    ];

    if (hg.isEmpty &&
        ag.isEmpty &&
        ha.isEmpty &&
        aa.isEmpty &&
        lining.isEmpty) {
      return const SizedBox(height: 4);
    }
    return Padding(
      padding: const EdgeInsets.only(top: 9),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Divider(height: 1, color: Brand.darkBg),
          const SizedBox(height: 8),
          if (hg.isNotEmpty || ag.isNotEmpty)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: _Goals(entries: hg, week: week, mine: mine, end: true),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _Goals(
                    entries: ag,
                    week: week,
                    mine: mine,
                    end: false,
                  ),
                ),
              ],
            ),
          if (ha.isNotEmpty || aa.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 5),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: _Assists(
                      entries: ha,
                      week: week,
                      mine: mine,
                      end: true,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _Assists(
                      entries: aa,
                      week: week,
                      mine: mine,
                      end: false,
                    ),
                  ),
                ],
              ),
            ),
          // ⭐ A week not yet played has no events at all. What it has is who of yours is involved —
          // ⚠️ *involved, never "will start": FPL has not published a lineup and neither have we.*
          if (lining.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                'Yours: ${lining.map((y) => y.player?.name ?? '—').join(' · ')}',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Brand.madOnDark, fontSize: 11.5),
              ),
            ),
        ],
      ),
    );
  }
}

/// A column of scorers, one football **drawn** per goal.
///
/// ⭐⭐ **One mark per goal, not a number beside one mark** — the rule `result_pitch` already settled:
/// two footballs read as *two goals* before anything is parsed, where `⚽2` has to be read.
/// ⚠️ And drawn rather than typed, because Android substitutes its own emoji (see `event_icons.dart`).
class _Goals extends StatelessWidget {
  const _Goals({
    required this.entries,
    required this.week,
    required this.mine,
    required this.end,
  });

  final List<EventEntry> entries;
  final GameweekScores week;
  final Set<int> mine;
  final bool end;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: end ? CrossAxisAlignment.end : CrossAxisAlignment.start,
    children: [
      for (final e in entries)
        Padding(
          padding: const EdgeInsets.only(bottom: 3),
          child: Wrap(
            alignment: end ? WrapAlignment.end : WrapAlignment.start,
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 4,
            children: [
              if (mine.contains(e.player)) const _Mine(),
              Text(
                week.nameOf(e.player),
                style: const TextStyle(color: Colors.white, fontSize: 12.5),
              ),
              // ⚠️ Capped at three: a hat-trick is where the row runs out of width, and four of anything
              // is a number again anyway.
              for (var i = 0; i < e.count && i < 3; i++) const EventBall(),
            ],
          ),
        ),
    ],
  );
}

/// One side's assists, on one line, with the drawn boot.
class _Assists extends StatelessWidget {
  const _Assists({
    required this.entries,
    required this.week,
    required this.mine,
    required this.end,
  });

  final List<EventEntry> entries;
  final GameweekScores week;
  final Set<int> mine;
  final bool end;

  @override
  Widget build(BuildContext context) {
    if (entries.isEmpty) return const SizedBox.shrink();
    final names = <Widget>[
      for (final e in entries)
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 3,
          children: [
            if (mine.contains(e.player)) const _Mine(),
            Text(
              week.nameOf(e.player),
              style: const TextStyle(color: Colors.white60, fontSize: 11.5),
            ),
          ],
        ),
    ];
    return Wrap(
      alignment: end ? WrapAlignment.end : WrapAlignment.start,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 5,
      runSpacing: 2,
      // ⭐ The boot sits on the outer edge, mirroring the two columns.
      children: end
          ? [...names, const EventBoot()]
          : [const EventBoot(), ...names],
    );
  }
}

/// ⭐ The dot that marks one of yours. ⚠️ *A "your player" label was tried and removed* — it was true of
/// everything in its block and cost the width that truncated the names.
class _Mine extends StatelessWidget {
  const _Mine();

  @override
  Widget build(BuildContext context) => Container(
    width: 6,
    height: 6,
    decoration: const BoxDecoration(
      color: Brand.madOnDark,
      shape: BoxShape.circle,
    ),
  );
}

/// Everything the summary does not say: cards, your players, the bonus race, the video.
class _Dropdown extends StatelessWidget {
  const _Dropdown({
    required this.match,
    required this.week,
    required this.mine,
  });

  final MatchScore match;
  final GameweekScores week;
  final Set<int> mine;

  @override
  Widget build(BuildContext context) {
    final played = [
      for (final y in match.yours)
        if (y.played) y,
    ];
    final total = played.fold<int>(0, (sum, y) => sum + (y.points ?? 0));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (match.events.cards.isNotEmpty) ...[
          const _Label(text: 'CARDS'),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final c in match.events.cards)
                _CardChip(name: week.nameOf(c.player), red: c.isRed),
            ],
          ),
          const SizedBox(height: 12),
        ],
        if (played.isNotEmpty) ...[
          const _Label(text: 'YOUR PLAYERS', colour: Brand.madOnDark),
          for (final y in played) _YourLine(entry: y),
          const SizedBox(height: 6),
          const Divider(height: 1, color: Brand.darkBg),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'This match',
                style: TextStyle(color: Colors.white60, fontSize: 12.5),
              ),
              _Total(points: total),
            ],
          ),
          const SizedBox(height: 12),
        ],
        if (match.bonusRace.isNotEmpty) ...[
          const _Label(text: 'BONUS RACE', colour: Brand.bonus),
          for (final b in match.bonusRace)
            _BonusLine(entry: b, week: week, mine: mine),
          const SizedBox(height: 12),
        ],
        if (match.highlights != null) _Highlights(url: match.highlights!),
      ],
    );
  }
}

class _Label extends StatelessWidget {
  const _Label({required this.text, this.colour = Colors.white38});

  final String text;
  final Color colour;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(
      text,
      style: TextStyle(
        color: colour,
        fontSize: 10,
        fontWeight: FontWeight.w800,
        letterSpacing: 0.07,
      ),
    ),
  );
}

/// ⭐ Shape **and** colour: red against yellow is the one pair most likely to fail the readers who most
/// need to tell them apart, so the red chip carries a darker ground as well as a redder mark.
class _CardChip extends StatelessWidget {
  const _CardChip({required this.name, required this.red});

  final String name;
  final bool red;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(
      color: red
          ? const Color(0xFF3A1C24)
          : Brand.darkBg.withValues(alpha: 0.7),
      borderRadius: BorderRadius.circular(6),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 7,
          height: 10,
          decoration: BoxDecoration(
            color: red ? const Color(0xFFE04141) : Brand.yellow,
            borderRadius: BorderRadius.circular(1),
          ),
        ),
        const SizedBox(width: 5),
        Text(
          name,
          style: const TextStyle(color: Colors.white70, fontSize: 11.5),
        ),
      ],
    ),
  );
}

/// One of yours, what he did, and what it was worth.
class _YourLine extends StatelessWidget {
  const _YourLine({required this.entry});

  final MatchAppearance entry;

  /// ⭐ What he did, in words. ⚠️ *Never a points total worked out here* — FPL's own number is the one
  /// that has to match, and one this app computed would eventually disagree with it (ADR-346).
  String get _did {
    final bits = <String>[];
    final g = entry.goals ?? 0;
    final a = entry.assists ?? 0;
    final b = entry.bonus ?? 0;
    if (g > 0) bits.add('$g goal${g == 1 ? '' : 's'}');
    if (a > 0) bits.add('$a assist${a == 1 ? '' : 's'}');
    if (b > 0) bits.add('$b bonus');
    if (bits.isEmpty) bits.add('${entry.minutes ?? 0} min');
    return bits.join(' · ');
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 7),
    child: Row(
      children: [
        Expanded(
          child: Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: entry.player?.name ?? '—',
                  style: const TextStyle(color: Colors.white, fontSize: 12.5),
                ),
                TextSpan(
                  text: '  $_did',
                  style: const TextStyle(color: Colors.white38, fontSize: 11.5),
                ),
              ],
            ),
          ),
        ),
        Text(
          '${entry.points ?? 0}',
          style: const TextStyle(
            color: Color(0xFF6FD79A),
            fontSize: 13,
            fontWeight: FontWeight.w800,
            fontFeatures: [FontFeature.tabularFigures()],
          ),
        ),
      ],
    ),
  );
}

/// ⭐⭐ The bonus race — the one thing no livescore app carries. ⚠️ Ordered by **BPS**, because while the
/// award is provisional (ADR-356 measured ninety-six minutes) the bonus column is still empty and the
/// order is the whole story.
class _BonusLine extends StatelessWidget {
  const _BonusLine({
    required this.entry,
    required this.week,
    required this.mine,
  });

  final BonusEntry entry;
  final GameweekScores week;
  final Set<int> mine;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 7),
    child: Row(
      children: [
        SizedBox(
          width: 24,
          child: Text(
            // ⚠️ A dash, not `+0`: ⭐ *nought bonus and no bonus yet awarded are the same glyph and
            // different facts, and the dash claims neither.*
            entry.bonus > 0 ? '+${entry.bonus}' : '—',
            style: TextStyle(
              color: entry.bonus > 0 ? Brand.bonus : Colors.white24,
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        if (mine.contains(entry.player)) ...[
          const _Mine(),
          const SizedBox(width: 5),
        ],
        Expanded(
          child: Text(
            week.nameOf(entry.player),
            style: const TextStyle(color: Colors.white70, fontSize: 12.5),
          ),
        ),
        Text(
          '${entry.bps}',
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 11.5,
            fontFeatures: [FontFeature.tabularFigures()],
          ),
        ),
      ],
    ),
  );
}

class _Total extends StatelessWidget {
  const _Total({required this.points});

  final int points;

  @override
  Widget build(BuildContext context) => Text(
    // ⚠️ `pt` at one. "1 pts" is the kind of thing a reader notices and nobody fixes.
    '$points ${points == 1 ? 'pt' : 'pts'}',
    style: const TextStyle(
      color: Color(0xFF6FD79A),
      fontSize: 14,
      fontWeight: FontWeight.w800,
      fontFeatures: [FontFeature.tabularFigures()],
    ),
  );
}

/// A link to the club's own highlights video (ADR-347), with the still YouTube publishes for it.
///
/// ⚠️⚠️ **It says where it goes.** `test_help_link.py` exists in this repo because *tapping a row and
/// landing in another app is a surprise unless it was announced* — so the label names YouTube rather than
/// saying "Highlights" and hoping.
class _Highlights extends StatelessWidget {
  const _Highlights({required this.url});

  final String url;

  /// ⭐ The id out of the watch URL. ⚠️ *A thumbnail is only drawn when one can be addressed* — never
  /// guessed at from a URL shape this does not recognise.
  String? get _videoId {
    final v = Uri.tryParse(url)?.queryParameters['v'];
    return (v != null && v.isNotEmpty) ? v : null;
  }

  @override
  Widget build(BuildContext context) {
    final id = _videoId;
    return InkWell(
      onTap: () async {
        final ok = await launchUrl(
          Uri.parse(url),
          mode: LaunchMode.externalApplication,
        ).catchError((_) => false);
        if (ok || !context.mounted) return;
        // ⚠️ Reports a failure rather than doing nothing — ⭐ *a tap that silently does nothing teaches
        // the reader the app is broken, and they are right.*
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open the video')),
        );
      },
      borderRadius: BorderRadius.circular(8),
      child: Row(
        children: [
          if (id != null) ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.network(
                'https://img.youtube.com/vi/$id/mqdefault.jpg',
                width: 100,
                height: 56,
                fit: BoxFit.cover,
                // ⭐ A still that will not load must not take the row with it: the card falls back to the
                // plain label, which is what shipped before there were thumbnails at all.
                errorBuilder: (_, _, _) => const SizedBox.shrink(),
                loadingBuilder: (context, child, progress) => progress == null
                    ? child
                    : const SizedBox(width: 100, height: 56),
              ),
            ),
            const SizedBox(width: 10),
          ],
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Match highlights',
                  style: TextStyle(
                    color: Brand.darkText,
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'on YouTube',
                  style: TextStyle(color: Colors.white38, fontSize: 11.5),
                ),
              ],
            ),
          ),
          const Icon(Icons.play_circle_fill, color: Brand.madOnDark, size: 24),
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
