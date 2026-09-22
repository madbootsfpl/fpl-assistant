/// MADBOOTS — My Team, as a pitch (ADR-222).
///
/// ⭐ **Still one screen and no state management.** Riverpod and Drift are on the audit's Phase 4 list;
/// adding them before a screen asks for anything is a foundation built to a guess. `http` remains the only
/// dependency.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'pitch.dart';
import 'this_week_view.dart';
import 'transfers_view.dart';

/// ⚠️ **Reaches the dev server from macOS desktop, the iOS simulator and Chrome** — all three share the
/// host's network. A **physical device** cannot, and that is the point at which the API needs hosting.
const String kBaseUrl = 'http://localhost:8078';

/// The owner's own team, so the app opens on something real rather than a stranger's squad.
const int kDefaultManagerId = 2885974;

void main() => runApp(const MadbootsApp());

class MadbootsApp extends StatelessWidget {
  const MadbootsApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: Brand.name,
        debugShowCheckedModeBanner: false,
        // ⭐ Seeded from the brand's own purple, generated from `brand.py` — the web app's single source of
        // truth (ADR-103/114). A hex typed here would be a second definition of the brand.
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Brand.purple),
          scaffoldBackgroundColor: Brand.ink,
          useMaterial3: true,
        ),
        home: const MyTeamScreen(),
      );
}

class MyTeamScreen extends StatefulWidget {
  const MyTeamScreen({super.key});

  @override
  State<MyTeamScreen> createState() => _MyTeamScreenState();
}

/// The tabs, in the order the web app's sub-tabs run.
///
/// ⚠️ **Captain and Chips are listed and not yet built.** Showing them greyed is a deliberate choice over
/// hiding them: a bottom bar that grows items later moves everything under the user's thumb, and muscle
/// memory is the first thing a returning user brings.
enum _Tab { myTeam, transfers, thisWeek, captain, chips }

extension on _Tab {
  String get label => switch (this) {
        _Tab.myTeam => 'My team',
        _Tab.transfers => 'Transfers',
        _Tab.thisWeek => 'This week',
        _Tab.captain => 'Captain',
        _Tab.chips => 'Chips',
      };

  IconData get icon => switch (this) {
        _Tab.myTeam => Icons.sports_soccer,
        _Tab.transfers => Icons.swap_horiz,
        _Tab.thisWeek => Icons.event_note,
        _Tab.captain => Icons.star_outline,
        _Tab.chips => Icons.style_outlined,
      };

  bool get ready => this == _Tab.myTeam || this == _Tab.transfers || this == _Tab.thisWeek;
}

class _MyTeamScreenState extends State<MyTeamScreen> {
  final ServiceClient _client = ServiceClient(baseUrl: kBaseUrl);
  late final TextEditingController _id =
      TextEditingController(text: '$kDefaultManagerId');
  late Future<MyTeam> _team = _load(kDefaultManagerId);
  _Tab _tab = _Tab.myTeam;

  /// ⭐ **Loaded once and shared across the tabs**, rather than fetched per screen. Two screens fetching
  /// the same squad could disagree about who you own — and on a phone it is also three round trips for
  /// one answer.
  ///
  /// ⚠️ This is also why there is still no Riverpod: a `setState` at the top of one screen is genuinely
  /// enough today. When it stops being enough, that is the moment it earns its place.

  /// ⭐ The health check first, because *"the service is not running"* and *"that team is not public yet"*
  /// are different problems, and only one of them is the manager's to fix.
  Future<MyTeam> _load(int managerId) async {
    if (!await _client.healthy()) {
      throw StateError(
        'The service is not answering on $kBaseUrl.\n\n'
        'Start it with:\n'
        '  venv/bin/python -m uvicorn src.service.http:app --port 8078',
      );
    }
    return _client.myTeam(managerId, horizon: 1, freeTransfers: _freeTransfers);
  }

  /// ⚠️ FPL does not publish this, so the app has to ask (ADR-191). One is the common case.
  final int _freeTransfers = 1;

