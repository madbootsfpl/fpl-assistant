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
import 'pitch.dart';
import 'pitch_markings.dart';
import 'result_pitch.dart';

/// How far forward the swipe goes (ADR-298).
///
/// ⚠️ Not a hedge picked to sound cautious: **five is already the answer elsewhere** — the Lab's wildcard
/// and fresh-season modes plan over five, Players ranks on *"xP over 5 GW"*. ⭐ *A new limit that
/// disagrees with the limits already in the product teaches the reader that limits are arbitrary.*
const int kForwardWeeks = 5;

/// One played gameweek, drawn as a list of what each player did.
class PastGameweek extends StatelessWidget {
  const PastGameweek({required this.result, this.onTapPlayer, super.key});

  final GameweekResult result;

  /// ⭐ Carries **which week the tap came from** (ADR-299) — the sheet opens on that gameweek rather
  /// than on the next one.
  final void Function(
    PlayerSummary player,
    int? gameweek,
    GameweekPlayer? result,
  )?
  onTapPlayer;

  @override
  Widget build(BuildContext context) {
    if (!result.played) {
      // ⭐ Named here as well. *"This gameweek has not been played yet"* with no gameweek on it is the
      // same omission in a shorter sentence.
      return _NotYet(gameweek: result.gameweek);
    }
    // ⚠️⚠️⚠️ **A pitch, not a list** — the owner's feedback on the first build: *"the right swipe into
    // history shows a list rather than a pitch layout."* ⭐ *The pitch is how this app says "your team";
    // the same fifteen names in a column says "a report about your team",* and the reason to swipe back
    // is to see the side you picked in the shape you picked it.
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 0, 14, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _WeekLine(gameweek: result.gameweek, label: 'final'),
              _Summary(summary: result.summary),
            ],
          ),
        ),
        const SizedBox(height: 8),
        // ⭐ The green runs to the bottom, exactly as it does on the live pitch (ADR-253) — ⚠️ *a past
        // week drawn in half the space would read as a lesser screen.*
        Expanded(
          child: ClipRRect(
            borderRadius: const BorderRadius.vertical(
              top: Radius.circular(Brand.radiusMd),
            ),
            child: PitchMarkings(
              child: ResultPitch(
                result: result,
                // ⭐ The week that was played — the sheet opens on the result, not on a projection.
                // ⭐ The whole entry travels with the tap: what he did that week is the one thing the
                // sheet cannot look up for itself (ADR-299).
                onTapPlayer: onTapPlayer == null
                    ? null
                    : (e) => onTapPlayer!(e.player, result.gameweek, e),
              ),
            ),
          ),
        ),
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
  // ⭐ No card around it any more. On the live pitch these four figures sit bare under the gameweek
  // line, and ⚠️ *a panel here and no panel there makes two screens out of one.*
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 2),
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

  /// ⭐ Carries **which week the tap came from**, and on a played week **what he did in it**
  /// (ADR-299) — so the sheet opens on that gameweek rather than on the next one.
  final void Function(
    PlayerSummary player,
    int? gameweek,
    GameweekPlayer? result,
  )
  onTapPlayer;

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
      if (gameweek < _current) {
        // ⭐ Tapping a past player opens the same sheet the live pitch opens — ⚠️ *a card that is
        // tappable on one page and inert on the next teaches the reader that neither is reliable.*
        return _Past(
          future: _result(gameweek),
          onTapPlayer: widget.onTapPlayer,
        );
      }
      if (gameweek == _current) {
        return PitchView(
          team: widget.team,
          mode: widget.mode,
          onMode: widget.onMode,
          // ⭐ Null: the live pitch IS the next gameweek, and the sheet's default is that week.
          onTapPlayer: (p) => widget.onTapPlayer(p, null, null),
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
          onTapPlayer: (p) => widget.onTapPlayer(p, gameweek, null),
          gameweek: gameweek,
        );
      }
      return const ForwardEdge();
    },
  );
}

/// A past page, while its week is in the air.
class _Past extends StatelessWidget {
  const _Past({required this.future, this.onTapPlayer});

  final Future<GameweekResult> future;

  /// ⭐ Carries **which week the tap came from** (ADR-299) — the sheet opens on that gameweek rather
  /// than on the next one.
  final void Function(
    PlayerSummary player,
    int? gameweek,
    GameweekPlayer? result,
  )?
  onTapPlayer;

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
      return PastGameweek(result: snap.data!, onTapPlayer: onTapPlayer);
    },
  );
}
