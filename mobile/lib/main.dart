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
import 'chips_view.dart';
import 'draft.dart';
import 'more_view.dart';
import 'pitch.dart';
import 'player_sheet.dart';
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
/// ⚠️ **Chips left the bar and ADR-223 argued it should not.** That argument was *"a bar that grows items
/// later moves everything under the user's thumb"* — and it held while the fourth slot was a placeholder.
/// ⭐ It stops holding when there is a **real** fourth item: four working tabs beat three plus a dead one,
/// and the move is cheaper now than after anyone has built muscle memory for a button that does nothing.
/// ⚠️ **Chips is back in the bar** — ADR-223 greyed it, ADR-228 moved it into More *because it did not
/// work*, and ADR-229 built it. ⭐ *A tab earns its slot by working*, which is the rule both earlier moves
/// were reaching for.
enum _Tab { myTeam, transfers, thisWeek, chips, more }

extension on _Tab {
  String get label => switch (this) {
        _Tab.myTeam => 'My team',
        _Tab.transfers => 'Transfers',
        _Tab.thisWeek => 'This week',
        _Tab.chips => 'Chips',
        _Tab.more => 'More',
      };

  IconData get icon => switch (this) {
        _Tab.myTeam => Icons.sports_soccer,
        _Tab.transfers => Icons.swap_horiz,
        _Tab.thisWeek => Icons.event_note,
        _Tab.chips => Icons.style_outlined,
        _Tab.more => Icons.more_horiz,
      };
}

class _MyTeamScreenState extends State<MyTeamScreen> {
  final ServiceClient _client = ServiceClient(baseUrl: kBaseUrl);
  late final TextEditingController _id =
      TextEditingController(text: '$kDefaultManagerId');
  late Future<MyTeam> _team = _load(kDefaultManagerId);
  _Tab _tab = _Tab.myTeam;

  final DraftStore _drafts = DraftStore();

  /// The draft currently being shown, or null when the real team is.
  Draft? _draft;

  /// Why a saved draft was dropped, kept so the app can say so **once** rather than silently.
  DraftStaleness? _dropped;

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
    final real = await _client.myTeam(managerId, horizon: 1, freeTransfers: _freeTransfers);

    // ⭐⭐ **The real team is fetched FIRST, always.** A saved draft is an overlay on reality, never a
    // substitute for it — so reality is established before anything is laid over it, and a draft that no
    // longer applies is discarded rather than displayed.
    final saved = await _drafts.load();
    if (saved == null) return real;

    final verdict = saved.checkAgainst(
      managerId: managerId,
      gameweek: real.gameweek,
      fplPlayerIds: real.fplPlayerIds,
    );
    if (verdict != DraftStaleness.fresh) {
      // ⚠️ Dropped **and** reported. Silently discarding a manager's plan is its own kind of lie, and
      // "your squad changed" is usually the news that he already made the move.
      await _drafts.clear();
      _draft = null;
      _dropped = verdict;
      return real;
    }

