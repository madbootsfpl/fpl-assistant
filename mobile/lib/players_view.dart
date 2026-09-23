/// Players — the market (ADR-230).
///
/// ⭐⭐ **Fetched once, filtered on the device.** The whole ranked market is ~95 KB and searching 481 rows
/// locally is instant; a round trip per keystroke is not. *The cheap thing sent once beats the small thing
/// sent constantly* — which is the same payload reasoning spike 017 used to make this client's whole
/// architecture.
///
/// ⚠️ **Players who cannot play are already gone** — the server excludes them, because a browse list is
/// for finding someone to buy. Doubtful players stay and are flagged: a doubt is a probability, not a
/// verdict (ADR-206).
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'boot_battle.dart';
import 'brand.dart';
import 'mugshot.dart';
import 'player_picker.dart';

const List<String> _positions = ['GK', 'DEF', 'MID', 'FWD'];

/// ⭐ Round numbers a manager already thinks in. FPL prices sit between £3.8m and about £15m, and nobody
/// has ever wanted "under £7.3m" — the budget in someone's head is a whole million.
const List<double> _priceSteps = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0];

class PlayersView extends StatefulWidget {
  const PlayersView({required this.client, required this.owned, super.key});

  final ServiceClient client;

  /// ⭐ Ids you already hold, so the list can say so. A market list that does not know what you own makes
  /// you check your own pitch to read it.
  final Set<int> owned;

  @override
  State<PlayersView> createState() => _PlayersViewState();
}

class _PlayersViewState extends State<PlayersView> {
  late final Future<List<PlayerSummary>> _all = widget.client.players(
    horizon: 5,
  );
  final TextEditingController _search = TextEditingController();
  String? _position;

  /// ⭐⭐ **The filter that could not be chips is exactly the one worth showing a value for.** Position has
  /// five options and they all fit, so highlighting one of five already says what is on. Price has sixty,
  /// so it has to hide behind a tap — and the moment a filter is hidden, the chip has to *say* what it is
  /// set to or the list is silently lying about being the whole market.
  double? _maxPrice;

  /// ⭐⭐ **Progressive disclosure** (ADR-257) — the pattern the owner liked in the competitor's custom
  /// transfers. A row showing every filter it *could* apply spends its width on questions nobody asked;
  /// one showing only the filters in play, plus a way to add another, spends it on answers.
  ///
  /// ⚠️ Position and price are deliberately **not** behind it: they were already visible and already
  /// used. *Hiding a filter people reach for is not disclosure, it is a tax.*
  double? _minXp;
  String? _club;

  /// ⭐ **"Show me mine"** (feedback item 5). The board is 481 players and fifteen of them are the ones a
  /// manager keeps coming back to — to check a price, a run, a flag. Without this, finding your own player
  /// meant typing his name into a search box that already knows who you own.
  bool _mineOnly = false;

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  List<PlayerSummary> _filtered(List<PlayerSummary> all) {
    final term = _search.text.trim().toLowerCase();
    return all.where((p) {
      if (_position != null && p.position != _position) return false;
      if (_maxPrice != null && p.price > _maxPrice!) return false;
      if (_mineOnly && !widget.owned.contains(p.id)) return false;
      if (_minXp != null && p.xp < _minXp!) return false;
      if (_club != null && p.team != _club) return false;
      if (term.isEmpty) return true;
      // ⭐ Name **or** club: "ars" should find Arsenal's players, which is how a manager actually looks.
      return p.name.toLowerCase().contains(term) ||
          p.team.toLowerCase().contains(term);
    }).toList();
  }

  List<String> _activeFilters() {
    final term = _search.text.trim();
    return [
      if (term.isNotEmpty) '“$term”',
      ?_position,
      if (_maxPrice != null) 'under £${_maxPrice!.toStringAsFixed(1)}m',
      if (_mineOnly) 'your squad',
      if (_minXp != null) '${_minXp!.toStringAsFixed(0)}+ xP',
      ?_club,
    ];
  }

