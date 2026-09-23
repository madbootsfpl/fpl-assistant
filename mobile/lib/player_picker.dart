/// One way to sift a long list of players, used everywhere a long list of players is offered (ADR-264).
///
/// ⭐⭐ **Two screens asked for the same thing, so they get one answer.** Boot Battle offered *"one of
/// 214"* as a flat list, and the transfer flow offered its candidates the same way — ⚠️ *a list nobody can
/// sift is a list nobody reads to the bottom of*, so both were really offering the top of the list.
///
/// ⚠️ **Deliberately not a second copy of the Players tab's filter row** (ADR-258). That row is for
/// *browsing* a market you are exploring; this is for *finding* someone in a list already narrowed by the
/// question you asked. ⭐ *Same widget, different job* would have been the mistake — and two hand-built
/// pickers that drift apart would have been the other one (ADR-184).
library;

import 'package:flutter/material.dart';

import 'api/models.dart';
import 'brand.dart';

/// How to order the list. ⭐ **xP first because it is the reason to be here**; the others are ways to find
/// a player you have already decided on.
enum PickerSort { xp, price, club, name }

extension PickerSortLabel on PickerSort {
  String get label => switch (this) {
    PickerSort.xp => 'xP',
    PickerSort.price => 'Price',
    PickerSort.club => 'Club',
    PickerSort.name => 'Name',
  };
}

/// The list as the reader asked for it: matching `query`, limited to `club`, in `sort` order.
///
/// ⭐ **Pure, because this is the part worth testing.** The sheet around it is layout; this is the
/// behaviour, and it can be mutation-tested without pumping a widget.
///
/// ⚠️ Search matches **name or club**, because *"spurs"* is how someone looks for a Spurs player whose
/// name they cannot spell — and matching only the name would answer "no such player".
List<T> siftPlayers<T>(
  List<T> items,
  PlayerSummary Function(T) of, {
  String query = '',
  String? club,
  PickerSort sort = PickerSort.xp,
}) {
  final term = query.trim().toLowerCase();
  final kept = [
    for (final item in items)
      if (club == null || of(item).team == club)
        if (term.isEmpty ||
            of(item).name.toLowerCase().contains(term) ||
            of(item).team.toLowerCase().contains(term))
          item,
  ];
  kept.sort(
    (a, b) => switch (sort) {
      // ⚠️ Descending for xP: the best is the one you want at the top. Ascending for price, because the
      // question a price sort answers is *"what can I afford?"*
      PickerSort.xp => of(b).xp.compareTo(of(a).xp),
      PickerSort.price => of(a).price.compareTo(of(b).price),
      PickerSort.club => of(a).team.compareTo(of(b).team),
      PickerSort.name => of(a).name.compareTo(of(b).name),
    },
  );
  return kept;
}

/// Every club present in the list — ⭐ *built from the list, so it can never offer one with nobody in it.*
List<String> clubsIn<T>(List<T> items, PlayerSummary Function(T) of) =>
    items.map(of).map((p) => p.team).toSet().toList()..sort();

/// Show the picker. Returns the chosen item, or `null` if the reader backed out.
Future<T?> pickPlayer<T>(
  BuildContext context, {
  required String title,
  required String subtitle,
  required List<T> items,
  required PlayerSummary Function(T) of,
  String Function(T)? detail,
}) => showModalBottomSheet<T>(
  context: context,
  backgroundColor: Brand.ink,
  isScrollControlled: true,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
  ),
  builder: (sheet) => _Picker<T>(
    title: title,
    subtitle: subtitle,
    items: items,
    of: of,
    detail: detail,
  ),
);

class _Picker<T> extends StatefulWidget {
  const _Picker({
    required this.title,
    required this.subtitle,
    required this.items,
    required this.of,
    this.detail,
  });

  final String title;
  final String subtitle;
  final List<T> items;
  final PlayerSummary Function(T) of;
  final String Function(T)? detail;

  @override
  State<_Picker<T>> createState() => _PickerState<T>();
}

class _PickerState<T> extends State<_Picker<T>> {
  final TextEditingController _search = TextEditingController();
  String? _club;
  PickerSort _sort = PickerSort.xp;

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final clubs = clubsIn(widget.items, widget.of);
    final shown = siftPlayers(
      widget.items,
      widget.of,
      query: _search.text,
      club: _club,
      sort: _sort,
    );

