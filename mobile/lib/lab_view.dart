/// Squad Lab — build a fifteen, edit it, and make it your plan (ADR-268/272).
///
/// ⭐⭐ **A draft is only useful next to the squad it replaces.** The solver has answered *"the best
/// fifteen within a budget"* since ADR-013, and on its own that is a list of names you then diff against
/// your own team in your head. ⚠️ *The comparison is the product; the squad is the input to it.*
///
/// ⚠️⚠️ **"Apply" does not touch FPL, and cannot.** There is no write API and there will not be one — so
/// applying makes this **your plan in this app**, which the pitch then draws and which survives closing
/// the app (ADR-225/260). ⭐ *The real move still happens in the FPL app, and pretending otherwise would
/// be the worst lie this screen could tell.*
///
/// 📌 **No pitch here, deliberately.** `PitchView` needs a real `MyTeam` — kits, fixtures, price moves,
/// a deadline — and a built squad has none of them. ⭐ *A second pitch drawn from thinner data would be a
/// worse pitch*, and applying the draft puts these fifteen on the real one.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'pill.dart';

/// What the Lab is being asked to do. ⭐ Each mode is a **budget and a horizon**, not a new feature.
enum LabMode { wildcard, freeHit, freshSeason }

extension LabModeDetail on LabMode {
  String get label => switch (this) {
    LabMode.wildcard => 'Wildcard',
    LabMode.freeHit => 'Free Hit',
    LabMode.freshSeason => 'New season',
  };

  /// ⚠️ **The horizon is the point of the mode.** A wildcard is played for a **run**; a free hit is
  /// played for **one week**, and asking the solver for a run would give a different fifteen.
  int get horizon => switch (this) {
    LabMode.wildcard => 5,
    LabMode.freeHit => 1,
    LabMode.freshSeason => 5,
  };

  /// ⭐ A new season starts from FPL's £100.0m, not from what you own — *that is the whole point of the
  /// mode.* The other two spend your team value.
  bool get fromScratch => this == LabMode.freshSeason;

  String get note => switch (this) {
    LabMode.wildcard => 'Your fifteen, rebuilt for the next five gameweeks.',
    LabMode.freeHit =>
      'One week only — picked for this gameweek and nothing after it.',
    LabMode.freshSeason =>
      'From £100.0m and nothing owned, the way a season starts.',
  };
}

/// ⭐⭐ **How the solver values the bench** (ADR-045). Not a preference — two genuinely different squads.
enum BuildStyle { strongXi, strongFifteen }

extension BuildStyleDetail on BuildStyle {
  String get label => switch (this) {
    // ⭐ **One numbering.** "Strong XI" beside "Strong 15" mixed Roman and Arabic inside a single
    // control — ⚠️ *two ways of writing a number in one control reads as two kinds of thing.* Arabic,
    // because it is how FPL managers talk: *"all 15 score on a Bench Boost."*
    BuildStyle.strongXi => 'Strong 11',
    BuildStyle.strongFifteen => 'Strong 15',
  };

  /// `0.1` spends almost everything on the eleven and buys a cheap bench that plays; `1.0` values all
  /// fifteen equally, which is what a **Bench Boost** week actually asks for.
  double get benchWeight => switch (this) {
    BuildStyle.strongXi => 0.1,
    BuildStyle.strongFifteen => 1.0,
  };

  String get note => switch (this) {
    BuildStyle.strongXi =>
      'Money on the eleven, a cheap bench that still plays.',
    BuildStyle.strongFifteen =>
      'All fifteen count — the shape for a Bench Boost.',
  };
}

class LabView extends StatefulWidget {
  const LabView({
    required this.client,
    required this.team,
    required this.onApply,
    super.key,
  });

  final ServiceClient client;
  final MyTeam team;

  /// Make this squad the plan. ⚠️ *Not* a transfer — see the library note.
  final Future<void> Function(BuildAnswer squad, String name) onApply;

  @override
  State<LabView> createState() => _LabViewState();
}

class _LabViewState extends State<LabView> {
  LabMode _mode = LabMode.wildcard;
  BuildStyle _style = BuildStyle.strongXi;
  final Set<int> _keep = {};

  /// ⭐ Players sent away by **"Replace him"** — the solver must find someone else.
  final Set<int> _drop = {};

  final TextEditingController _name = TextEditingController();
  Future<BuildAnswer>? _draft;
  BuildAnswer? _built;
  bool _applied = false;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  List<PlayerSummary> get _mine => [
    ...widget.team.analysis.xi,
    ...widget.team.analysis.bench,
  ];