  /// ⭐ The clubs actually on the board, not a hard-coded twenty — a promoted side appears without a
  /// release, and the filter can never offer a club with nobody in it.
  List<String> _clubsIn(List<PlayerSummary> all) =>
      all.map((p) => p.team).toSet().toList()..sort();

  Future<void> _pickPrice() async {
    final picked = await showModalBottomSheet<double?>(
      context: context,
      backgroundColor: Brand.ink,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 16, 20, 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Most I want to spend',
                  style: TextStyle(color: Colors.white, fontSize: 14.5),
                ),
              ),
            ),
            // ⚠️⚠️ **Scrollable, and not for tidiness.** A bottom sheet is capped at a fraction of the
            // screen; eight options in a fixed `Column` fit a tall phone and are **clipped** on a short
            // one — and the rows that fall off the bottom are the expensive ones, so the filter would
            // quietly lose "under £12.0m" for exactly the managers browsing premiums. ⭐ *Found by a
            // widget test running at 800×600, which is smaller than the phone I had been picturing.*
            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
                  // ⚠️ `null` is a legitimate answer here, so the sheet cannot distinguish "chose any
                  // price" from "dismissed" by the popped value alone — hence the sentinel.
                  _PriceOption(
                    label: 'Any price',
                    on: _maxPrice == null,
                    value: -1,
                  ),
                  for (final step in _priceSteps)
                    _PriceOption(
                      label: 'Under £${step.toStringAsFixed(1)}m',
                      on: _maxPrice == step,
                      value: step,
                    ),
                ],
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
    if (picked == null) return; // dismissed
    setState(() => _maxPrice = picked < 0 ? null : picked);
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<PlayerSummary>>(
    future: _all,
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
      final all = snapshot.data!;
      final shown = _filtered(all);

      return Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 8, 14, 4),
            child: TextField(
              controller: _search,
              onChanged: (_) => setState(() {}),
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Search a player or club',
                hintStyle: const TextStyle(
                  color: Colors.white38,
                  fontSize: 13.5,
                ),
                prefixIcon: const Icon(
                  Icons.search,
                  size: 18,
                  color: Colors.white38,
                ),
                isDense: true,
                filled: true,
                fillColor: Colors.white10,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(Brand.radiusSm),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          SizedBox(
            height: 38,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              children: [
                // ⚠️ Disabled rather than hidden when the caller passes no squad — a chip that vanishes
                // looks like a bug; one that is visibly unavailable looks like a state.
                _Chip(
                  label: 'My squad',
                  on: _mineOnly,
                  onTap: widget.owned.isEmpty
                      ? null
                      : () => setState(() => _mineOnly = !_mineOnly),
                ),
                const _Divider(),
                _Chip(
                  label: 'All',
                  on: _position == null,
                  onTap: () => setState(() => _position = null),
                ),
                for (final pos in _positions)
                  _Chip(
                    label: pos,
                    on: _position == pos,
                    onTap: () => setState(() => _position = pos),
                  ),
                const _Divider(),
                if (_minXp != null)
                  _ValueChip(
                    label: 'xP',
                    value: '${_minXp!.toStringAsFixed(0)}+',
                    on: true,
                    // ⚠️ Tapping the chip **removes** it. A separate ✕ would be a second control for one
                    // idea, and at this size a target nobody hits.
                    onTap: () => setState(() => _minXp = null),
                  ),
                if (_club != null)
                  _ValueChip(
                    label: 'Club',
                    value: _club!,
                    on: true,
                    onTap: () => setState(() => _club = null),
                  ),
                _AddFilter(
                  clubs: _clubsIn(all),
                  hasXp: _minXp != null,
                  hasClub: _club != null,
                  onXp: (v) => setState(() => _minXp = v),
                  onClub: (c) => setState(() => _club = c),
                ),
                _ValueChip(
                  label: 'Price',
                  // ⭐ It reads as a sentence either way — `Price: any` is a statement about the list,
                  // not an invitation. A chip that only ever showed `Price` would leave a reader who
                  // set it yesterday unable to tell what they are looking at.
                  value: _maxPrice == null
                      ? 'any'
                      : 'under £${_maxPrice!.toStringAsFixed(1)}m',
                  on: _maxPrice != null,
                  onTap: _pickPrice,
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 2, 16, 6),
            child: Row(
              children: [
                Text(
                  // ⭐ "of" matters: the list is filtered, and a bare count implies it is everyone.
                  shown.length == all.length
                      ? '${all.length} players, best first'
                      : '${shown.length} of ${all.length}',
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
                const Spacer(),
                const Text(
                  'xP over 5 GW',
                  style: TextStyle(color: Colors.white24, fontSize: 10.5),
                ),
              ],
            ),
          ),
          Expanded(
            child: shown.isEmpty
                ? Center(
                    // ⭐ An empty list is caused by the filters, so it should name the ones that are
                    // on. "Nobody matches that" makes a reader hunt for what "that" was.
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 32),
                      child: Text(
                        'Nobody matches ${_activeFilters().join(' + ')}.',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Colors.white38,
                          height: 1.5,
                        ),
                      ),
                    ),
                  )
                : ListView.builder(
                    itemCount: shown.length,
                    itemBuilder: (_, i) => _Row(
                      player: shown[i],
                      owned: widget.owned.contains(shown[i].id),
                      client: widget.client,
                      // ⭐ The filtered list, minus himself, same position only.
                      rivals: [
                        for (final p in shown)
                          if (p.id != shown[i].id &&
                              p.position == shown[i].position)
                            p,
                      ],
                    ),
                  ),
          ),
        ],
      );
    },
  );
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label, required this.on, required this.onTap});

  final String label;
  final bool on;

  /// ⭐ Null means *there is nothing to filter to* — the chip renders dimmed and ignores taps.
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    behavior: HitTestBehavior.opaque,
    child: Container(
      margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 5),
      padding: const EdgeInsets.symmetric(horizontal: 14),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: onTap == null
            ? Colors.white10
            : on
            ? Brand.purple
            : Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusPill),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: onTap == null
              ? Colors.white24
              : on
              ? Colors.white
              : Colors.white54,
          fontSize: 12.5,
          fontWeight: on ? FontWeight.w600 : FontWeight.w400,
        ),
      ),
    ),
  );
}