  void _reload() {
    final id = int.tryParse(_id.text.trim());
    if (id == null || id < 1) return;
    setState(() => _team = _load(id));
  }

  @override
  void dispose() {
    _client.close();
    _id.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              _TitleBar(controller: _id, onSubmit: _reload),
              Expanded(
                child: FutureBuilder<MyTeam>(
                  future: _team,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snapshot.hasError) {
                      // ⚠️ Shown, not swallowed. An app that renders an empty pitch on failure looks like a
                      // squad with no players — and the message is usually the whole diagnosis.
                      return Padding(
                        padding: const EdgeInsets.all(22),
                        child: Center(
                          child: SelectableText(_reason(snapshot.error),
                              style: const TextStyle(color: Colors.white70, height: 1.55)),
                        ),
                      );
                    }
                    return _body(snapshot.data!);
                  },
                ),
              ),
            ],
          ),
        ),
        bottomNavigationBar: _BottomBar(
          current: _tab,
          onPick: (t) => setState(() => _tab = t),
        ),
      );

  Widget _body(MyTeam team) => switch (_tab) {
        _Tab.myTeam => SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 16),
            child: PitchView(team: team),
          ),
        _Tab.transfers => TransfersView(client: _client, team: team),
        _Tab.thisWeek => ThisWeekView(client: _client, team: team),
        // ⭐ Named rather than blank. "Not built yet" is information; an empty screen is a bug report.
        _ => Center(
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Text(
                '${_tab.label} is not built yet.\n\nOn the web it lives under My Squad; '
                'it needs a way to change your team, not just read it.',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white38, height: 1.6),
              ),
            ),
          ),
      };

  static String _reason(Object? error) =>
      error is ApiException ? error.detail : '$error';
}

class _TitleBar extends StatelessWidget {
  const _TitleBar({required this.controller, required this.onSubmit});

  final TextEditingController controller;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 6),
        child: Row(
          children: [
            const Text.rich(
              TextSpan(children: [
                TextSpan(
                    text: 'MAD',
                    style: TextStyle(color: Brand.purpleLight, fontWeight: FontWeight.w700)),
                TextSpan(text: 'BOOTS', style: TextStyle(color: Colors.white)),
              ]),
              style: TextStyle(fontSize: 15, letterSpacing: .5),
            ),
            const Spacer(),
            SizedBox(
              width: 108,
              height: 30,
              child: TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.end,
                onSubmitted: (_) => onSubmit(),
                style: const TextStyle(color: Colors.white, fontSize: 12.5),
                decoration: InputDecoration(
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  hintText: 'manager id',
                  hintStyle: const TextStyle(color: Colors.white38, fontSize: 12),
                  filled: true,
                  fillColor: Colors.white10,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 6),
            IconButton(
              onPressed: onSubmit,
              icon: const Icon(Icons.refresh, size: 18, color: Colors.white70),
              tooltip: 'Load this team',
            ),
          ],
        ),
      );
}


class _BottomBar extends StatelessWidget {
  const _BottomBar({required this.current, required this.onPick});

  final _Tab current;
  final ValueChanged<_Tab> onPick;

  @override
  Widget build(BuildContext context) => Container(
        color: const Color(0xFF0F0C16),
        padding: const EdgeInsets.only(top: 6, bottom: 8),
        child: SafeArea(
          top: false,
          child: Row(
            children: [
              for (final tab in _Tab.values)
                Expanded(
                  child: GestureDetector(
                    // ⚠️ `opaque` so the whole column is the target, not just the glyph — a 15px icon is
                    // under Apple's 44pt minimum and misses on a real thumb.
                    behavior: HitTestBehavior.opaque,
                    onTap: () => onPick(tab),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(tab.icon,
                            size: 19,
                            color: tab == current
                                ? Colors.white
                                : (tab.ready ? Colors.white54 : Colors.white24)),
                        const SizedBox(height: 3),
                        Text(tab.label,
                            style: TextStyle(
                                fontSize: 9.5,
                                color: tab == current
                                    ? Colors.white
                                    : (tab.ready ? Colors.white54 : Colors.white24))),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      );
}
