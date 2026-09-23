/// Squad Lab — rebuild your fifteen and see what changes (ADR-268).
///
/// ⭐⭐ **A wildcard draft is only useful next to the squad it replaces.** The solver has answered *"the
/// best fifteen within a budget"* since ADR-013, and on its own that is a list of names you then have to
/// diff against your own team in your head. ⚠️ *The comparison is the product; the squad is the input to
/// it.*
///
/// ⭐ **Nothing here changes anything.** FPL has no write API (and would not be given one), so this is a
/// scratchpad — which is also why it can afford to be wrong: *an experiment you cannot accidentally
/// execute is one you can run freely.*
///
/// 📌 **Wildcard first, by the owner's call** — *"will need all 3, however to get feedback lets start with
/// the Wildcard."* Free Hit and a fresh-season build are the **same solver with different defaults**
/// (horizon 1, and £100.0m from nothing), which is why `_Mode` exists now rather than later: ⚠️ *a second
/// mode bolted onto a screen built for one is how a screen ends up with two of everything.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

/// What the Lab is being asked to do. ⭐ Each mode is a **budget and a horizon**, not a different feature.
enum LabMode { wildcard }

extension LabModeDetail on LabMode {
  String get label => switch (this) {
    LabMode.wildcard => 'Wildcard',
  };

  /// ⚠️ The horizon is the point of the mode. A wildcard is played for a **run**; a free hit would be
  /// played for one week, and asking the solver for one week would give a different fifteen.
  int get horizon => switch (this) {
    LabMode.wildcard => 5,
  };
}

class LabView extends StatefulWidget {
  const LabView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<LabView> createState() => _LabViewState();
}

class _LabViewState extends State<LabView> {
  final LabMode _mode = LabMode.wildcard;
  final Set<int> _keep = {};
  Future<BuildAnswer>? _draft;

  List<PlayerSummary> get _mine => [
    ...widget.team.analysis.xi,
    ...widget.team.analysis.bench,
  ];

  /// ⭐⭐ **FPL's team value already includes the bank**, which is exactly what a wildcard has to spend.
  ///
  /// ⚠️ It is not the sum of what the fifteen are worth today: FPL sells a risen player for less than his
  /// current price, and ⭐ *a budget built by adding up current prices would be optimistic by exactly the
  /// amount a manager has earned* — which is the direction that invents money.
  double? get _budget => widget.team.value;

  void _run() {
    final budget = _budget;
    if (budget == null) return;
    setState(() {
      _draft = widget.client.build(
        budget: budget,
        horizon: _mode.horizon,
        includeIds: _keep.toList(),
        // ⚠️⚠️ **Without this the solver treats all fifteen as if they play**, and spends real money on
        // a bench that scores nothing (ADR-045). Measured: the bench-aware eleven beats the flat
        // build's BEST POSSIBLE eleven — 329.1 against 325.1 — so this is not a preference.
        benchWeight: 0.1,
      );
    });
  }

  void _toggle(int id) {
    setState(() {
      if (!_keep.remove(id)) _keep.add(id);
      // ⚠️ The draft is cleared, never left standing. ⭐ *A result that no longer matches the question
      // above it is worse than no result*, because it still looks like an answer.
      _draft = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final budget = _budget;
    if (budget == null) {
      return const _Note(
        'Your team value has not loaded, so there is no budget to build against. '
        'Open My Team first.',
      );
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 24),
      children: [
        _Header(mode: _mode, budget: budget, keeping: _keep.length),
        const SizedBox(height: 12),
        Text(
          // ⭐ Says what tapping does before anything is tapped — the interaction is not guessable from a
          // grid of names.
          'Tap anyone you want to keep. The rest is rebuilt around them.',
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 11.5,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 8),
        _KeepGrid(players: _mine, keep: _keep, onToggle: _toggle),
        const SizedBox(height: 14),
        Row(
          children: [
            Expanded(
              child: TextButton(
                onPressed: _run,
                style: TextButton.styleFrom(
                  backgroundColor: Brand.purple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                  ),
                ),
                child: Text(
                  _keep.isEmpty
                      ? 'Build the best fifteen'
                      : 'Build around ${_keep.length} kept',
                  style: const TextStyle(fontSize: 13.5),
                ),
              ),
            ),
            if (_keep.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(left: 8),
                child: TextButton(
                  onPressed: () => setState(() {
                    _keep.clear();
                    _draft = null;
                  }),
                  child: const Text('Clear'),
                ),
              ),
          ],
        ),
        if (_draft != null)
          Padding(
            padding: const EdgeInsets.only(top: 14),
            child: FutureBuilder<BuildAnswer>(
              future: _draft,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Padding(
                    padding: EdgeInsets.all(24),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                if (snapshot.hasError) {
                  return _Note(friendlyError(snapshot.error));
                }
                return _Draft(answer: snapshot.data!, mine: _mine);
              },
            ),
          ),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.mode,
    required this.budget,
    required this.keeping,
  });

  final LabMode mode;
  final double budget;
  final int keeping;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: Brand.purple.withValues(alpha: 0.18),
      borderRadius: BorderRadius.circular(Brand.radiusMd),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '${mode.label} — £${budget.toStringAsFixed(1)}m to spend',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14.5,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          // ⚠️⚠️ **The budget is FPL's team value, which is built from SELLING prices.** Saying so matters:
          // a manager who compares this against the prices on the pitch will find they do not add up, and
          // ⭐ *an unexplained number that disagrees with another number on the same app is a bug report.*
          'That is your FPL team value — the bank plus what your fifteen would sell for. '
          'Nothing here changes your real team.',
          style: const TextStyle(
            color: Colors.white54,
            fontSize: 11,
            height: 1.5,
          ),
        ),
      ],
    ),
  );
}