  /// ⭐⭐ **FPL's team value already includes the bank**, which is exactly what a wildcard has to spend.
  ///
  /// ⚠️ It is not the sum of what the fifteen are worth today: FPL sells a risen player for less than
  /// his current price, and ⭐ *a budget built by adding up current prices would be optimistic by exactly
  /// the amount a manager has earned* — the direction that invents money.
  double? get _budget => _mode.fromScratch ? 100.0 : widget.team.value;

  void _run({Set<int>? keep, Set<int>? drop}) {
    final budget = _budget;
    if (budget == null) return;
    setState(() {
      _applied = false;
      _draft = widget.client
          .build(
            budget: budget,
            horizon: _mode.horizon,
            includeIds: (keep ?? _keep).toList(),
            excludeIds: (drop ?? _drop).toList(),
            benchWeight: _style.benchWeight,
          )
          .then((answer) {
            _built = answer;
            return answer;
          });
    });
  }

  /// Send one player away and rebuild around the rest.
  ///
  /// ⭐⭐ **The other fourteen are forced in**, so the solver replaces exactly one — ⚠️ *and the budget
  /// stays honest without the screen doing any arithmetic*, which a hand-rolled swap list would have had
  /// to get right on its own.
  void _replace(BuiltPlayer player) {
    final built = _built;
    if (built == null) return;
    final keep = {
      for (final b in built.selected)
        if (b.player.id != player.player.id) b.player.id,
    };
    _keep
      ..clear()
      ..addAll(keep);
    _drop.add(player.player.id);
    _run();
  }

