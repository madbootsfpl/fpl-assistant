/// MADBOOTS — My Team, as a pitch (ADR-222).
///
/// ⭐ **Still one screen and no state management.** Riverpod and Drift are on the audit's Phase 4 list;
/// adding them before a screen asks for anything is a foundation built to a guess. `http` remains the only
/// dependency.
library;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'apply_plan.dart';
import 'brand.dart';
import 'chips_view.dart';
import 'players_view.dart';
import 'server.dart';
import 'settings_view.dart';
import 'signals_view.dart';
import 'draft.dart';
import 'feedback_view.dart';
import 'more_view.dart';
import 'pitch.dart';
import 'player_dna_view.dart';
import 'player_sheet.dart';
import 'team_dna_view.dart';
import 'this_week_view.dart';
import 'transfers_view.dart';

/// The owner's own team, so the app opens on something real rather than a stranger's squad.
const int kDefaultManagerId = 2885974;

/// ⚠️ **`main` is async now, and that is the whole point** — the API's address is read from the device
/// before the first frame, so no screen is ever built against a placeholder it would then have to be told
/// about (ADR-239). The read is one `SharedPreferences` lookup; nothing user-visible waits on it.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(MadbootsApp(baseUrl: await Server.load()));
}

class MadbootsApp extends StatelessWidget {
  const MadbootsApp({required this.baseUrl, super.key});

  final String baseUrl;

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
    home: MyTeamScreen(baseUrl: baseUrl),
  );
}

class MyTeamScreen extends StatefulWidget {
  const MyTeamScreen({required this.baseUrl, super.key});

  final String baseUrl;

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
/// The bar, **ordered by how often a manager needs each** (ADR-166's rule for the web sidebar).
///
/// ⚠️ **Chips is not here, and it works.** ADR-229 put it in the bar on the rule *a tab earns its slot by
/// working* — which is the rule for **removing dead tabs**, not for **allocating scarce slots**. Those are
/// different questions, and the second one is decided by frequency: a chip is a handful of decisions per
/// season, where Players is browsed weekly.
///
/// ⭐ The audit's §6 settles it without my opinion: the first release is *This week · My squad · Transfers
/// · Players*, and Chips is not in it. It lives in More, which is no longer a graveyard for unbuilt
/// things — it holds working ones now.
enum _Tab { myTeam, thisWeek, transfers, players, more }

extension on _Tab {
  String get label => switch (this) {
    _Tab.myTeam => 'My team',
    _Tab.thisWeek => 'This week',
    _Tab.transfers => 'Transfers',
    _Tab.players => 'Players',
    _Tab.more => 'More',
  };

  IconData get icon => switch (this) {
    _Tab.myTeam => Icons.sports_soccer,
    _Tab.thisWeek => Icons.event_note,
    _Tab.transfers => Icons.swap_horiz,
    _Tab.players => Icons.people_outline,
    _Tab.more => Icons.more_horiz,
  };
}

class _MyTeamScreenState extends State<MyTeamScreen> {
  /// ⚠️ **Not `final`.** Changing the address has to build a new client — `ServiceClient` holds its base
  /// URL, so mutating a field would leave every in-flight and future call pointed at the old machine.
  late ServiceClient _client = ServiceClient(baseUrl: widget.baseUrl);
  late final TextEditingController _id = TextEditingController(
    text: '$kDefaultManagerId',
  );
  late Future<MyTeam> _team = _load(kDefaultManagerId);
  _Tab _tab = _Tab.myTeam;

  /// ⭐ Held here, not inside the pitch, so it survives a tab switch. Changing what every card means and
  /// then forgetting it the moment you look at Transfers would be its own small betrayal.
  PitchMode _mode = PitchMode.nextGw;

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

