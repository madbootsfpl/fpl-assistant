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
}) => showModalBottomSheet<PlayerAction>(
  context: context,
  backgroundColor: Brand.ink,
  isScrollControlled: true,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(Brand.radiusLg)),
  ),
  builder: (_) => _PlayerSheet(team: team, player: player, client: client),
);

class _PlayerSheet extends StatefulWidget {
  const _PlayerSheet({
    required this.team,
    required this.player,
    required this.client,
  });

  final MyTeam team;
  final PlayerSummary player;
  final ServiceClient client;

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
              '${p.position} · ${p.team} · £${p.price.toStringAsFixed(1)}m · '
              '${p.xp.toStringAsFixed(1)} xP',
              style: const TextStyle(color: Colors.white54, fontSize: 12.5),
            ),
            // ⚠️ **Only with the actions.** Once the sheet has become a replacement list or a swap
            // picker it is answering a different question, and ⭐ *a stat block under a list of
            // candidates describes the wrong player.*
            if (_options == null && !_swapping)
              _Card(future: _card, team: widget.team, player: p),
            const SizedBox(height: 12),
            if (_options == null && !_swapping) ...[
              _Action(
                icon: Icons.star,
                label: isCaptain ? 'Already your captain' : 'Make captain',
                enabled: !isCaptain,
                onTap: () => Navigator.pop(context, MakeCaptain(p.id)),
              ),
              _Action(
                icon: Icons.star_half,
                label: isVice ? 'Already your vice' : 'Make vice-captain',
                enabled: !isVice,
                onTap: () => Navigator.pop(context, MakeVice(p.id)),
              ),
              // ⭐⭐ **Above Transfer, deliberately.** A substitution is free and reversible; a transfer
              // costs points and cannot be undone. ⚠️ *Order on a list of actions is a recommendation,
              // whether or not it was meant as one.*
              if (widget.team.swapsFor(p.id).isNotEmpty)
                _Action(
                  icon: Icons.swap_vert,
                  // ⭐ **"Substitute", the word FPL uses** (feedback) — the same reasoning that made
                  // "Replace him" into "Transfer": ⚠️ *an app that renames the moves makes the manager
                  // translate.* The ellipsis stays because a picker follows; the bench direction keeps
                  // its own words, since "Substitute" does not say which way he is going.
                  label: widget.team.benchedIds.contains(p.id)
                      ? 'Substitute…'
                      : 'Bench him…',
                  enabled: true,
                  onTap: () => setState(() => _swapping = true),
                ),
              _Action(
                icon: Icons.swap_horiz,
                // ⭐ **"Transfer", because that is the word FPL uses** (feedback item 1). "Replace him"
                // described the mechanic; the manager is thinking in the vocabulary of the game he is
                // playing, and an app that renames his moves makes him translate.
                label: 'Transfer…',
                enabled: true,
                onTap: _findReplacements,
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

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: enabled ? onTap : null,
    child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          Icon(
            icon,
            size: 19,
            color: enabled ? Brand.purpleLight : Colors.white24,
          ),
          const SizedBox(width: 12),
          Text(
            label,
            style: TextStyle(
              color: enabled ? Colors.white : Colors.white24,
              fontSize: 14.5,
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
  const _Card({required this.future, required this.team, required this.player});

  final Future<PlayerCard> future;
  final MyTeam team;
  final PlayerSummary player;

  @override
  Widget build(BuildContext context) {
    final run = team.runFor(player);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (run.isNotEmpty) ...[
          const SizedBox(height: 12),
          Row(
            children: [
              for (final fixture in run.take(3))
                Expanded(
                  child: _Fixture(fixture: fixture, player: player),
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
            return Padding(
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
  const _Fixture({required this.fixture, required this.player});

  final Fixture fixture;
  final PlayerSummary player;

  @override
  Widget build(BuildContext context) {
    final gw = fixture.gameweek;
    // ⚠️ Per-gameweek xP, which is the number that makes a fixture readable — *"CRY (H)" says who; "4.4"
    // says what it is worth.*
    final xp = gw == null ? null : player.byGameweek[gw];
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