    _draft = saved;
    return _client.myTeam(managerId,
        horizon: 1,
        freeTransfers: _freeTransfers,
        draftPlayerIds: saved.playerIds,
        draftBenchIds: saved.benchIds);
  }

  /// Plan a swap: `outId` leaves, `inId` arrives.
  ///
  /// ⚠️ **Built from the squad FPL holds, never from what is on screen.** Applying a second swap to an
  /// already-drafted squad would compound plans and lose the thread back to reality — and the draft could
  /// then no longer tell whether it was stale. One base, one set of changes.
  Future<void> _planSwap(MyTeam team, int outId, int inId) async {
    final base = team.fplPlayerIds;
    final current = _draft?.playerIds ?? base;
    if (!current.contains(outId) || current.contains(inId)) return;

    final next = [for (final id in current) id == outId ? inId : id];
    final bench = [
      for (final p in team.analysis.bench) p.id == outId ? inId : p.id,
    ];
    final draft = Draft(
      managerId: team.fplPlayerIds.isEmpty ? kDefaultManagerId : _managerId,
      gameweek: team.gameweek ?? 0,
      basePlayerIds: base,
      playerIds: next,
      benchIds: bench,
      // ⚠️ Stamped so a future version can age a plan out; nothing reads it yet, and it costs one field.
      savedAt: DateTime.now(),
    );
    await _drafts.save(draft);
    setState(() {
      _draft = draft;
      _dropped = null;
      _tab = _Tab.myTeam;      // ⭐ Back to the pitch: the point of applying is to SEE it.
      _team = _load(_managerId);
    });
  }

  int get _managerId => int.tryParse(_id.text.trim()) ?? kDefaultManagerId;

  /// Tap a player: armband, or replace him.
  Future<void> _openPlayer(MyTeam team, PlayerSummary player) async {
    final action = await showPlayerSheet(context,
        team: team, player: player, client: _client);
    if (action == null) return;
    switch (action) {
      // ⭐ Armbands change no number this app computes, so they never leave the device — no round trip,
      // no reload, just a redraw. That is why a tap is enough and a tab would have been too much.
      case MakeCaptain(:final playerId):
        await _setArmband(team, captainId: playerId);
      case MakeVice(:final playerId):
        await _setArmband(team, viceCaptainId: playerId);
      case ReplaceWith(:final outId, :final inId):
        await _planSwap(team, outId, inId);
    }
  }

  /// ⚠️ **A captain cannot also be vice.** Setting one clears the other if they collide — FPL would reject
  /// it, and an app that let you build an impossible team is teaching you something untrue.
  Future<void> _setArmband(MyTeam team, {int? captainId, int? viceCaptainId}) async {
    final base = _draft ??
        Draft(
          managerId: _managerId,
          gameweek: team.gameweek ?? 0,
          basePlayerIds: team.fplPlayerIds,
          playerIds: team.fplPlayerIds,
          benchIds: team.analysis.bench.map((p) => p.id).toList(),
          savedAt: DateTime.now(),
        );
    final nextCaptain = captainId ?? base.captainId ?? team.captainId;
    final nextVice = viceCaptainId ?? base.viceCaptainId ?? team.viceCaptainId;
    final draft = base.copyWith(
      captainId: nextCaptain,
      viceCaptainId: nextVice == nextCaptain ? null : nextVice,
    );
    await _drafts.save(draft);
    setState(() {
      _draft = draft;
      _dropped = null;
    });
  }

  /// Show the real team again, forgetting the plan.
  Future<void> _discardDraft() async {
    await _drafts.clear();
    setState(() {
      _draft = null;
      _dropped = null;
      _team = _load(int.tryParse(_id.text.trim()) ?? kDefaultManagerId);
    });
  }

  /// ⚠️⚠️ **FPL does not publish this, so the app has to ask** (ADR-191). It was `final int = 1` until
  /// ADR-228 gave it a home in More — ⭐ *the app was advising a position the manager might not be in,
  /// because there was nowhere to put a setting.* One is the common case, not the only one.
  int _freeTransfers = 1;

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
              const _TitleBar(),
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
                    return Column(
                      children: [
                        if (snapshot.data!.isDraft || _draft != null)
                          _DraftBanner(draft: _draft, onDiscard: _discardDraft),
                        if (_dropped != null) _DroppedBanner(reason: _dropped!),
                        Expanded(child: _body(snapshot.data!)),
                      ],
                    );
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

  Widget _body(MyTeam rawTeam) {
    // ⭐ The draft's armbands win over FPL's for display. They are the only part of a plan the server never
    // sees, because they change nothing it computes.
    final team = _draft == null
        ? rawTeam
        : rawTeam.withArmbands(
            captainId: _draft!.captainId ?? rawTeam.captainId,
            viceCaptainId: _draft!.viceCaptainId ?? rawTeam.viceCaptainId,
          );
    return switch (_tab) {
        _Tab.myTeam => SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 16),
            child: PitchView(team: team, onTapPlayer: (p) => _openPlayer(team, p)),
          ),
        _Tab.transfers => TransfersView(
            client: _client,
            team: team,
            onPlan: (outId, inId) => _planSwap(team, outId, inId),
          ),
        _Tab.thisWeek => ThisWeekView(client: _client, team: team),
        _Tab.chips => ChipsView(client: _client, team: team),
        _Tab.more => MoreView(
            team: team,
            managerId: _managerId,
            freeTransfers: _freeTransfers,
            onManagerId: (id) {
              _id.text = '$id';
              setState(() => _team = _load(id));
            },
            onFreeTransfers: (n) => setState(() {
              _freeTransfers = n;
              _team = _load(_managerId);
            }),
          ),
      };
  }

  static String _reason(Object? error) =>
      error is ApiException ? error.detail : '$error';
}

