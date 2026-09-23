/// Signals — what should I know, about my fifteen (ADR-232).
///
/// ⭐⭐ **The ordering is the design** (ADR-150). These sources are not equally reliable, and rendering them
/// as one undifferentiated list would present a Reddit rumour beside an injury FPL confirmed. So they
/// descend by evidentiary strength and **each says what it is**.
///
/// ⭐ **And the phone can do something the web cannot: remember what you had already seen.** The server has
/// no idea when you last looked — but every signal carries a stable key, so the device does. That is the
/// *what-changed* view the start checklist asked for, and it needed no new data at all.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'seen_store.dart';
import 'trending_view.dart';

/// How much the source behind a signal actually knows.
enum SignalKind { official, departure, exodus, headline, trending, unknown }

SignalKind _kindOf(String raw) => switch (raw) {
  'official' => SignalKind.official,
  'departure' => SignalKind.departure,
  'exodus' => SignalKind.exodus,
  'headline' => SignalKind.headline,
  'trending' => SignalKind.trending,
  _ => SignalKind.unknown,
};

extension on SignalKind {
  /// ⚠️ The label says **what kind of claim it is**, not how alarming it is. *"Unexplained"* is a statement
  /// about our own data, which is the honest thing an inference can say about itself.
  String get label => switch (this) {
    SignalKind.official => 'FPL',
    SignalKind.departure => 'Reported move',
    SignalKind.exodus => 'Unexplained',
    SignalKind.headline => 'Headline',
    // ⚠️ "The crowd", not "Trending". *Trending* sounds like a verdict about the player; this is a fact
    // about other managers, and the label should not borrow authority the data does not have.
    SignalKind.trending => 'The crowd',
    SignalKind.unknown => 'Signal',
  };

  Color get colour => switch (this) {
    SignalKind.official => Brand.bad,
    SignalKind.departure => Brand.bad,
    SignalKind.exodus => Brand.warn,
    SignalKind.headline => Brand.purpleLight,
    SignalKind.trending => Brand.accentTeal,
    SignalKind.unknown => Brand.muted,
  };
}

class SignalsView extends StatefulWidget {
  const SignalsView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<SignalsView> createState() => _SignalsViewState();
}

class _SignalsViewState extends State<SignalsView> {
  final SeenStore _store = SeenStore();

  /// ⭐⭐ **Trending is not a separate screen any more** (ADR-245). It was the same question — *what is the
  /// crowd doing?* — asked in a different shape, and a second screen would have meant a second ordering,
  /// a second idea of what counts as evidence, and two places to keep honest.
  String _scope = 'squad';
  late Future<(List<Map<String, dynamic>>, int, Set<String>, double?)> _load =
      _fetch();

  Future<(List<Map<String, dynamic>>, int, Set<String>, double?)>
  _fetch() async {
    final seen = await _store.load();
    final body = await widget.client.signals([
      ...widget.team.analysis.xi.map((p) => p.id),
      ...widget.team.analysis.bench.map((p) => p.id),
    ], scope: _scope);
    final signals = ((body['signals'] as List?) ?? const [])
        .cast<Map<String, dynamic>>();

    // ⭐ Marked seen on *this* render, so the badge survives exactly one visit — which is what "new since
    // you last looked" means. Saving before rendering would make it never show.
    await _store.save(signals.map((s) => '${s['key']}').toSet());
    return (
      signals,
      body['checked'] as int? ?? 0,
      seen,
      (body['ownership_floor'] as num?)?.toDouble(),
    );
  }

  void _pick(String scope) {
    if (scope == _scope) return;
    setState(() {
      _scope = scope;
      // ⚠️ Trending does not go through `signals`, and that endpoint only accepts squad/global — asking
      // it here would fetch a **422** nothing reads.
      if (scope != 'trending') _load = _fetch();
    });
  }

  @override
  Widget build(BuildContext context) {
    // ⭐ A different question needs a different body, not a reshaped one. The boards are ranked by crowd
    // volume; the signals are ranked by evidence (ADR-150). ⚠️ *Forcing both through one list would mean
    // choosing one ordering and misrepresenting the other.*
    if (_scope == 'trending') {
      return Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 0),
            child: _ScopeBar(scope: _scope, onPick: _pick),
          ),
          Expanded(
            child: TrendingBoards(client: widget.client, team: widget.team),
          ),
        ],
      );
    }
    return FutureBuilder<
      (List<Map<String, dynamic>>, int, Set<String>, double?)
    >(
      future: _load,
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
        final (signals, checked, seen, floor) = snapshot.data!;
        final fresh = signals
            .where((s) => !seen.contains('${s['key']}'))
            .length;
        final global = _scope == 'global';

        if (signals.isEmpty) {
          // ⭐ A quiet week is news. An empty screen reads as a failure to load.
          return Column(
            children: [
              _ScopeBar(scope: _scope, onPick: _pick),
              Expanded(child: _Empty(checked: checked)),
            ],
          );
        }

        return ListView(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 22),
          children: [
            _ScopeBar(scope: _scope, onPick: _pick),
            const SizedBox(height: 10),
            Text(
              global
                  // ⚠️⚠️ **The floor is stated, always.** A market view that silently drops four fifths of
                  // the board is a view that lies by omission — ⭐ *a filter the reader cannot see is one he
                  // will eventually be surprised by* (ADR-215).
                  ? '$fresh new · ${signals.length} across $checked players '
                        'owned by ${floor?.toStringAsFixed(1) ?? '—'}% or more'
                  : fresh == 0
                  ? '${signals.length} across your $checked players — nothing new since you last looked.'
                  : '$fresh new · ${signals.length} across your $checked players',
              style: const TextStyle(
                color: Colors.white54,
                fontSize: 12,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 12),
            for (final signal in signals)
              _Signal(data: signal, isNew: !seen.contains('${signal['key']}')),
            const SizedBox(height: 12),
            const Text(
              'Ordered by how much the source actually knows: FPL first, then a reported move, then a '
              'sell-off nothing in the data explains, then headlines.',
              style: TextStyle(
                color: Colors.white24,
                fontSize: 10.5,
                height: 1.5,
              ),
            ),
          ],
        );
      },
    );
  }
}