/// ⭐⭐ **The card opens where the row is.** The Hub does this and it is the right shape: a list you can
/// interrogate without leaving it beats a list that sends you somewhere and loses your place in it.
///
/// ⚠️ The detail is fetched **on expand**, never with the list.
class _Row extends StatefulWidget {
  const _Row({
    required this.player,
    required this.owned,
    required this.client,
    required this.rivals,
  });

  final PlayerSummary player;
  final bool owned;
  final ServiceClient client;

  /// ⭐⭐ **Who he can be compared with** — the *currently filtered* list, same position only.
  ///
  /// ⭐ That the filters narrow it is the point: `MID · under £8.0m · BHA` is how you find the two players
  /// worth putting side by side, so the filter row earns its keep twice. ⚠️ Same position is the engine's
  /// rule, not a simplification — *a comparison across positions ranks them on stats that do not mean the
  /// same thing*, and `compare` refuses it.
  final List<PlayerSummary> rivals;

  @override
  State<_Row> createState() => _RowState();
}

class _RowState extends State<_Row> {
  Future<PlayerCard>? _card;

  /// ⭐ Boot Battle, from the list — the last piece the audit's §6 *"search, compare, the card"* was
  /// missing (ADR-257). It has existed since ADR-236 and could only be reached from the transfer flow,
  /// which answers *"who should replace him?"* — a different question from *"which of these two?"*.
  void _battle(BuildContext context, PlayerSummary other) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => Scaffold(
          backgroundColor: Brand.ink,
          appBar: AppBar(
            // ⭐ The brand's word, not a description of it (ADR-258). The names are on the card below,
            // in their own colours — repeating them in the bar spends the title on something already said.
            title: const Text('Boot Battle'),
            backgroundColor: Brand.ink,
            foregroundColor: Colors.white,
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
            child: BootBattleView(
              future: widget.client.compare(widget.player.id, other.id),
            ),
          ),
        ),
      ),
    );
  }

  void _toggle() => setState(() {
    _card = _card == null
        ? widget.client.player(widget.player.id, horizon: 5)
        : null;
  });

  @override
  Widget build(BuildContext context) {
    final player = widget.player;
    final owned = widget.owned;
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.white10)),
      ),
      child: Column(
        children: [
          GestureDetector(
            onTap: _toggle,
            behavior: HitTestBehavior.opaque,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 9, 16, 9),
              child: Row(
                children: [
                  SizedBox(
                    width: 34,
                    child: Text(
                      player.position,
                      style: const TextStyle(
                        color: Colors.white38,
                        fontSize: 11,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Row(
                      children: [
                        Flexible(
                          child: Text(
                            player.name,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                            ),
                          ),
                        ),
                        if (owned)
                          // ⭐ A market list that does not know what you own makes you check your own pitch to
                          // read it.
                          Container(
                            margin: const EdgeInsets.only(left: 6),
                            padding: const EdgeInsets.symmetric(horizontal: 6),
                            decoration: BoxDecoration(
                              color: Brand.goodTint,
                              borderRadius: BorderRadius.circular(
                                Brand.radiusPill,
                              ),
                            ),
                            child: const Text(
                              'owned',
                              style: TextStyle(
                                color: Brand.goodFg,
                                fontSize: 9,
                              ),
                            ),
                          ),
                        if (player.isLeaving)
                          const Padding(
                            padding: EdgeInsets.only(left: 5),
                            child: Text(
                              '✈',
                              style: TextStyle(color: Brand.bad, fontSize: 11),
                            ),
                          )
                        else if (player.isDoubtful)
                          Padding(
                            padding: const EdgeInsets.only(left: 5),
                            child: Text(
                              '${player.chance ?? '?'}%',
                              style: const TextStyle(
                                color: Brand.warn,
                                fontSize: 10,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  SizedBox(
                    width: 42,
                    child: Text(
                      player.team,
                      style: const TextStyle(
                        color: Colors.white38,
                        fontSize: 11,
                      ),
                    ),
                  ),
                  SizedBox(
                    width: 48,
                    child: Text(
                      '£${player.price.toStringAsFixed(1)}',
                      textAlign: TextAlign.right,
                      style: const TextStyle(
                        color: Colors.white60,
                        fontSize: 12.5,
                      ),
                    ),
                  ),
                  SizedBox(
                    width: 52,
                    child: Text(
                      player.xp.toStringAsFixed(1),
                      textAlign: TextAlign.right,
                      style: const TextStyle(
                        color: Brand.accentTeal,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  Icon(
                    _card == null ? Icons.expand_more : Icons.expand_less,
                    size: 16,
                    color: Colors.white24,
                  ),
                ],
              ),
            ),
          ),
          if (_card != null)
            _Card(
              future: _card!,
              rivals: widget.rivals,
              onCompare: (other) => _battle(context, other),
            ),
        ],
      ),
    );
  }
}

/// The expanded detail. ⭐ Three blocks — the season, the recent past, the projected run — because those
/// are the three different questions a reader has about a name on a list.
class _Card extends StatelessWidget {
  const _Card({
    required this.future,
    required this.rivals,
    required this.onCompare,
  });

  final Future<PlayerCard> future;
  final List<PlayerSummary> rivals;
  final void Function(PlayerSummary) onCompare;

  @override
  Widget build(BuildContext context) => FutureBuilder<PlayerCard>(
    future: future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Padding(
          padding: EdgeInsets.symmetric(vertical: 18),
          child: Center(
            child: SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ),
        );
      }
      if (snapshot.hasError) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: Text(
            friendlyError(snapshot.error),
            style: const TextStyle(
              color: Colors.white54,
              fontSize: 11,
              height: 1.45,
            ),
          ),
        );
      }
      final card = snapshot.data!;
      return Container(
        width: double.infinity,
        color: Colors.white.withValues(alpha: 0.03),
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ⭐ The run first: a reader opening a row is usually asking *"is he good, or is this an
            // easy month?"*, and the fixtures are half that answer.
            const Text(
              'NEXT',
              style: TextStyle(
                color: Colors.white24,
                fontSize: 9,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                for (final f in card.fixtures)
                  Expanded(
                    child: Container(
                      margin: const EdgeInsets.only(right: 3),
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        // ⭐ Difficulty colours the FIXTURE, not the player — which is the distinction
                        // ADR-179 protects: a hue about the opponent, beside a number about the player.
                        color:
                            Brand.fdr[f.difficulty]?.background ??
                            Colors.white10,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        '${f.opponent} (${f.venue})',
                        style: TextStyle(
                          color:
                              Brand.fdr[f.difficulty]?.foreground ??
                              Colors.white54,
                          fontSize: 9,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            // ⭐ Beside the fixtures, not above them: the face identifies, the numbers decide, and the
            // decision should not have to scroll past the identification.
            if (card.photo.isNotEmpty || card.player.name.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Mugshot(url: card.photo, name: card.player.name),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            card.player.name,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            '${card.player.position} · ${card.player.team} · '
                            '£${card.player.price.toStringAsFixed(1)}m',
                            style: const TextStyle(
                              color: Colors.white38,
                              fontSize: 11.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            // ⭐⭐ **The last piece of audit §6** — *search, compare, the card* (ADR-257). Boot Battle has
            // existed since ADR-236 and could only be reached from the transfer flow, which answers *"who
            // should replace him?"*. ⚠️ *That is a different question from "which of these two?"*, and the
            // second one is what a browse list is for.
            if (rivals.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton.icon(
                    onPressed: () => _pick(context, card.player),
                    icon: const Icon(Icons.sports_mma_outlined, size: 16),
                    // ⚠️ *A feature with two names is two features to anyone who has to be told which is
                    // which* — the desktop has called this **Boot Battle** since the wave-3 feedback.
                    label: Text('Boot Battle — one of ${rivals.length}'),
                    style: TextButton.styleFrom(
                      foregroundColor: Brand.purpleLight,
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      minimumSize: const Size(0, 32),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      backgroundColor: Brand.purple.withValues(alpha: 0.18),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(Brand.radiusSm),
                      ),
                    ),
                  ),
                ),
              ),
            if (card.recent.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                // ⚠️⚠️ **It said "LAST 5" over four boxes** and the owner reasonably read that as a
                // missing gameweek. It was not — early in a season, or for a player who joined late,
                // there simply are not five. ⭐ *A heading that names a number it is not showing turns a
                // correct screen into a bug report* — and it hid a real one underneath, because the fifth
                // gameweek genuinely was missing from the database.
                card.recent.length >= 5
                    ? 'LAST 5'
                    : 'LAST ${card.recent.length}',
                style: const TextStyle(
                  color: Colors.white24,
                  fontSize: 9,
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  for (final g in card.recent)
                    Expanded(
                      child: Container(
                        margin: const EdgeInsets.only(right: 3),
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: Colors.white10,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Column(
                          children: [
                            Text(
                              '${g.points}',
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            Text(
                              "${g.minutes}'",
                              style: const TextStyle(
                                color: Colors.white24,
                                fontSize: 7.5,
                              ),
                            ),
                            Text(
                              g.versus,
                              maxLines: 1,
                              overflow: TextOverflow.clip,
                              style: const TextStyle(
                                color: Colors.white38,
                                fontSize: 7.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ],
            const SizedBox(height: 10),
            // ⭐ Two columns, because twelve stats in one list is a wall a reader scrolls past.
            Wrap(
              spacing: 18,
              runSpacing: 3,
              children: [
                for (final stat in card.stats)
                  SizedBox(
                    width: 150,
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            stat.label,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Colors.white38,
                              fontSize: 10.5,
                            ),
                          ),
                        ),
                        Text(
                          stat.value,
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ],
        ),
      );
    },
  );
}

/// A filter that **states what it is set to**, not what it could be set to (ADR-238).
///
/// ⭐⭐ Worth it precisely where [_Chip] is not: when the options do not fit on the row, the only place the
/// current setting can live is on the chip itself.
class _ValueChip extends StatelessWidget {
  const _ValueChip({
    required this.label,
    required this.value,
    required this.on,
    required this.onTap,
  });

  final String label;
  final String value;
  final bool on;

  /// ⭐ Null means *there is nothing to filter to* — the chip renders dimmed and ignores taps.
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    behavior: HitTestBehavior.opaque,
    child: Container(
      margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 5),
      padding: const EdgeInsets.only(left: 14, right: 8),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: on ? Brand.purple : Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusPill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: '$label: ',
                  style: TextStyle(color: on ? Colors.white70 : Colors.white38),
                ),
                TextSpan(
                  text: value,
                  style: TextStyle(
                    color: on ? Colors.white : Colors.white70,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            style: const TextStyle(fontSize: 12.5),
          ),
          Icon(
            Icons.arrow_drop_down,
            size: 17,
            color: on ? Colors.white70 : Colors.white38,
          ),
        ],
      ),
    ),
  );
}

/// ⭐ A hairline between the filters that show their options and the ones that show their value — without
/// it the row reads as one long list of positions with a stray price on the end.
class _Divider extends StatelessWidget {
  const _Divider();

  @override
  Widget build(BuildContext context) => Container(
    width: 1,
    height: 16,
    margin: const EdgeInsets.symmetric(horizontal: 7, vertical: 11),
    color: Colors.white12,
  );
}

class _PriceOption extends StatelessWidget {
  const _PriceOption({
    required this.label,
    required this.on,
    required this.value,
  });

  final String label;
  final bool on;

  /// ⚠️ **-1 means "any"**, because `Navigator.pop(context, null)` is indistinguishable from a dismissal.
  final double value;

  @override
  Widget build(BuildContext context) => ListTile(
    dense: true,
    title: Text(
      label,
      style: TextStyle(
        color: on ? Brand.purpleLight : Colors.white70,
        fontSize: 13.5,
        fontWeight: on ? FontWeight.w600 : FontWeight.normal,
      ),
    ),
    trailing: on
        ? const Icon(Icons.check, size: 17, color: Brand.purpleLight)
        : null,
    onTap: () => Navigator.of(context).pop(value),
  );
}

/// *"Add filter"* — ⭐⭐ **the row shows what is in play, not everything that could be** (ADR-257).
///
/// ⚠️ An added filter becomes a chip that states its value, and **tapping that chip removes it**. A
/// separate ✕ would be a second control for one idea, and at this size a target nobody hits.
class _AddFilter extends StatelessWidget {
  const _AddFilter({
    required this.clubs,
    required this.hasXp,
    required this.hasClub,
    required this.onXp,
    required this.onClub,
  });

  final List<String> clubs;
  final bool hasXp;
  final bool hasClub;
  final ValueChanged<double> onXp;
  final ValueChanged<String> onClub;

  @override
  Widget build(BuildContext context) {
    // ⭐ Gone entirely when there is nothing left to add — *a button that can only disappoint should
    // disappear.*
    if (hasXp && hasClub) return const SizedBox.shrink();
    return GestureDetector(
      onTap: () => _open(context),
      behavior: HitTestBehavior.opaque,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 5),
        padding: const EdgeInsets.only(left: 10, right: 12),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          border: Border.all(color: Colors.white24),
          borderRadius: BorderRadius.circular(Brand.radiusPill),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.add, size: 13, color: Colors.white54),
            SizedBox(width: 3),
            Text(
              'Filter',
              style: TextStyle(color: Colors.white54, fontSize: 12.5),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _open(BuildContext context) => showModalBottomSheet<void>(
    context: context,
    backgroundColor: Brand.ink,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (sheet) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 16, 20, 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Add a filter',
                style: TextStyle(color: Colors.white, fontSize: 14.5),
              ),
            ),
          ),
          // ⚠️ Only what is not already on. A menu offering a filter you are using would be a menu that
          // has not looked at the screen behind it.
          if (!hasXp)
            _Option(
              icon: Icons.trending_up,
              title: 'Minimum xP',
              why: 'Hide anyone projected below a threshold',
              onTap: () async {
                Navigator.of(sheet).pop();
                final picked = await _pickNumber(context);
                if (picked != null) onXp(picked);
              },
            ),
          if (!hasClub)
            _Option(
              icon: Icons.shield_outlined,
              title: 'Club',
              why: 'One side only',
              onTap: () async {
                Navigator.of(sheet).pop();
                final picked = await _pickClub(context);
                if (picked != null) onClub(picked);
              },
            ),
          const SizedBox(height: 8),
        ],
      ),
    ),
  );

  Future<double?> _pickNumber(BuildContext context) =>
      showModalBottomSheet<double>(
        context: context,
        backgroundColor: Brand.ink,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        builder: (sheet) => SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final step in const [2.0, 3.0, 4.0, 5.0, 6.0])
                ListTile(
                  dense: true,
                  title: Text(
                    '${step.toStringAsFixed(0)} xP or more',
                    style: const TextStyle(color: Colors.white, fontSize: 13.5),
                  ),
                  onTap: () => Navigator.of(sheet).pop(step),
                ),
            ],
          ),
        ),
      );

  Future<String?> _pickClub(BuildContext context) =>
      showModalBottomSheet<String>(
        context: context,
        backgroundColor: Brand.ink,
        isScrollControlled: true,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        builder: (sheet) => SafeArea(
          child: ListView(
            shrinkWrap: true,
            children: [
              for (final club in clubs)
                ListTile(
                  dense: true,
                  title: Text(
                    club,
                    style: const TextStyle(color: Colors.white, fontSize: 13.5),
                  ),
                  onTap: () => Navigator.of(sheet).pop(club),
                ),
            ],
          ),
        ),
      );
}