  /// ⚠️ **The health check is gone, and the message with it.** It said the same thing the client now says
  /// for every call — and saying it here meant *only* this screen said it: six others surfaced
  /// `SocketException: Connection refused … errno = 61` verbatim.
  ///
  /// ⭐ *A fix scoped to where it was noticed is a fix the next screen does not get.*
  Future<MyTeam> _load(int managerId) async {
    final real = await _client.myTeam(
      managerId,
      horizon: 1,
      freeTransfers: _freeTransfers,
    );

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
    return _client.myTeam(
      managerId,
      horizon: 1,
      freeTransfers: _freeTransfers,
      draftPlayerIds: saved.playerIds,
      draftBenchIds: saved.benchIds,
    );
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

    final draft = Draft.swap(
      existing: _draft,
      managerId: team.fplPlayerIds.isEmpty ? kDefaultManagerId : _managerId,
      gameweek: team.gameweek ?? 0,
      basePlayerIds: base,
      benchIds: team.analysis.bench.map((p) => p.id).toList(),
      outId: outId,
      inId: inId,
      // ⚠️ Stamped so a future version can age a plan out; nothing reads it yet, and it costs one field.
      savedAt: DateTime.now(),
      teamCaptainId: team.captainId,
      teamViceCaptainId: team.viceCaptainId,
    );
    await _drafts.save(draft);
    setState(() {
      _draft = draft;
      _dropped = null;
      _tab = _Tab
          .myTeam; // ⭐ Back to the pitch: the point of applying is to SEE it.
      _team = _load(_managerId);
    });
  }

  int get _managerId => int.tryParse(_id.text.trim()) ?? kDefaultManagerId;

  /// Push a full screen. ⭐ Used for the things More links to — they are screens, not rows, and giving them
  /// a back button is what makes More a menu rather than a very long page.
  void _open(String title, Widget body) => Navigator.of(context).push(
    MaterialPageRoute<void>(
      builder: (_) => Scaffold(
        backgroundColor: Brand.ink,
        appBar: AppBar(
          title: Text(title),
          backgroundColor: Brand.ink,
          foregroundColor: Colors.white,
        ),
        body: body,
      ),
    ),
  );

  /// Tap a player: armband, or replace him.
  Future<void> _openPlayer(MyTeam team, PlayerSummary player) async {
    final action = await showPlayerSheet(
      context,
      team: team,
      player: player,
      client: _client,
    );
    if (action == null) return;
    switch (action) {
      // ⭐ Armbands change no number this app computes, so they never leave the device — no round trip,
      // no reload, just a redraw. That is why a tap is enough and a tab would have been too much.
      case MakeCaptain(:final playerId):
        await _setArmband(team, captainId: playerId);
      case MakeVice(:final playerId):
        await _setArmband(team, viceCaptainId: playerId);
      case SwapWith(:final a, :final b):
        await _substitute(team, a, b);
      case ReplaceWith(:final outId, :final inId):
        await _planSwap(team, outId, inId);
    }
  }

  /// ⚠️ **A captain cannot also be vice.** Setting one clears the other if they collide — FPL would reject
  /// it, and an app that let you build an impossible team is teaching you something untrue.
  Future<void> _setArmband(
    MyTeam team, {
    int? captainId,
    int? viceCaptainId,
  }) async {
    final base =
        _draft ??
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
    // ⚠️ `clearViceCaptain`, not `null` — see `Draft.copyWith`. Passing null asked for "no opinion" and
    // left the collision in place, so promoting your vice left him wearing both letters.
    final collides = nextVice == nextCaptain;
    final draft = base.copyWith(
      captainId: nextCaptain,
      viceCaptainId: collides ? null : nextVice,
      clearViceCaptain: collides,
    );
    await _drafts.save(draft);
    setState(() {
      _draft = draft;
      _dropped = null;
    });
  }