/// ⭐ A wordmark and nothing else. The manager id used to live here, which made a **setting** look like a
/// title — it is in More now, where a thing you change once belongs.
class _TitleBar extends StatelessWidget {
  const _TitleBar();

  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.fromLTRB(14, 12, 14, 8),
        child: Text.rich(
          TextSpan(children: [
            TextSpan(
                text: 'MAD',
                style: TextStyle(color: Brand.purpleLight, fontWeight: FontWeight.w700)),
            TextSpan(text: 'BOOTS', style: TextStyle(color: Colors.white)),
          ]),
          style: TextStyle(fontSize: 15, letterSpacing: .5),
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
                    // ⚠️ `opaque` so the whole column is the target, not just the glyph — a 19px icon is
                    // under Apple's 44pt minimum and misses on a real thumb.
                    behavior: HitTestBehavior.opaque,
                    onTap: () => onPick(tab),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(tab.icon,
                            size: 19,
                            color: tab == current ? Colors.white : Colors.white54),
                        const SizedBox(height: 3),
                        Text(tab.label,
                            style: TextStyle(
                                fontSize: 9.5,
                                color: tab == current ? Colors.white : Colors.white54)),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      );
}


/// ⭐⭐ **Unmissable, and it has to be.** A plan shown as your squad is a lie about something you can act
/// on — so the banner is coloured, permanent while the draft is live, and carries the way out.
class _DraftBanner extends StatelessWidget {
  const _DraftBanner({required this.draft, required this.onDiscard});

  final Draft? draft;
  final VoidCallback onDiscard;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        color: Brand.orange,
        padding: const EdgeInsets.fromLTRB(14, 7, 8, 7),
        child: Row(
          children: [
            const Icon(Icons.edit_note, size: 17, color: Colors.white),
            const SizedBox(width: 7),
            Expanded(
              child: Text(
                // ⚠️ Says what it is AND what it is not. "Plan" alone could be read as a saved team.
                'A plan — not your FPL team. '
                '${draft == null ? '' : '${draft!.changeCount} change${draft!.changeCount == 1 ? '' : 's'}. '}'
                'Make it for real in the FPL app.',
                style: const TextStyle(color: Colors.white, fontSize: 11.5, height: 1.35),
              ),
            ),
            TextButton(
              onPressed: onDiscard,
              style: TextButton.styleFrom(
                  foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(horizontal: 10)),
              child: const Text('Discard', style: TextStyle(fontSize: 11.5)),
            ),
          ],
        ),
      );
}

/// ⭐ *"Your plan is gone"* and *"your plan already happened"* mean opposite things, so each gets its own
/// sentence rather than a shared apology.
class _DroppedBanner extends StatelessWidget {
  const _DroppedBanner({required this.reason});

  final DraftStaleness reason;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        color: Colors.white12,
        padding: const EdgeInsets.fromLTRB(14, 7, 14, 7),
        child: Text(
          switch (reason) {
            DraftStaleness.gameweekPassed =>
              'Your saved plan was for a gameweek that has been played, so it has been cleared.',
            DraftStaleness.squadChanged =>
              'Your squad changed since you saved a plan — looks like you made the move. Plan cleared.',
            DraftStaleness.otherManager => 'That plan belonged to a different manager id. Cleared.',
            DraftStaleness.fresh => '',
          },
          style: const TextStyle(color: Colors.white54, fontSize: 11, height: 1.4),
        ),
      );
}