  void _reset() {
    setState(() {
      _keep.clear();
      _drop.clear();
      _draft = null;
      _built = null;
      _applied = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final budget = _budget;
    if (budget == null) {
      return const _Note(
        'Your team value has not loaded, so there is no budget to build against. Open My Team first.',
      );
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 24),
      children: [
        PillRow(
          children: [
            for (final mode in LabMode.values)
              Pill(
                label: mode.label,
                selected: _mode == mode,
                onTap: () {
                  setState(() => _mode = mode);
                  _reset();
                },
              ),
          ],
        ),
        const SizedBox(height: 6),
        // ⭐ A **toggle**, not a second row of pills: the build style modifies the mode above it, and
        // ⚠️ *a control's size is a claim about its importance.*
        MiniToggle(
          label: 'Bench',
          options: [for (final s in BuildStyle.values) s.label],
          selected: _style.label,
          onPick: (label) {
            final style = BuildStyle.values.firstWhere((s) => s.label == label);
            setState(() => _style = style);
            if (_built != null) _run();
          },
        ),
        const SizedBox(height: 10),
        _Header(mode: _mode, style: _style, budget: budget),
        const SizedBox(height: 12),
        if (!_mode.fromScratch) ...[
          const Text(
            // ⭐ Says what tapping does before anything is tapped — the interaction is not guessable
            // from a grid of names. ⚠️ **In orange** (owner's call): grey made it read as a caption
            // under the card above, and *an instruction that looks like a footnote gets skipped.*
            'Tap anyone you want to keep. The rest is rebuilt around them.',
            style: TextStyle(
              color: Brand.orange,
              fontSize: 11.5,
              height: 1.5,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          _KeepGrid(
            players: _mine,
            keep: _keep,
            onToggle: (id) => setState(() {
              if (!_keep.remove(id)) _keep.add(id);
              // ⚠️ The draft is cleared, never left standing. ⭐ *A result that no longer matches the
              // question above it is worse than no result*, because it still looks like an answer.
              _draft = null;
              _built = null;
              _applied = false;
            }),
          ),
          const SizedBox(height: 12),
        ],
        Row(
          children: [
            Expanded(
              child: TextButton(
                onPressed: () => _run(),
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
            if (_keep.isNotEmpty || _drop.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(left: 8),
                child: TextButton(
                  onPressed: _reset,
                  child: const Text('Reset'),
                ),
              ),
          ],
        ),
        if (_drop.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              // ⚠️ Stated, because an exclusion the reader has forgotten about looks like the solver
              // making an odd choice.
              '${_drop.length} player${_drop.length == 1 ? '' : 's'} sent away — Reset brings them back.',
              style: const TextStyle(color: Colors.white38, fontSize: 11),
            ),
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
                return _Draft(
                  answer: snapshot.data!,
                  mine: _mine,
                  mode: _mode,
                  name: _name,
                  applied: _applied,
                  onReplace: _replace,
                  onApply: () async {
                    await widget.onApply(snapshot.data!, _name.text.trim());
                    if (mounted) setState(() => _applied = true);
                  },
                );
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
    required this.style,
    required this.budget,
  });

  final LabMode mode;
  final BuildStyle style;
  final double budget;

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
          '${mode.note}  ${style.note}',
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 11,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          mode.fromScratch
              // ⚠️⚠️ **The budget is FPL's team value, built from SELLING prices.** Saying so matters: a
              // manager comparing it against the prices on the pitch will find they do not add up, and
              // ⭐ *an unexplained number that disagrees with another number on the same app is a bug
              // report.*
              ? 'Nothing here changes your real team.'
              : 'That is your FPL team value — the bank plus what your fifteen would sell for. '
                    'Nothing here changes your real team.',
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 10.5,
            height: 1.45,
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

/// `3-4-3` — ⭐ **the shape, which a list of names does not show** and a wildcard very often changes.
String formationOf(BuildAnswer answer) {
  final counts = <String, int>{};
  for (final b in answer.xi) {
    counts[b.player.position] = (counts[b.player.position] ?? 0) + 1;
  }
  return '${counts['DEF'] ?? 0}-${counts['MID'] ?? 0}-${counts['FWD'] ?? 0}';
}

class _Draft extends StatelessWidget {
  const _Draft({
    required this.answer,
    required this.mine,
    required this.mode,
    required this.name,
    required this.applied,
    required this.onReplace,
    required this.onApply,
  });

  final BuildAnswer answer;
  final List<PlayerSummary> mine;
  final LabMode mode;
  final TextEditingController name;
  final bool applied;
  final ValueChanged<BuiltPlayer> onReplace;
  final Future<void> Function() onApply;

  @override
  Widget build(BuildContext context) {
    // ⚠️⚠️ **"Infeasible" is an answer, and it is not an empty squad.** Rendering fifteen blank rows
    // under a heading is how *"your constraints cannot be met"* gets read as *"there are no good
    // players"*.
    if (!answer.solved) {
      return const _Note(
        'No legal fifteen fits that. Keeping several expensive players — or sending too many away — '
        'leaves too little for the rest. Release one and try again.',
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
              unit: mode.horizon == 1 ? 'xP this GW' : 'xP over 5 GWs',
            ),
            _Stat(
              label: 'Spent',
              value: '£${answer.totalCost.toStringAsFixed(1)}m',
              unit: 'of £${answer.budget.toStringAsFixed(1)}m',
            ),
            _Stat(
              label: 'Shape',
              value: formationOf(answer),
              unit: '${diff.out.length} out',
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (diff.out.isEmpty)
          const Text(
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
        const Text(
          'The eleven it would start  ·  tap anyone to replace him',
          style: TextStyle(
            color: Colors.white54,
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        for (final b in answer.xi) _DraftRow(built: b, onReplace: onReplace),
        const SizedBox(height: 10),
        const Text(
          // ⚠️ Named as the solver's bench, because it is not ordered the way FPL substitutes.
          'Bench (not in substitution order)',
          style: TextStyle(color: Colors.white38, fontSize: 11),
        ),
        const SizedBox(height: 6),
        for (final b in answer.bench) _DraftRow(built: b, onReplace: onReplace),
        const SizedBox(height: 16),
        TextField(
          controller: name,
          style: const TextStyle(color: Colors.white, fontSize: 13.5),
          decoration: InputDecoration(
            isDense: true,
            // ⭐ Optional, and labelled by what it buys: two drafts for the same fifteen are different
            // plans, and a screen showing one of them with no name cannot say which.
            hintText: 'Name this squad (optional) — e.g. “${mode.label} plan”',
            hintStyle: const TextStyle(color: Colors.white24, fontSize: 12.5),
            filled: true,
            fillColor: Colors.white10,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(Brand.radiusSm),
              borderSide: BorderSide.none,
            ),
          ),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: applied ? null : onApply,
          style: TextButton.styleFrom(
            backgroundColor: applied ? Colors.white10 : Brand.good,
            foregroundColor: Colors.white,
            disabledForegroundColor: Brand.good,
            padding: const EdgeInsets.symmetric(vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(Brand.radiusSm),
            ),
          ),
          child: Text(
            applied ? '✓ This is your plan' : 'Make this my plan',
            style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700),
          ),
        ),
        const Padding(
          padding: EdgeInsets.only(top: 8),
          child: Text(
            // ⚠️⚠️ **The one thing this screen must never imply.** FPL has no write API: applying makes
            // it your plan here, and the transfers still have to be made in the FPL app.
            'This becomes your plan in MADBOOTS — the pitch will show it, and it survives closing the '
            'app. It does not make the transfers: FPL has no way to accept them from us.',
            style: TextStyle(
              color: Colors.white38,
              fontSize: 10.5,
              height: 1.5,
            ),
          ),
        ),
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
  const _DraftRow({required this.built, required this.onReplace});

  final BuiltPlayer built;
  final ValueChanged<BuiltPlayer> onReplace;

  @override
  Widget build(BuildContext context) {
    final p = built.player;
    return InkWell(
      onTap: () => onReplace(built),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
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