  /// ⭐ **The one link that leaves the app** (ADR-254). Help is content — better on a big screen, and
  /// updatable without an App Store release.
  ///
  /// ⚠️ **It reports a failure rather than doing nothing.** A row that silently does not open is worse
  /// than one that is not there: the reader taps twice, concludes the app is broken, and is right.
  Future<void> _openHelp() async {
    const url = 'https://madboots.streamlit.app/Help';
    final opened = await launchUrl(
      Uri.parse(url),
      mode: LaunchMode.externalApplication,
    ).catchError((_) => false);
    if (!mounted || opened) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Could not open $url')));
  }

  /// Change two players' places — ⭐ **free and reversible**, unlike a transfer (ADR-246).
  Future<void> _substitute(MyTeam team, int a, int b) async {
    final draft = Draft.substitute(
      existing: _draft,
      managerId: _managerId,
      gameweek: team.gameweek ?? 0,
      basePlayerIds: team.fplPlayerIds,
      benchIds: team.analysis.bench.map((p) => p.id).toList(),
      a: a,
      b: b,
      savedAt: DateTime.now(),
      teamCaptainId: team.captainId,
      teamViceCaptainId: team.viceCaptainId,
    );
    await _drafts.save(draft);
    if (!mounted) return;
    setState(() {
      _draft = draft;
      _dropped = null;
      _team = _load(_managerId);
    });
  }

  /// Field the best XI you already own — ⚠️ **a lineup change, never a transfer** (ADR-244).
  ///
  /// ⭐ Goes through the same [Draft] as everything else, so it inherits the banner, the staleness check
  /// and the way out. A second mechanism for "the squad you are looking at is not your FPL squad" is how
  /// one of them ends up not saying so.
  Future<void> _applyPlan(MyTeam team, SuggestedLineup plan) async {
    final base =
        _draft ??
        Draft(
          managerId: _managerId,
          gameweek: team.gameweek ?? 0,
          basePlayerIds: team.fplPlayerIds,
          playerIds: team.fplPlayerIds,
          benchIds: team.analysis.bench.map((p) => p.id).toList(),
          savedAt: DateTime.now(),
          captainId: team.captainId,
          viceCaptainId: team.viceCaptainId,
        );
    // ⚠️ `playerIds` is untouched on purpose — the fifteen are the same fifteen. Only the bench moves.
    final draft = base.copyWith(benchIds: plan.bench);
    await _drafts.save(draft);
    if (!mounted) return;
    setState(() {
      _draft = draft;
      _dropped = null;
      _team = _load(_managerId);
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
          // ⭐⭐ **On every tab except My Team**, where the pitch carries the wordmark itself (ADR-253).
          // ⚠️ Deleting it outright would have stripped the branding from Players, Transfers and More,
          // which have no green to put it on — *a row worth reclaiming on one screen is not a row worth
          // reclaiming on all of them.*
          if (_tab != _Tab.myTeam) const _TitleBar(),
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
                      child: SelectableText(
                        _reason(snapshot.error),
                        style: const TextStyle(
                          color: Colors.white70,
                          height: 1.55,
                        ),
                      ),
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
      // ⭐⭐⭐ **No scroll view, and that is the change** (ADR-253). The pitch was 747px of a 1932px
      // screen: chrome above it, the bench floating on the dark below it, and 140px of dead space under
      // that. It now fills whatever is left after the header — ⚠️ *a screen whose main subject scrolls
      // is a screen that has decided its main subject is not important enough to fit.*
      _Tab.myTeam => Padding(
        padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ⚠️⚠️ **Only when a FINISHED gameweek is missing** (ADR-248). A permanent "last updated"
            // strip would be read once and then never again; this appears exactly when the numbers below
            // it are wrong, and disappears when they are not. ⭐ *A warning that is always on is a
            // decoration.*
            if (team.data.behind) _StaleBanner(data: team.data),
            Expanded(
              child: PitchView(
                team: team,
                mode: _mode,
                onMode: (m) => setState(() => _mode = m),
                onTapPlayer: (p) => _openPlayer(team, p),
                // ⭐ On the pitch, below the bench — the action where the thing it acts on is.
                footer: ApplyPlanStrip(
                  team: team,
                  onApply: (plan) => _applyPlan(team, plan),
                ),
              ),
            ),
          ],
        ),
      ),
      _Tab.transfers => TransfersView(
        client: _client,
        team: team,
        onPlan: (outId, inId) => _planSwap(team, outId, inId),
      ),
      _Tab.thisWeek => ThisWeekView(
        client: _client,
        team: team,
        onApply: (plan) => _applyPlan(team, plan),
      ),
      _Tab.players => PlayersView(
        client: _client,
        owned: {
          ...team.analysis.xi.map((p) => p.id),
          ...team.analysis.bench.map((p) => p.id),
        },
      ),
      _Tab.more => MoreView(
        managerId: _managerId,
        freeTransfers: _freeTransfers,
        onOpenChips: () => _open(
          'Chips',
          ChipsView(client: _client, team: team, managerId: _managerId),
        ),
        onOpenSignals: () =>
            _open('Signals', SignalsView(client: _client, team: team)),
        onOpenPlayerDna: () =>
            _open('Player DNA', PlayerDnaView(client: _client, team: team)),
        onOpenTeamDna: () =>
            _open('Team DNA', TeamDnaView(client: _client, team: team)),
        onOpenFeedback: () =>
            _open('Tell us something', FeedbackView(client: _client)),
        onOpenHelp: _openHelp,
        onOpenSettings: () => _open(
          'Settings',
          SettingsView(
            team: team,
            managerId: _managerId,
            freeTransfers: _freeTransfers,
            baseUrl: _client.baseUrl,
            // ⭐ A new client, and an immediate reload against it — the screen you came from is the
            // proof the new address works, which beats a message saying it should.
            onServer: (url) async {
              await Server.save(url);
              if (!mounted) return;
              setState(() {
                _client = ServiceClient(baseUrl: Server.tidy(url));
                _team = _load(_managerId);
              });
            },
            onManagerId: (id) {
              _id.text = '$id';
              setState(() => _team = _load(id));
            },
            onFreeTransfers: (n) => setState(() {
              _freeTransfers = n;
              _team = _load(_managerId);
            }),
          ),
        ),
      ),
    };
  }