    return SafeArea(
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.85,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 10, 16, 0),
              child: Row(
                children: [
                  // ⭐ **An explicit way out** (feedback). A sheet dismisses by swiping down, which is
                  // discoverable only to people who already know it — ⚠️ *a gesture is not an
                  // affordance*, and changing your mind is the commonest thing a reader does here.
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.white70),
                    onPressed: () => Navigator.of(context).pop(),
                    tooltip: 'Back',
                  ),
                  Expanded(
                    child: Text(
                      widget.title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14.5,
                      ),
                    ),
                  ),
                  Text(
                    // ⭐ Says how much is left after filtering, so an empty list reads as *"your filters"*
                    // rather than *"no such player"*.
                    '${shown.length}',
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 12.5,
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
              child: Text(
                widget.subtitle,
                style: const TextStyle(color: Colors.white38, fontSize: 11),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              child: PickerControls(
                search: _search,
                onChanged: (_) => setState(() {}),
                sort: _sort,
                onSort: (s) => setState(() => _sort = s),
                club: _club,
                clubs: clubs,
                onClub: (c) => setState(() => _club = c),
              ),
            ),
            const Divider(height: 12, color: Colors.white12),
            Expanded(
              child: shown.isEmpty
                  ? const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text(
                          'Nobody matches that. Clear the search or the club.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.white38,
                            fontSize: 12.5,
                          ),
                        ),
                      ),
                    )
                  : ListView.builder(
                      itemCount: shown.length,
                      itemBuilder: (_, i) {
                        final item = shown[i];
                        final p = widget.of(item);
                        return ListTile(
                          dense: true,
                          title: Text(
                            p.name,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 13.5,
                            ),
                          ),
                          subtitle: Text(
                            widget.detail?.call(item) ??
                                '${p.team} · £${p.price.toStringAsFixed(1)}m · '
                                    '${p.xp.toStringAsFixed(1)} xP',
                            style: const TextStyle(
                              color: Colors.white38,
                              fontSize: 11,
                            ),
                          ),
                          onTap: () => Navigator.of(context).pop(item),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

/// The search box, the sort chips and the club chip — ⭐ **shared so the two lists cannot drift apart**
/// (ADR-184), while each keeps its own chrome: the Boot Battle picker is a modal, the transfer list is
/// already inside one.
class PickerControls extends StatelessWidget {
  const PickerControls({
    required this.search,
    required this.onChanged,
    required this.sort,
    required this.onSort,
    required this.club,
    required this.clubs,
    required this.onClub,
    super.key,
  });

  final TextEditingController search;
  final ValueChanged<String> onChanged;
  final PickerSort sort;
  final ValueChanged<PickerSort> onSort;
  final String? club;
  final List<String> clubs;
  final ValueChanged<String?> onClub;

  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    children: [
      TextField(
        controller: search,
        onChanged: onChanged,
        style: const TextStyle(color: Colors.white, fontSize: 13.5),
        decoration: InputDecoration(
          isDense: true,
          prefixIcon: const Icon(Icons.search, color: Colors.white30, size: 18),
          hintText: 'Search name or club',
          hintStyle: const TextStyle(color: Colors.white24, fontSize: 12.5),
          filled: true,
          fillColor: Colors.white10,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(Brand.radiusSm),
            borderSide: BorderSide.none,
          ),
        ),
      ),
      SizedBox(
        height: 42,
        child: ListView(
          scrollDirection: Axis.horizontal,
          children: [
            for (final option in PickerSort.values)
              Padding(
                padding: const EdgeInsets.only(right: 6, top: 7),
                child: ChoiceChip(
                  label: Text(option.label),
                  labelStyle: TextStyle(
                    fontSize: 11.5,
                    color: sort == option ? Colors.white : Colors.white54,
                  ),
                  selected: sort == option,
                  showCheckmark: false,
                  backgroundColor: Colors.white10,
                  selectedColor: Brand.purple,
                  side: BorderSide.none,
                  onSelected: (_) => onSort(option),
                ),
              ),
            Padding(
              padding: const EdgeInsets.only(right: 6, top: 7),
              child: ChoiceChip(
                // ⚠️ The club chip **says its value** when one is set (ADR-258) — a filter hiding behind
                // a generic label is a filter people forget is on.
                label: Text(club ?? 'Any club'),
                labelStyle: TextStyle(
                  fontSize: 11.5,
                  color: club == null ? Colors.white54 : Colors.white,
                ),
                selected: club != null,
                showCheckmark: false,
                backgroundColor: Colors.white10,
                selectedColor: Brand.purple,
                side: BorderSide.none,
                onSelected: (_) => _chooseClub(context),
              ),
            ),
          ],
        ),
      ),
    ],
  );

  Future<void> _chooseClub(BuildContext context) async {
    final picked = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: Brand.ink,
      builder: (sheet) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            ListTile(
              dense: true,
              title: const Text(
                'Any club',
                style: TextStyle(color: Colors.white, fontSize: 13.5),
              ),
              onTap: () => Navigator.of(sheet).pop(''),
            ),
            for (final name in clubs)
              ListTile(
                dense: true,
                title: Text(
                  name,
                  style: const TextStyle(color: Colors.white, fontSize: 13.5),
                ),
                onTap: () => Navigator.of(sheet).pop(name),
              ),
          ],
        ),
      ),
    );
    if (picked == null) return;
    onClub(picked.isEmpty ? null : picked);
  }
}
