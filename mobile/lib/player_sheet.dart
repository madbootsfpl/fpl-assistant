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
            const SizedBox(height: 14),
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
                  label: widget.team.benchedIds.contains(p.id)
                      ? 'Bring him on…'
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
                child: _Options(future: _options!, outId: p.id),
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

class _Options extends StatelessWidget {
  const _Options({required this.future, required this.outId});

  final Future<ReplacementsAnswer> future;
  final int outId;

  @override
  Widget build(BuildContext context) => FutureBuilder<ReplacementsAnswer>(
    future: future,
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
      return Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              '£${answer.budget.toStringAsFixed(1)}m to spend',
              style: const TextStyle(color: Colors.white54, fontSize: 12),
            ),
          ),
          Flexible(
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: answer.candidates.length,
              itemBuilder: (_, i) {
                final c = answer.candidates[i];
                return InkWell(
                  onTap: () =>
                      Navigator.pop(context, ReplaceWith(outId, c.player.id)),
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