  static String _reason(Object? error) => friendlyError(error);
}

/// ⭐ A wordmark and nothing else. The manager id used to live here, which made a **setting** look like a
/// title — it is in More now, where a thing you change once belongs.
class _TitleBar extends StatelessWidget {
  const _TitleBar();

  @override
  Widget build(BuildContext context) => const Padding(
    padding: EdgeInsets.fromLTRB(14, 8, 14, 6),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // ⭐ **The badge, not just the wordmark** (ADR-243). On a phone the badge is what a person
        // recognises — it is what they tapped on the home screen a second earlier.
        Image(
          image: AssetImage('assets/madboots-badge.png'),
          width: 22,
          height: 22,
          filterQuality: FilterQuality.medium,
        ),
        SizedBox(width: 7),
        Text.rich(
          TextSpan(
            children: [
              TextSpan(
                text: 'MAD',
                style: TextStyle(
                  color: Brand.purpleLight,
                  fontWeight: FontWeight.w700,
                ),
              ),
              // ⚠️⚠️ **Orange, because the brand says so** — `brand.py`'s `wordmark_html`: *"MAD purple ·
              // BOOTS orange, the colour split doing the word-break"*. The app rendered it white, which
              // was not a decision anybody took: the wordmark was **retyped here** instead of derived,
              // so it drifted from the one source of truth ADR-103/114 exists to keep.
              //
              // ⭐ `tests/test_brand_dart.py` now compares these two colours against `brand.py`. *A
              // generated palette does not stop a hand-written rule from disagreeing with it.*
              TextSpan(
                text: 'BOOTS',
                style: TextStyle(color: Brand.orange),
              ),
            ],
          ),
          style: TextStyle(fontSize: 15, letterSpacing: .5),
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
                // ⚠️ `opaque` so the whole column is the target, not just the glyph — a 19px icon is
                // under Apple's 44pt minimum and misses on a real thumb.
                behavior: HitTestBehavior.opaque,
                onTap: () => onPick(tab),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      tab.icon,
                      size: 19,
                      color: tab == current ? Colors.white : Colors.white54,
                    ),
                    const SizedBox(height: 3),
                    Text(
                      tab.label,
                      style: TextStyle(
                        fontSize: 9.5,
                        color: tab == current ? Colors.white : Colors.white54,
                      ),
                    ),
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
    // ⭐ **Quieter, not quiet** (feedback item 1: *"Orange Banner could be smaller"*). It still has to be
    // unmissable — a plan shown as your squad is a lie about something you can act on — but it was taking
    // a slab of a small screen to say something you learn in one glance and then stop needing. ⚠️ *The
    // colour is what makes it unmissable; the height was only making it loud.*
    color: Brand.orange,
    padding: const EdgeInsets.fromLTRB(12, 4, 6, 4),
    child: Row(
      children: [
        const Icon(Icons.edit_note, size: 14, color: Colors.white),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            // ⚠️ Says what it is AND what it is not. "Plan" alone could be read as a saved team.
            // ⚠️ Still says what it is AND what it is not — "Plan" alone could be read as a saved team.
            // ⭐ The instruction to go and make it real moved out: it is advice for when you are finished,
            // not a caption you need on every screen, and it was the line that made this two rows tall.
            'A plan — not your FPL team'
            '${draft == null ? '' : ' · ${draft!.changeCount} change${draft!.changeCount == 1 ? '' : 's'}'}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 10.5,
              height: 1.2,
            ),
          ),
        ),
        TextButton(
          onPressed: onDiscard,
          style: TextButton.styleFrom(
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 8),
            minimumSize: const Size(0, 28),
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: const Text('Discard', style: TextStyle(fontSize: 10.5)),
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
        DraftStaleness.gameweekPassed => 'Your saved plan was for a gameweek that has been played, so it has been cleared.',
        DraftStaleness.squadChanged => 'Your squad changed since you saved a plan — looks like you made the move. Plan cleared.',
        DraftStaleness.otherManager =>
          'That plan belonged to a different manager id. Cleared.',
        DraftStaleness.fresh => '',
      },
      style: const TextStyle(color: Colors.white54, fontSize: 11, height: 1.4),
    ),
  );
}