class _KeepGrid extends StatelessWidget {
  const _KeepGrid({
    required this.players,
    required this.keep,
    required this.onToggle,
  });

  final List<PlayerSummary> players;
  final Set<int> keep;
  final ValueChanged<int> onToggle;

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 5,
    runSpacing: 5,
    children: [
      for (final p in players)
        GestureDetector(
          onTap: () => onToggle(p.id),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
            decoration: BoxDecoration(
              color: keep.contains(p.id) ? Brand.purple : Colors.white10,
              borderRadius: BorderRadius.circular(Brand.radiusPill),
            ),
            child: Text(
              '${p.name} £${p.price.toStringAsFixed(1)}',
              style: TextStyle(
                color: keep.contains(p.id) ? Colors.white : Colors.white54,
                fontSize: 11.5,
                fontWeight: keep.contains(p.id)
                    ? FontWeight.w600
                    : FontWeight.w400,
              ),
            ),
          ),
        ),
    ],
  );
}

/// Who leaves and who arrives, given a draft and the squad it replaces.
///
/// ⭐ **Computed from ids, not from names** — two players can share a surname, and a diff that matched on
/// text would quietly pair the wrong two.
({List<PlayerSummary> out, List<BuiltPlayer> in_}) squadDiff(
  BuildAnswer answer,
  List<PlayerSummary> mine,
) {
  final drafted = {for (final b in answer.selected) b.player.id};
  final owned = {for (final p in mine) p.id};
  return (
    out: [
      for (final p in mine)
        if (!drafted.contains(p.id)) p,
    ],
    in_: [
      for (final b in answer.selected)
        if (!owned.contains(b.player.id)) b,
    ],
  );
}

class _Draft extends StatelessWidget {
  const _Draft({required this.answer, required this.mine});

  final BuildAnswer answer;
  final List<PlayerSummary> mine;