class _Signal extends StatelessWidget {
  const _Signal({required this.data, required this.isNew});

  final Map<String, dynamic> data;
  final bool isNew;

  @override
  Widget build(BuildContext context) {
    final kind = _kindOf('${data['kind']}');
    final player = PlayerSummary.fromJson(
      data['player'] as Map<String, dynamic>,
    );

    return Container(
      margin: const EdgeInsets.only(bottom: 9),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 11),
      decoration: BoxDecoration(
        color: Colors.white10,
        border: Border(left: BorderSide(color: kind.colour, width: 3)),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                player.name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                '${player.team} · ${player.position}',
                style: const TextStyle(color: Colors.white38, fontSize: 11),
              ),
              // ⭐⭐ **"Yours" changes what the signal means, not just who it is about.** An exodus from a
              // player you hold is a decision; the same exodus from one you do not is a fact about the
              // market. ⚠️ Flagged by the server so the client is not matching ids and getting it wrong.
              if (data['owned'] == true) ...[
                const SizedBox(width: 6),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 1,
                  ),
                  decoration: BoxDecoration(
                    border: Border.all(color: Brand.purpleLight, width: 1),
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
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
              const Spacer(),
              if (isNew)
                Container(
                  margin: const EdgeInsets.only(right: 6),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 1,
                  ),
                  decoration: BoxDecoration(
                    color: Brand.accentTeal,
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
                  ),
                  child: const Text(
                    'new',
                    style: TextStyle(
                      color: Brand.ink,
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              Text(
                kind.label,
                style: TextStyle(
                  color: kind.colour,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 5),
          Text(
            '${data['headline']}',
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 13,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            '${data['detail']}',
            style: const TextStyle(
              color: Colors.white38,
              fontSize: 11,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty({required this.checked});

  final int checked;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.check_circle_outline,
            size: 30,
            color: Colors.white24,
          ),
          const SizedBox(height: 10),
          Text(
            'Nothing to report across your $checked players.',
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white54, fontSize: 13.5),
          ),
          const SizedBox(height: 6),
          const Text(
            'No FPL news, no reported moves, no sell-off the data cannot explain.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white24,
              fontSize: 11.5,
              height: 1.5,
            ),
          ),
        ],
      ),
    ),
  );
}

/// Your fifteen, or the market — ⭐ **one screen, two questions** (ADR-245).
///
/// ⚠️ Squad is first and is the default. *A default that widens the question is a default that surprises
/// somebody*, and the app is the decision layer before it is the exploration one.
class _ScopeBar extends StatelessWidget {
  const _ScopeBar({required this.scope, required this.onPick});

  final String scope;
  final ValueChanged<String> onPick;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      // ⚠️⚠️ **Trending returns as a tab, not as the screen ADR-245 removed.** That ADR folded the old
      // Trending *page* into the market scope and was right: *"what is notable?"* was asked twice. ⭐ This
      // is the other question — **the charts** — ordered by how many managers moved, where the market
      // scope orders by how strong the evidence is. *Same data, different ordering.*
      for (final (value, label) in const [
        ('squad', 'My squad'),
        ('global', 'The market'),
        ('trending', 'Trending'),
      ])
        Expanded(
          child: GestureDetector(
            onTap: () => onPick(value),
            behavior: HitTestBehavior.opaque,
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 2),
              padding: const EdgeInsets.symmetric(vertical: 8),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: scope == value ? Brand.purple : Colors.white10,
                borderRadius: BorderRadius.circular(Brand.radiusPill),
              ),
              child: Text(
                label,
                style: TextStyle(
                  color: scope == value ? Colors.white : Colors.white54,
                  fontSize: 12.5,
                  fontWeight: scope == value
                      ? FontWeight.w600
                      : FontWeight.w400,
                ),
              ),
            ),
          ),
        ),
    ],
  );
}
