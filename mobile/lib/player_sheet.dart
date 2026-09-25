/// Tap a player on the pitch (ADR-226).
///
/// ⭐⭐ **The armband is a tap, not a screen.** Setting a captain changes no number this app computes —
/// FPL doubles the captain's points; our projections are the XI's own xP and do not — so it is a display
/// decision, and a display decision does not deserve a tab of its own. The owner saw that before I did:
/// *"surely a simple client side click for captain & vice Captain could be viable."*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'mugshot.dart';
import 'ticker_view.dart' show difficultyColour;
import 'player_picker.dart';

/// What the sheet was asked to do.
sealed class PlayerAction {
  const PlayerAction();
}

class MakeCaptain extends PlayerAction {
  const MakeCaptain(this.playerId);
  final int playerId;
}

class MakeVice extends PlayerAction {
  const MakeVice(this.playerId);
  final int playerId;
}

/// Change two players' places in the XI — ⭐ free and reversible, unlike [ReplaceWith].
class SwapWith extends PlayerAction {
  const SwapWith(this.a, this.b);

  final int a;
  final int b;
}

class ReplaceWith extends PlayerAction {
  const ReplaceWith(this.outId, this.inId);
  final int outId;
  final int inId;
}

/// Opens the sheet for [player] and returns what the manager chose, or null.
Future<PlayerAction?> showPlayerSheet(
  BuildContext context, {
  required MyTeam team,
  required PlayerSummary player,
  required ServiceClient client,
  int? gameweek,
  GameweekPlayer? result,
}) => showModalBottomSheet<PlayerAction>(
  context: context,
  backgroundColor: Brand.ink,
  isScrollControlled: true,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(Brand.radiusLg)),
  ),
  builder: (_) => _PlayerSheet(
    team: team,
    player: player,
    client: client,
    gameweek: gameweek,
    result: result,
  ),
);

class _PlayerSheet extends StatefulWidget {
  const _PlayerSheet({
    required this.team,
    required this.player,
    required this.client,
    this.gameweek,
    this.result,
  });

  final MyTeam team;
  final PlayerSummary player;
  final ServiceClient client;

  /// The gameweek page this sheet was opened from, or null on the live pitch (ADR-299).
  ///
  /// ⭐⭐⭐ **ADR-298 made the pitch week-aware and left this behind.** Swipe to a future week, tap a
  /// player, and the sheet answered a question about *this* Saturday — ⚠️ *a screen that changes what it
  /// is about must change what its children are about*, and the sheet is where a reader goes for detail.
  final int? gameweek;

  /// What this player actually did, when the sheet was opened from a **played** week (ADR-299).
  ///
  /// ⭐⭐ **Its presence is what makes this a different card**, rather than a flag saying so. Null on every
  /// other page, and the one thing a past sheet has that no other sheet can have.
  final GameweekPlayer? result;

  @override
  State<_PlayerSheet> createState() => _PlayerSheetState();
}

class _PlayerSheetState extends State<_PlayerSheet> {
  Future<ReplacementsAnswer>? _options;

  /// ⭐ A second mode on the same sheet rather than a second sheet — you are still deciding about the same
  /// player, and pushing a route would lose the context you opened it from.
  bool _swapping = false;

  /// ⭐⭐ **The desktop's mini-card, merged into the sheet the owner already taps** (ADR-276).
  ///
  /// The owner: *"do you think there is enough real estate to merge these 2 at the bottom of the
  /// screen… so you can select the option as well as having some real stats?"* There is — the sheet was
  /// four actions and a subtitle, in a panel half of which was blank.
  ///
  /// ⚠️ **Fetched, not free.** The run and the price are already in hand; the season stats are not, and
  /// they are the half that answers *"is he actually any good?"* ⭐ *The alternative was a second tap to
  /// a second screen, which is the thing this merge removes.*
  late final Future<PlayerCard> _card = widget.client.player(widget.player.id);