class _Option extends StatelessWidget {
  const _Option({
    required this.icon,
    required this.title,
    required this.why,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String why;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
    dense: true,
    leading: Icon(icon, size: 18, color: Brand.purpleLight),
    title: Text(
      title,
      style: const TextStyle(color: Colors.white, fontSize: 13.5),
    ),
    // ⭐ A line each, like the More directory: a menu of nouns makes you guess what they do.
    subtitle: Text(
      why,
      style: const TextStyle(color: Colors.white38, fontSize: 11),
    ),
    onTap: onTap,
  );
}

extension on _Card {
  /// Who to put him up against — ⭐ **the filtered list**, which is why the filter row is worth having.
  ///
  /// ⚠️ Same position only, and that is the **engine's** rule surfaced rather than a simplification:
  /// `compare` refuses a cross-position pairing because *"it ranks them on stats that do not mean the
  /// same thing"*. Offering one here would be offering an error.
  Future<void> _pick(BuildContext context, PlayerSummary subject) async {
    final chosen = await pickPlayer<PlayerSummary>(
      context,
      title: 'Boot Battle — ${subject.name} against…',
      // ⭐ Says why the list is what it is — otherwise "where is everyone?" is the first thought, and
      // the answer (your filters, and his position) is invisible.
      subtitle: 'Other ${subject.position}s in the list you are looking at.',
      items: rivals,
      of: (p) => p,
    );
    if (chosen != null) onCompare(chosen);
  }
}