/// The board is behind a finished gameweek — ⭐⭐ **the message whose absence made a stale database look
/// like a broken engine** (ADR-248).
///
/// The owner checked a player's last five, saw a blank against Coventry and no Arsenal game at all, and
/// asked why the app was not reflecting reality. It was: *a reality from the previous afternoon.*
class _StaleBanner extends StatelessWidget {
  const _StaleBanner({required this.data});

  final DataFreshness data;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    margin: const EdgeInsets.fromLTRB(6, 4, 6, 6),
    padding: const EdgeInsets.fromLTRB(11, 8, 11, 9),
    decoration: BoxDecoration(
      color: Brand.warn.withValues(alpha: 0.18),
      border: Border.all(color: Brand.warn, width: 1),
      borderRadius: BorderRadius.circular(Brand.radiusSm),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.history_toggle_off, size: 15, color: Brand.warn),
        const SizedBox(width: 7),
        Expanded(
          child: Text(
            // ⭐ Names the gameweek, because *"missing GW5"* is a fact someone can act on and "stale" is
            // a mood. And says what it costs, because a warning without a consequence gets dismissed.
            '${data.warning}  Last refreshed ${data.age}.',
            style: const TextStyle(
              color: Brand.warn,
              fontSize: 11,
              height: 1.4,
            ),
          ),
        ),
      ],
    ),
  );
}