  void _findReplacements() {
    final team = widget.team;
    setState(() {
      _options = widget.client.replacements(
        [
          ...team.analysis.xi.map((p) => p.id),
          ...team.analysis.bench.map((p) => p.id),
        ],
        widget.player.id,
        benchIds: team.analysis.bench.map((p) => p.id).toList(),
        horizon: 1,
        // ⚠️ The real bank. A search run against £0 would hide every affordable option behind a flag.
        bank: team.bank ?? 0.0,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.player;
    final past = widget.result;
    final isCaptain = p.id == widget.team.captainId;
    final isVice = p.id == widget.team.viceCaptainId;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 18),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 36,
                height: 4,
                margin: const EdgeInsets.only(bottom: 14),
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text(
              p.name,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 19,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              // ⚠️⚠️ **No xP and no price on a played week.** Both are facts about *today* — a projection
              // for a match that has been played is meaningless, and today's price under a GW4 heading
              // reads as the price then. ⭐ *A true number in the wrong place becomes a false claim*, the
              // same rule the forward pitch follows.
              past == null
                  ? '${p.position} · ${p.team} · £${p.price.toStringAsFixed(1)}m · '
                        '${p.xp.toStringAsFixed(1)} xP'
                  : '${p.position} · ${p.team} · GW${widget.gameweek}',
              style: const TextStyle(color: Colors.white54, fontSize: 12.5),
            ),
            // ⭐⭐⭐ **What he actually did** (ADR-299) — the owner's report: *"the player pop up card needs
            // to show the history of that GW and not the prediction from the current gameweek onwards."*
            if (past != null) _Played(entry: past),
            // ⚠️ **Only with the actions.** Once the sheet has become a replacement list or a swap
            // picker it is answering a different question, and ⭐ *a stat block under a list of
            // candidates describes the wrong player.*
            if (past == null && _options == null && !_swapping)
              _Card(
                future: _card,
                team: widget.team,
                player: p,
                gameweek: widget.gameweek,
              ),
            const SizedBox(height: 12),
            // ⚠️⚠️⚠️ **The played-week guard belongs INSIDE this branch, not on it** — putting it on the
            // `if` dropped a past week through to the `else` below, which dereferences `_options!`, and
            // the whole sheet threw before drawing a pixel. ⭐ *A condition added to the head of an
            // if/else chain changes which branch every other case lands in*, and this one is three
            // branches long.
            if (_options == null && !_swapping) ...[
              // ⭐⭐ **One row, not four** (ADR-286). Four full-width rows cost ~200pt of a sheet whose
              // job is to show a player, and ⚠️ *a sheet that pushes its own subject off the screen has
              // become a menu about him.* Across, they read as *what can I do here?* — one glance, four
              // answers.
              //
              // ⚠️ **Order preserved, left to right.** A substitution is free and reversible; a transfer
              // costs points and cannot be undone — ⭐ *order on a set of actions is a recommendation,
              // whether or not it was meant as one*, and reading order still carries it.
              // ⚠️⚠️ **Nothing to do about a week that has been played.** Captain · Vice · Bench ·
              // Transfer were being offered against a gameweek that finished eleven days ago — ⭐ *an
              // action that cannot be taken is worse than a missing one, because the reader has to work
              // out why it did nothing.*
              if (past == null)
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: _Action(
                        icon: Icons.star,
                        label: isCaptain ? 'Your captain' : 'Captain',
                        enabled: !isCaptain,
                        onTap: () => Navigator.pop(context, MakeCaptain(p.id)),
                      ),
                    ),
                    Expanded(
                      child: _Action(
                        icon: Icons.star_half,
                        label: isVice ? 'Your vice' : 'Vice-captain',
                        enabled: !isVice,
                        onTap: () => Navigator.pop(context, MakeVice(p.id)),
                      ),
                    ),
                    Expanded(
                      child: _Action(
                        icon: Icons.swap_vert,
                        // ⭐ **"Substitute", the word FPL uses** (feedback) — the same reasoning that made
                        // "Replace him" into "Transfer": ⚠️ *an app that renames the moves makes the
                        // manager translate.* The bench direction keeps its own word, since "Substitute"
                        // does not say which way he is going.
                        label: widget.team.benchedIds.contains(p.id)
                            ? 'Substitute'
                            : 'Bench',
                        // ⚠️ Shown greyed rather than removed when he has no legal partner. ⭐ *A row of
                        // four that sometimes has three moves the other three sideways*, and a control
                        // that changes place is a control you have to find again.
                        enabled: widget.team.swapsFor(p.id).isNotEmpty,
                        onTap: () => setState(() => _swapping = true),
                      ),
                    ),
                    Expanded(
                      child: _Action(
                        icon: Icons.swap_horiz,
                        // ⭐ **"Transfer", because that is the word FPL uses** (feedback item 1).
                        label: 'Transfer',
                        enabled: true,
                        onTap: _findReplacements,
                      ),
                    ),
                  ],
                ),
            ] else if (_swapping)
              Flexible(
                child: _SwapOptions(team: widget.team, player: p),
              )
            else
              Flexible(
                child: _Options(
                  future: _options!,
                  outId: p.id,
                  onBack: () => setState(() => _options = null),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Action extends StatelessWidget {
  const _Action({
    required this.icon,
    required this.label,
    required this.enabled,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool enabled;
  final VoidCallback onTap;

  /// ⭐ Icon above word, because four of these share a line. Side by side they would each need the
  /// width of their longest label; stacked, the icon carries the recognition and the word confirms it.
  @override
  Widget build(BuildContext context) => InkWell(
    onTap: enabled ? onTap : null,
    borderRadius: BorderRadius.circular(Brand.radiusMd),
    child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 11, horizontal: 2),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 21,
            color: enabled ? Brand.purpleLight : Colors.white24,
          ),
          const SizedBox(height: 6),
          // ⚠️ `scaleDown`, so "Vice-captain" on a narrow phone shrinks rather than wrapping to two
          // lines and making its tile taller than the three beside it.
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              label,
              style: TextStyle(
                color: enabled ? Colors.white : Colors.white24,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

/// ⭐⭐ **A candidate list you can sift** (ADR-264). It arrived as a flat list of everything affordable,
/// which for a midfielder is most of the market — ⚠️ *a list nobody can sift is a list nobody reads to
/// the bottom of*, so it was really offering its top.
///
/// ⚠️ It keeps its own chrome rather than becoming the modal picker: this list is **already inside** the
/// player sheet, and the over-budget flag below is a deliberate feature the generic row does not carry.
/// ⭐ *The sifting is shared; the presentation is not the thing that was wrong.*
class _Options extends StatefulWidget {
  const _Options({required this.future, required this.outId, this.onBack});

  final Future<ReplacementsAnswer> future;
  final int outId;

  /// ⭐ **A way to change your mind** (feedback) — the list replaces the actions in place, so without
  /// this the only way back out is closing the sheet and finding the player again.
  final VoidCallback? onBack;

  @override
  State<_Options> createState() => _OptionsState();
}

class _OptionsState extends State<_Options> {
  final TextEditingController _search = TextEditingController();
  String? _club;
  PickerSort _sort = PickerSort.xp;

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<ReplacementsAnswer>(
    future: widget.future,
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
            style: const TextStyle(color: Colors.white70),
          ),
        );
      }
      final answer = snapshot.data!;
      final shown = siftPlayers<Replacement>(
        answer.candidates,
        (c) => c.player,
        query: _search.text,
        club: _club,
        sort: _sort,
      );
      return Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              if (widget.onBack != null)
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white70),
                  onPressed: widget.onBack,
                  tooltip: 'Back',
                  visualDensity: VisualDensity.compact,
                ),
              Expanded(
                child: Text(
                  '£${answer.budget.toStringAsFixed(1)}m to spend',
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ),
              Text(
                // ⭐ So an empty list reads as *"your filters"*, not *"nobody is available"*.
                '${shown.length}',
                style: const TextStyle(color: Colors.white38, fontSize: 12),
              ),
            ],
          ),
          PickerControls(
            search: _search,
            onChanged: (_) => setState(() {}),
            sort: _sort,
            onSort: (s) => setState(() => _sort = s),
            club: _club,
            clubs: clubsIn<Replacement>(answer.candidates, (c) => c.player),
            onClub: (c) => setState(() => _club = c),
          ),
          if (shown.isEmpty)
            const Padding(
              padding: EdgeInsets.all(20),
              child: Text(
                'Nobody matches that. Clear the search or the club.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white38, fontSize: 12.5),
              ),
            ),
          Flexible(
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: shown.length,
              itemBuilder: (_, i) {
                final c = shown[i];
                return InkWell(
                  onTap: () => Navigator.pop(
                    context,
                    ReplaceWith(widget.outId, c.player.id),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 9),
                    child: Row(
                      children: [
                        Expanded(
                          child: Row(
                            children: [
                              Flexible(
                                child: Text(
                                  c.player.name,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                              // ⚠️ **Flagged, never hidden.** The owner's call: *"can select a higher
                              // priced player, just flag it as over budget"* — and a candidate
                              // silently removed looks like one that does not exist, so a manager
                              // would conclude the player is ineligible rather than dear.
                              if (!c.affordable)
                                Container(
                                  margin: const EdgeInsets.only(left: 6),
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 1,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Brand.warnTint,
                                    borderRadius: BorderRadius.circular(
                                      Brand.radiusPill,
                                    ),
                                  ),
                                  child: Text(
                                    '£${c.overBy.toStringAsFixed(1)}m over',
                                    style: const TextStyle(
                                      color: Brand.warnFg,
                                      fontSize: 9.5,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ),
                        SizedBox(
                          width: 40,
                          child: Text(
                            c.player.team,
                            style: const TextStyle(
                              color: Colors.white38,
                              fontSize: 11,
                            ),
                          ),
                        ),
                        SizedBox(
                          width: 52,
                          child: Text(
                            '£${c.player.price.toStringAsFixed(1)}',
                            textAlign: TextAlign.right,
                            style: const TextStyle(
                              color: Colors.white60,
                              fontSize: 12.5,
                            ),
                          ),
                        ),
                        SizedBox(
                          width: 44,
                          child: Text(
                            c.player.xp.toStringAsFixed(1),
                            textAlign: TextAlign.right,
                            style: const TextStyle(
                              color: Brand.accentTeal,
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text(
              'Players over your budget are shown too — prices drift, and a move you cannot quite '
              'afford yet is still a plan.',
              style: TextStyle(
                color: Colors.white38,
                fontSize: 10.5,
                height: 1.45,
              ),
            ),
          ),
        ],
      );
    },
  );
}

/// Who this player can change places with — ⭐ **the engine's list, not the client's** (ADR-246).
///
/// ⚠️⚠️ FPL's formation limits decide this, and they live in `XI_FLEX` on the server. A client that
/// offered "any bench player" would propose squads FPL rejects — a keeper for a forward being the one
/// everybody hits first.
class _SwapOptions extends StatelessWidget {
  const _SwapOptions({required this.team, required this.player});

  final MyTeam team;
  final PlayerSummary player;

  @override
  Widget build(BuildContext context) {
    final benched = team.benchedIds.contains(player.id);
    final ids = team.swapsFor(player.id);
    final all = [...team.analysis.xi, ...team.analysis.bench];
    final options = [for (final id in ids) ...all.where((p) => p.id == id)];
    // ⭐ Best first — it is a lineup decision, and the number is the reason for it.
    options.sort((a, b) => b.xp.compareTo(a.xp));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(
            benched
                ? 'Bring ${player.name} on for…'
                : 'Bench ${player.name} and start…',
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
        ),
        // ⚠️ Only the legal ones are here at all. Showing the rest greyed out would invite a manager to
        // wonder what he did wrong, when the answer is "nothing — FPL would not allow it".
        Flexible(
          child: ListView(
            shrinkWrap: true,
            children: [
              for (final other in options)
                ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    other.name,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                  ),
                  subtitle: Text(
                    '${other.position} · ${other.team} · '
                    '${other.xp.toStringAsFixed(1)} xP',
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 11.5,
                    ),
                  ),
                  trailing: const Icon(
                    Icons.swap_vert,
                    size: 17,
                    color: Brand.purpleLight,
                  ),
                  onTap: () =>
                      Navigator.pop(context, SwapWith(player.id, other.id)),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

/// The stats half of the sheet (ADR-276): his run, then his season.
///
/// ⭐ **The run is drawn immediately and the season fills in.** The fixtures are already on the device
/// (`MyTeam` carries three per club); the season stats are a round trip. ⚠️ *Blocking the whole card on
/// the slower half would make the fast half feel slow.*
class _Card extends StatelessWidget {
  const _Card({
    required this.future,
    required this.team,
    required this.player,
    this.gameweek,
  });

  final Future<PlayerCard> future;
  final MyTeam team;
  final PlayerSummary player;

  /// The week being looked at — see `showPlayerSheet`.
  final int? gameweek;

  @override
  Widget build(BuildContext context) {
    // ⚠️⚠️ **From the week you are standing on, not always from the next one** (ADR-299). Tapping a
    // player on the GW9 page used to open GW6 · GW7 · GW8 — ⭐ *three correct numbers answering a
    // question the reader had already swiped past.*
    //
    // ⭐ **This half cost one line and no request.** `runFor` and `runXpFor` have carried six gameweeks
    // since ADR-298 widened the window to `SWIPE`; the sheet was simply always reading from the front.
    final all = team.runFor(player);
    final from = gameweek == null
        ? 0
        : all.indexWhere((f) => f.gameweek == gameweek);
    // ⚠️ A week the run does not contain (a blank gameweek, or a stale page) falls back to the front
    // rather than showing nothing — *an empty row reads as a broken card.*
    final run = from <= 0 ? all : all.sublist(from);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (run.isNotEmpty) ...[
          const SizedBox(height: 12),
          Row(
            children: [
              for (final fixture in run.take(3))
                Expanded(
                  child: _Fixture(
                    fixture: fixture,
                    // ⚠️⚠️ **`runXpFor`, not the player's own map** (ADR-286). `my-team` is fetched with
                    // `horizon: 1`, so `player.byGameweek` holds **one** gameweek and the second and
                    // third fixtures rendered as `—`. The numbers were on the device the whole time,
                    // in `run_xp` — ⭐ *a value that is fetched, parsed, stored and then read from the
                    // wrong place looks exactly like a value the server never sent.*
                    xpByGameweek: team.runXpFor(player),
                  ),
                ),
            ],
          ),
        ],
        FutureBuilder<PlayerCard>(
          future: future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 18),
                child: Center(
                  child: SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }
            // ⚠️ **A failure here loses the stats, never the actions.** ⭐ *The reason the sheet exists
            // is the four buttons below it*, and a network error must not take them with it.
            if (snapshot.hasError) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 10),
                child: Text(
                  'Season stats did not load.',
                  style: TextStyle(color: Colors.white24, fontSize: 11),
                ),
              );
            }
            final card = snapshot.data!;
            // ⭐ Four, not nine. The endpoint returns everything the Players tab shows; this is a sheet
            // above a pitch, and ⚠️ *a stat block long enough to push the actions off-screen has
            // replaced them rather than joined them.*
            final shown = card.stats.take(4).toList();
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Row(
                    children: [
                      Mugshot(url: card.photo, name: player.name, size: 40),
                      const SizedBox(width: 12),
                      for (final stat in shown)
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              FittedBox(
                                fit: BoxFit.scaleDown,
                                alignment: Alignment.centerLeft,
                                child: Text(
                                  stat.value,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 15,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              FittedBox(
                                fit: BoxFit.scaleDown,
                                alignment: Alignment.centerLeft,
                                child: Text(
                                  stat.label,
                                  style: const TextStyle(
                                    color: Colors.white38,
                                    fontSize: 9.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
                // ⭐⭐ **The lenses, on one line** (ADR-286). Ownership tier then set-piece duty — the
                // order they answer in: *how many people own him* frames *what he does for them.*
                // The web card has shown these for a year; ⚠️ *the phone was not missing a feature, it
                // was showing a different product.*
                //
                // ⚠️ **Never a number.** A penalty taker's penalties are already inside his xP — ⭐ *a
                // badge says why the projection looks like that, which is a different job from saying
                // what it is*, and a badge that looked like a score would be read as one.
                if (card.badges.isNotEmpty) _Badges(badges: card.badges),
              ],
            );
          },
        ),
      ],
    );
  }
}

/// One upcoming fixture — ⭐ **shaded on the same 1-5 scale as the ticker** (ADR-265), because *a colour
/// that means "hard" on one screen must not mean anything else on another* (ADR-184).
class _Fixture extends StatelessWidget {
  const _Fixture({required this.fixture, required this.xpByGameweek});

  final Fixture fixture;

  /// ⭐ The run's projections, which cover **every** fixture shown — not the squad summary's, which
  /// covers only the gameweek the board was asked for.
  final Map<int, double> xpByGameweek;

  @override
  Widget build(BuildContext context) {
    final gw = fixture.gameweek;
    // ⚠️ Per-gameweek xP, which is the number that makes a fixture readable — *"CRY (H)" says who; "4.4"
    // says what it is worth.*
    final xp = gw == null ? null : xpByGameweek[gw];
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 2),
      padding: const EdgeInsets.symmetric(vertical: 6),
      decoration: BoxDecoration(
        color: difficultyColour(fixture.difficulty).withValues(alpha: 0.28),
        border: Border.all(
          color: difficultyColour(fixture.difficulty).withValues(alpha: 0.7),
        ),
        borderRadius: BorderRadius.circular(Brand.radiusSm),
      ),
      child: Column(
        children: [
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              fixture.label,
              style: const TextStyle(color: Colors.white, fontSize: 11),
            ),
          ),
          Text(
            xp == null ? '—' : xp.toStringAsFixed(1),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

/// Ownership tier and set-piece duty, on one line (ADR-286).
///
/// ⭐⭐ **Glyph first, word second, both small.** The owner asked for "set piece and template emojis",
/// and the emoji alone was the temptation — ⚠️ *three unlabelled pictures is a rebus, and the reader who
/// does not already know what 🎯 means has no way to find out from a phone.* The web card learned this
/// the other way round (ADR-178): on a 104px kit the words wrapped to three lines, so the pitch dropped
/// them and put a key at the bottom. ⭐ There is room here, and a sheet has no key.
class _Badges extends StatelessWidget {
  const _Badges({required this.badges});

  final List<({String glyph, String label})> badges;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 12),
    // ⚠️ Wraps rather than scrolls. Four badges fit a phone; a fifth would be invisible in a scroller
    // nothing suggests you can scroll — ⭐ *a row that can hide something must not look full.*
    child: Wrap(
      spacing: 6,
      runSpacing: 6,
      children: [
        for (final badge in badges)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
            decoration: BoxDecoration(
              color: Colors.white10,
              borderRadius: BorderRadius.circular(Brand.radiusPill),
            ),
            child: Text(
              '${badge.glyph} ${badge.label}',
              style: const TextStyle(color: Colors.white70, fontSize: 11.5),
            ),
          ),
      ],
    ),
  );
}

/// What a player actually did in a week that has been played (ADR-299).
///
/// ⭐⭐⭐ **The owner's report, and the reason the card had to change at all:** *"the player pop up card
/// needs to show the history of that GW and not the prediction from the current gameweek onwards."*
///
/// ⚠️ Every number here comes from FPL — the total, the per-line attribution, and the scoreline. ⭐ *This
/// widget adds up nothing*, which is the whole design: a breakdown computed here would disagree with the
/// total the moment the game's scoring changes, and it changed this season.
class _Played extends StatelessWidget {
  const _Played({required this.entry});

  final GameweekPlayer entry;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      const SizedBox(height: 12),
      Container(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 11),
        decoration: BoxDecoration(
          color: Colors.white10,
          borderRadius: BorderRadius.circular(Brand.radiusMd),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    // ⚠️ A blank gameweek is a dash, not a zero — the rule the pitch already follows.
                    entry.didPlay ? '${entry.points}' : '—',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                if (entry.isCaptain || entry.isViceCaptain)
                  Text(
                    entry.isCaptain ? 'Captain' : 'Vice-captain',
                    style: const TextStyle(
                      color: Brand.purple,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
              ],
            ),
            const Text(
              'points',
              style: TextStyle(color: Colors.white38, fontSize: 11),
            ),
            // ⭐ The scoreline — *a bare total says how many; this says what match.* One row per
            // fixture, because a double gameweek is two of them.
            for (final m in entry.matches) ...[
              const SizedBox(height: 9),
              Text(
                m.opponent == null
                    // ⚠️ Null is never rendered as a guess.
                    ? 'opponent unknown'
                    : m.hasScore
                    ? '${m.home ? 'v' : 'away to'} ${m.opponent}  ${m.scored}–${m.conceded}'
                    : '${m.home ? 'v' : 'away to'} ${m.opponent}',
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
            ],
          ],
        ),
      ),
      const SizedBox(height: 10),
      if (entry.breakdown.isEmpty)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Text(
            // ⚠️⚠️ **Not an empty table.** FPL publishes no lines for a man who never came on, and ⭐ *a
            // table of zeroes claims he played and scored nothing, which is a different week.*
            entry.didPlay
                ? 'No scoring events this week.'
                : entry.benched
                ? 'On your bench, and did not come on.'
                : 'Did not play.',
            style: const TextStyle(color: Colors.white38, fontSize: 12.5),
          ),
        )
      else
        for (final line in entry.breakdown) _Line(line: line),
    ],
  );
}

/// One row of FPL's attribution — what he did, and what it was worth.
class _Line extends StatelessWidget {
  const _Line({required this.line});

  final ScoreLine line;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                line.label,
                style: const TextStyle(color: Colors.white, fontSize: 13),
              ),
              Text(
                // ⭐ `minutes` reads as a duration and everything else as a count — *"90 minutes" and
                // "1 goals" are the difference between a sentence and a database row.*
                line.stat == 'minutes' ? "${line.value}'" : '${line.value}',
                style: const TextStyle(color: Colors.white38, fontSize: 11),
              ),
            ],
          ),
        ),
        Text(
          // ⭐ Signed, always: a deduction has to be legible **as** a deduction.
          line.points > 0 ? '+${line.points}' : '${line.points}',
          style: TextStyle(
            color: line.points < 0 ? Brand.bad : Colors.white,
            fontSize: 15,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    ),
  );
}