  @override
  Widget build(BuildContext context) {
    // ⚠️⚠️ **"Infeasible" is an answer, and it is not an empty squad.** Rendering fifteen blank rows under
    // a heading is how *"your constraints cannot be met"* gets read as *"there are no good players"*.
    if (!answer.solved) {
      return const _Note(
        'No legal fifteen fits that. Keeping several expensive players leaves too little for the rest — '
        'release one and try again.',
      );
    }
    final diff = squadDiff(answer, mine);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            _Stat(
              // ⭐⭐ **The eleven, not the fifteen.** A bench-aware draft scores *lower* on the
              // all-fifteen total while fielding a *better* side — ⚠️ *a headline that falls when the
              // answer improves is a headline that will be optimised against.*
              label: 'Your XI',
              value: (answer.xiXp ?? answer.projectedXp).toStringAsFixed(1),
              unit: answer.xiXp == null ? 'xP (all 15)' : 'xP over 5 GWs',
            ),
            _Stat(
              label: 'Spent',
              value: '£${answer.totalCost.toStringAsFixed(1)}m',
              // ⭐ What is left over, because a draft that spends everything and one that leaves £1.5m in
              // the bank are different plans.
              unit: 'of £${answer.budget.toStringAsFixed(1)}m',
            ),
            _Stat(label: 'Changes', value: '${diff.out.length}', unit: 'moves'),
          ],
        ),
        const SizedBox(height: 12),
        if (diff.out.isEmpty)
          const Text(
            // ⭐ A real and rather good outcome, said plainly rather than shown as two empty lists.
            'Nothing changes — the solver would keep your fifteen exactly as they are.',
            style: TextStyle(color: Brand.good, fontSize: 12.5, height: 1.5),
          )
        else ...[
          _Side(title: 'Out', players: diff.out, good: false),
          const SizedBox(height: 8),
          _Side(
            title: 'In',
            players: [for (final b in diff.in_) b.player],
            good: true,
          ),
        ],
        const SizedBox(height: 14),
        Text(
          'The eleven it would start',
          style: const TextStyle(
            color: Colors.white54,
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        for (final b in answer.xi) _DraftRow(built: b),
        const SizedBox(height: 10),
        Text(
          // ⚠️ Named as the solver's bench, because it is not ordered the way FPL substitutes.
          'Bench (not in substitution order)',
          style: const TextStyle(color: Colors.white38, fontSize: 11),
        ),
        const SizedBox(height: 6),
        for (final b in answer.bench) _DraftRow(built: b),
      ],
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value, required this.unit});

  final String label;
  final String value;
  final String unit;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      margin: const EdgeInsets.symmetric(horizontal: 2),
      padding: const EdgeInsets.symmetric(vertical: 9, horizontal: 6),
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusSm),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: const TextStyle(color: Colors.white38, fontSize: 10),
          ),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 15,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              unit,
              style: const TextStyle(color: Colors.white30, fontSize: 9.5),
            ),
          ),
        ],
      ),
    ),
  );
}

class _Side extends StatelessWidget {
  const _Side({required this.title, required this.players, required this.good});

  final String title;
  final List<PlayerSummary> players;
  final bool good;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        title,
        style: TextStyle(
          color: good ? Brand.good : Brand.warn,
          fontSize: 11.5,
          fontWeight: FontWeight.w600,
        ),
      ),
      const SizedBox(height: 4),
      Wrap(
        spacing: 5,
        runSpacing: 5,
        children: [
          for (final p in players)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: (good ? Brand.good : Brand.warn).withValues(alpha: 0.16),
                borderRadius: BorderRadius.circular(Brand.radiusPill),
              ),
              child: Text(
                '${p.name} £${p.price.toStringAsFixed(1)}',
                style: const TextStyle(color: Colors.white, fontSize: 11.5),
              ),
            ),
        ],
      ),
    ],
  );
}

class _DraftRow extends StatelessWidget {
  const _DraftRow({required this.built});

  final BuiltPlayer built;

  @override
  Widget build(BuildContext context) {
    final p = built.player;
    return Padding(
      padding: const EdgeInsets.only(bottom: 3),
      child: Row(
        children: [
          SizedBox(
            width: 34,
            child: Text(
              p.position,
              style: const TextStyle(color: Colors.white30, fontSize: 10.5),
            ),
          ),
          Expanded(
            child: Text(
              p.name,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Colors.white, fontSize: 12.5),
            ),
          ),
          if (built.forced)
            const Padding(
              padding: EdgeInsets.only(right: 6),
              child: Text(
                // ⭐ Says which players you chose yourself — ⚠️ *a draft that cannot tell you which is
                // which invites you to trust a choice you made.*
                'kept',
                style: TextStyle(color: Brand.purple, fontSize: 9.5),
              ),
            ),
          SizedBox(
            width: 42,
            child: Text(
              '£${p.price.toStringAsFixed(1)}',
              textAlign: TextAlign.right,
              style: const TextStyle(color: Colors.white38, fontSize: 11),
            ),
          ),
          SizedBox(
            width: 42,
            child: Text(
              p.xp.toStringAsFixed(1),
              textAlign: TextAlign.right,
              style: const TextStyle(color: Colors.white70, fontSize: 11.5),
            ),
          ),
        ],
      ),
    );
  }
}

class _Note extends StatelessWidget {
  const _Note(this.message);

  final String message;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 6),
    child: Text(
      message,
      textAlign: TextAlign.center,
      style: const TextStyle(
        color: Colors.white54,
        fontSize: 12.5,
        height: 1.55,
      ),
    ),
  );
}
