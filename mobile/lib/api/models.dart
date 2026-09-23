/// Dart models for the MADBOOTS service responses (ADR-221).
///
/// ⭐⭐ **Hand-written, and guarded rather than generated.** The mobile audit §5 planned to generate these
/// from FastAPI's OpenAPI schema — *"one contract, no hand-written duplicates."* Every route is typed
/// `-> dict`, so the schema advertises each response as an untyped object and a generator would emit
/// `Map<String, dynamic>` for all six. Typing the six responses server-side would install a **second
/// definition of every answer** beside the dict the engine already builds, which is what ADRs 123, 127 and
/// 181 are each about.
///
/// So the contract is pinned from the other end: `tests/test_api_contract.py` fails when a response's
/// **shape** moves — a field disappearing, changing type, or becoming non-nullable. ⚠️ *These classes are
/// only as honest as that test*, so when it fails, read the diff before regenerating.
///
/// ⭐ **Every model reads the keys it needs and ignores the rest.** Two endpoints (`build`, `route`) still
/// return whole database rows — forty-odd columns of `cbi`, `corners_order`, `cost_change_event`. Ignoring
/// them here costs nothing at parse time; it costs bytes on the wire, which is a server-side decision noted
/// in the start checklist.
library;

/// ⚠️ **Gameweek keys cross the wire as STRINGS**, because JSON has no integer object keys — the same shape
/// PostgREST serves for the published board.
///
/// ⭐ **Parsed to `int` here, once, so nothing downstream sorts them as text.** As strings `"10"` sorts
/// before `"6"`, so a prefix sum over *the next two gameweeks* would silently answer for the wrong two.
Map<int, double> _gameweeks(dynamic raw) {
  if (raw == null) return const {};
  return {
    for (final entry in (raw as Map<String, dynamic>).entries)
      int.parse(entry.key): (entry.value as num).toDouble(),
  };
}

double _double(dynamic v) => (v as num?)?.toDouble() ?? 0.0;

/// **The** shape a player takes in every answer (ADR-227).
///
/// ⭐⭐ There used to be five, and a separate `PlayerRef` class to cope with the smallest of them. The API
/// now describes a player one way everywhere, so the client needs one class and one widget — ⚠️ *a model
/// that needed two classes was telling you the contract had two answers to one question.*
class PlayerSummary {
  PlayerSummary({
    required this.id,
    required this.name,
    required this.team,
    required this.position,
    required this.price,
    required this.xp,
    required this.status,
    required this.chance,
    required this.minutesWeight,
    required this.leaving,
    required this.byGameweek,
  });

  factory PlayerSummary.fromJson(Map<String, dynamic> json) => PlayerSummary(
    id: json['id'] as int,
    name: json['web_name'] as String,
    team: json['team'] as String,
    position: json['position'] as String,
    price: _double(json['price']),
    xp: _double(json['xp']),
    status: json['status'] as String? ?? 'a',
    chance: json['chance'] as int?,
    minutesWeight: (json['minutes_weight'] as num?)?.toDouble() ?? 1.0,
    leaving: json['leaving'] as Map<String, dynamic>?,
    byGameweek: _gameweeks(json['by_gameweek']),
  );

  final int id;
  final String name;
  final String team;
  final String position;
  final double price;

  /// Expected points over the **request's** horizon — already summed and rounded by the server.
  final double xp;

  /// FPL's own availability letter: `a` available · `d` doubtful · `i` injured · `s` suspended · `u` gone.
  final String status;

  /// ⚠️ Percentage chance of playing, or null when FPL has no opinion. ⭐ **Null and 100 are different
  /// things** — ADR-206 found the app treating every doubt as a certainty because a flag was read as a
  /// verdict rather than a probability.
  final int? chance;

  /// Expected-minutes weight, 0–1 (ADR-038). 1.0 when unknown.
  final double minutesWeight;

  /// ⚠️ **The press says this player is leaving the league** (ADR-151→156), or null. ⭐ Not derivable from
  /// `status`: FPL still reports an agreed transfer as fully available, which is the whole reason this
  /// field exists on six surfaces.
  final Map<String, dynamic>? leaving;

  /// Per-gameweek xP, keyed by the real gameweek number. Empty when the endpoint does not carry it.
  final Map<int, double> byGameweek;

  bool get isLeaving => leaving != null;
  bool get isDoubtful => status == 'd';

  /// ⭐ Anything that stops him scoring, in one question — the check a squad screen actually wants.
  bool get isUnavailable => status == 'i' || status == 's' || status == 'u';
}

/// `POST /api/v1/squad/analysis`
class SquadAnalysis {
  SquadAnalysis({
    required this.horizon,
    required this.gameweeks,
    required this.projectedXp,
    required this.benchXp,
    required this.value,
    required this.xi,
    required this.bench,
    required this.issues,
    required this.weakest,
    required this.topPick,
    required this.clubCounts,
    required this.concentratedClubs,
  });

  factory SquadAnalysis.fromJson(Map<String, dynamic> json) {
    List<PlayerSummary> players(String key) => ((json[key] as List?) ?? [])
        .map((p) => PlayerSummary.fromJson(p as Map<String, dynamic>))
        .toList();
    return SquadAnalysis(
      horizon: json['horizon'] as int,
      gameweeks: ((json['gameweeks'] as List?) ?? []).cast<int>(),
      projectedXp: _double(json['projected_xp']),
      benchXp: _double(json['bench_xp']),
      value: _double(json['value']),
      xi: players('xi'),
      bench: players('bench'),
      issues: players('issues'),
      weakest: players('weakest'),
      topPick: json['top_pick'] == null
          ? null
          : PlayerSummary.fromJson(json['top_pick'] as Map<String, dynamic>),
      clubCounts: ((json['club_counts'] as Map?) ?? {}).map(
        (k, v) => MapEntry('$k', v as int),
      ),
      concentratedClubs: ((json['concentrated_clubs'] as List?) ?? [])
          .cast<String>(),
    );
  }

  final int horizon;
  final List<int> gameweeks;
  final double projectedXp;
  final double benchXp;
  final double value;
  final List<PlayerSummary> xi;
  final List<PlayerSummary> bench;

  /// Players worth flagging — injured, suspended, doubtful, **or reported to be leaving**.
  final List<PlayerSummary> issues;
  final List<PlayerSummary> weakest;

  /// ⚠️ **Null when nobody is eligible**, which is rarer than it sounds but real: `analyse_squad` drops a
  /// reported leaver from the captainable set, so a squad can have a best player and no top pick.
  final PlayerSummary? topPick;
  final Map<String, int> clubCounts;

  /// Clubs you hold three of — the FPL maximum, so a blank gameweek hurts three times.
  final List<String> concentratedClubs;
}

/// One swap, as the transfer search ranks them.
class TransferMove {
  TransferMove({
    required this.position,
    required this.out,
    required this.incoming,
    required this.gain,
    required this.outOnBench,
    this.displaces,
  });

  factory TransferMove.fromJson(Map<String, dynamic> json) => TransferMove(
    position: json['position'] as String,
    out: PlayerSummary.fromJson(json['out'] as Map<String, dynamic>),
    // ⚠️ `in` is a Dart keyword, so the field cannot share the wire's name.
    incoming: PlayerSummary.fromJson(json['in'] as Map<String, dynamic>),
    gain: _double(json['gain']),
    outOnBench: json['out_on_bench'] as bool? ?? false,
    displaces: json['displaces'] == null
        ? null
        : PlayerSummary.fromJson(json['displaces'] as Map<String, dynamic>),
  );

  final String position;
  final PlayerSummary out;
  final PlayerSummary incoming;

  /// ⭐⭐ **Who stops starting if you make this move** (ADR-273), or null when the lineup does not move.
  ///
  /// ⚠️⚠️ The owner: *"Leno to Tzolakis won't provide a +2.2 xP as I will be playing Pickford."* He is
  /// right, and so is the number — they answer different questions. The gain is measured on the **best
  /// legal XI**, so buying a keeper better than the one you start is worth the difference **if you also
  /// start him**. ⭐ *A conditional gain stated unconditionally is not a number, it is a promise.*
  final PlayerSummary? displaces;

  /// ⭐ True when banking the gain needs a **second action** — the transfer alone will not do it.
  bool get needsLineupChange => displaces != null;

  /// Expected points gained **by the starting XI** over the request's horizon.
  final double gain;

  /// ⭐ Selling a benched player lifts the XI by nothing, so a gain here means something different.
  final bool outOnBench;
}

/// `POST /api/v1/squad/transfers`
class TransfersAnswer {
  TransfersAnswer({
    required this.horizon,
    required this.bank,
    required this.count,
    required this.coordinated,
    required this.longerWindow,
    required this.moves,
  });

  factory TransfersAnswer.fromJson(Map<String, dynamic> json) =>
      TransfersAnswer(
        horizon: json['horizon'] as int,
        bank: _double(json['bank']),
        count: json['count'] as int,
        coordinated: json['coordinated'] as bool,
        longerWindow: json['longer_window'] as int?,
        moves: ((json['moves'] as List?) ?? [])
            .map((m) => TransferMove.fromJson(m as Map<String, dynamic>))
            .toList(),
      );

  final int horizon;
  final double bank;
  final int count;

  /// ⭐ **A plan, not a menu.** When true the moves share a bank and their gains add up; when false they
  /// are alternatives, and adding two of them double-counts the same money.
  final bool coordinated;

  /// The wider window a near-tie was broken on (ADR-209), or null when the ranking window already is it.
  final int? longerWindow;
  final List<TransferMove> moves;
}

/// One captaincy candidate for the coming gameweek.
///
/// ⭐ A [PlayerSummary] plus the facts about the **fixture** — which is the only thing a pick adds to a
/// player. ⚠️ The xP decomposition (`rate`, `ep_next`, `defcon_xp`) used to ride along and no longer does:
/// that is the model's working, not the answer.
class CaptainPick {
  CaptainPick({
    required this.player,
    required this.opponent,
    required this.venue,
    required this.difficulty,
    required this.penaltyTaker,
  });

  factory CaptainPick.fromJson(Map<String, dynamic> json) => CaptainPick(
    player: PlayerSummary.fromJson(json),
    opponent: json['opponent'] as String?,
    venue: json['venue'] as String?,
    difficulty: json['difficulty'] as int?,
    penaltyTaker: json['penalty_taker'] as bool? ?? false,
  );

  final PlayerSummary player;
  final String? opponent;

  /// `H` or `A`. Null when the fixture is unknown.
  final String? venue;
  final int? difficulty;
  final bool penaltyTaker;

  /// ⚠️ **Next gameweek only**, whatever horizon was requested — captaincy is a one-week bet.
  double get xp => player.xp;
  String get name => player.name;

  /// ⭐ Read from the shared shape rather than a separate `doubtful` flag — *two representations of one
  /// fact are two things that can disagree*.
  bool get doubtful => player.isDoubtful;
}

/// `POST /api/v1/squad/captain`
class CaptainAnswer {
  CaptainAnswer({required this.gameweek, required this.picks});

  factory CaptainAnswer.fromJson(Map<String, dynamic> json) => CaptainAnswer(
    gameweek: json['gameweek'] as int?,
    picks: ((json['picks'] as List?) ?? [])
        .map((p) => CaptainPick.fromJson(p as Map<String, dynamic>))
        .toList(),
  );

  final int? gameweek;
  final List<CaptainPick> picks;
}

/// `POST /api/v1/squad/route` — *"what would it take to field X?"*
class RouteAnswer {
  RouteAnswer({
    required this.horizon,
    required this.target,
    required this.owned,
    required this.routes,
    required this.blocked,
    required this.shortfall,
  });

  factory RouteAnswer.fromJson(Map<String, dynamic> json) => RouteAnswer(
    horizon: json['horizon'] as int,
    target: PlayerSummary.fromJson(json['target'] as Map<String, dynamic>),
    owned: json['owned'] as bool? ?? false,
    routes: ((json['routes'] as List?) ?? []).cast<Map<String, dynamic>>(),
    blocked: ((json['blocked'] as List?) ?? []).cast<Map<String, dynamic>>(),
    shortfall: (json['shortfall'] as num?)?.toDouble(),
  );

  final int horizon;
  final PlayerSummary target;

  /// ⭐ *"You already own him"* is an answer to the question, not an empty result.
  final bool owned;

  /// ⚠️ **Left as raw maps**, because these still carry whole database rows — see the library note.
  final List<Map<String, dynamic>> routes;

  /// ⭐ **A blocked route is information**: *"short by £0.6m"* answers the question where an empty list
  /// looks like the question was not understood.
  final List<Map<String, dynamic>> blocked;

  /// How much more money the cheapest blocked route needs, in £m. Null when nothing is blocked on price.
  final double? shortfall;

  bool get isAffordable => routes.isNotEmpty;
}

/// `POST /api/v1/squad/build` — the wildcard question.
class BuildAnswer {
  BuildAnswer({
    required this.horizon,
    required this.budget,
    required this.status,
    required this.selected,
    required this.totalCost,
    required this.projectedXp,
    required this.xiXp,
  });

  factory BuildAnswer.fromJson(Map<String, dynamic> json) => BuildAnswer(
    horizon: json['horizon'] as int,
    budget: _double(json['budget']),
    status: json['status'] as String,
    selected: ((json['selected'] as List?) ?? [])
        .map((p) => BuiltPlayer.fromJson(p as Map<String, dynamic>))
        .toList(),
    totalCost: _double(json['total_cost']),
    projectedXp: _double(json['projected_xp']),
    xiXp: (json['xi_xp'] as num?)?.toDouble(),
  );

  final int horizon;
  final double budget;

  /// ⚠️ **The solver's own word — check it.** `Optimal` means a squad was found; anything else (`Infeasible`)
  /// means *nothing fits these constraints*, which is an answer, not a failure. ⭐ A client that ignored it
  /// would render an empty pitch with no reason given.
  final String status;

  /// ⚠️ **Not bare summaries.** A built squad has to say **who starts** and **who was forced**, and
  /// flattening it to a player list threw both away — ⭐ *a draft you cannot read the shape of is a list
  /// of fifteen names.*
  final List<BuiltPlayer> selected;

  /// The eleven the solver would start.
  List<BuiltPlayer> get xi => [
    for (final p in selected)
      if (!p.bench) p,
  ];

  /// The four it would not — ⚠️ in the solver's order, which is **not** FPL's substitution order.
  List<BuiltPlayer> get bench => [
    for (final p in selected)
      if (p.bench) p,
  ];

  /// ⭐ `Optimal` is the only status that means the fifteen below are the best available. Anything else —
  /// `Infeasible` above all — means the constraints could not be met, and ⚠️ *rendering an empty squad
  /// under a heading is how "no answer" gets read as "no good players".*
  bool get solved => status == 'Optimal' && selected.length == 15;
  final double totalCost;
  final double projectedXp;

  /// ⭐⭐ **What the manager actually scores** — only the eleven count. A bench-aware draft reads
  /// *lower* on the all-fifteen total while fielding a *better* side, so ⚠️ *a headline that falls
  /// when the answer improves is a headline that will be optimised against.*
  ///
  /// ⚠️ Null when no bench was designated: there is then no eleven to name, and *a zero there would
  /// read as a terrible squad.*
  final double? xiXp;

  bool get isOptimal => status == 'Optimal';
}

/// One upcoming fixture — a cell on a pitch card.
class Fixture {
  Fixture({
    required this.gameweek,
    required this.opponent,
    required this.venue,
    required this.difficulty,
  });

  factory Fixture.fromJson(Map<String, dynamic> json) => Fixture(
    gameweek: json['gameweek'] as int?,
    opponent: json['opponent'] as String,
    venue: json['venue'] as String,
    difficulty: json['difficulty'] as int? ?? 3,
  );

  final int? gameweek;
  final String opponent;

  /// `H` or `A`.
  final String venue;

  /// FDR 1–5. ⭐ Mirrors the official FPL app's scale so it reads familiarly.
  final int difficulty;

  String get label => '$opponent ($venue)';
}

/// What a player's price is doing, and the evidence for it.
///
/// ⚠️ **Direction only.** The engine answers rise/fall/stable against a live percentile — it does **not**
/// answer *when*, so there is no "Tonight" or "in 2 days" here. ⭐ *A number that looks authoritative and
/// is not computed is worse than an absent one.* The net transfers are the fact behind the call.
class PriceMove {
  PriceMove({
    required this.direction,
    required this.netTransfers,
    required this.changedThisGameweek,
  });

  factory PriceMove.fromJson(Map<String, dynamic> json) => PriceMove(
    direction: json['direction'] as String? ?? 'stable',
    netTransfers: json['net_transfers'] as int? ?? 0,
    changedThisGameweek:
        (json['changed_this_gameweek'] as num?)?.toDouble() ?? 0.0,
  );

  /// `rise` · `fall` · `stable`.
  final String direction;

  /// Transfers in minus out this gameweek. ⭐ Positive means the crowd is buying.
  final int netTransfers;

  /// How much his price has already moved this gameweek, in £m.
  final double changedThisGameweek;

  bool get rising => direction == 'rise';
  bool get falling => direction == 'fall';
}

/// `POST /api/v1/squad/my-team` — everything the landing pitch draws, in one call.
///
/// ⭐⭐ **One call because the pitch needs ten things `analysis` does not return.** Fetching them
/// separately is five round trips before anything renders, on the client whose architecture was justified
/// by measuring payload.
class MyTeam {
  MyTeam({
    required this.squadName,
    required this.isDraft,
    required this.fplPlayerIds,
    required this.bank,
    required this.value,
    required this.freeTransfers,
    required this.activeChip,
    required this.gameweek,
    required this.deadlineLabel,
    required this.deadlineWhen,
    required this.deadlineCountdown,
    required this.captainId,
    required this.viceCaptainId,
    required this.analysis,
    required this.kits,
    required this.fixtures,
    required this.prices,
    required this.run,
    required this.runXp,
    required this.suggestedLineup,
    required this.data,
    required this.signalKeys,
    required this.swaps,
    required this.benchedIds,
    required this.benchRoles,
  });

  factory MyTeam.fromJson(Map<String, dynamic> json) {
    final squad = json['squad'] as Map<String, dynamic>;
    final deadline = (json['deadline'] as Map<String, dynamic>?) ?? const {};
    return MyTeam(
      squadName: squad['name'] as String? ?? '',
      isDraft: json['draft'] as bool? ?? false,
      fplPlayerIds: ((json['fpl_player_ids'] as List?) ?? const []).cast<int>(),
      bank: (squad['bank'] as num?)?.toDouble(),
      value: (squad['value'] as num?)?.toDouble(),
      freeTransfers: json['free_transfers'] as int? ?? 1,
      activeChip: squad['active_chip'] as String?,
      gameweek: json['gameweek'] as int?,
      deadlineLabel: deadline['label'] as String? ?? '',
      deadlineWhen: deadline['when'] as String? ?? '',
      deadlineCountdown: deadline['countdown'] as String? ?? '',
      captainId: squad['captain_id'] as int?,
      viceCaptainId: squad['vice_captain_id'] as int?,
      analysis: SquadAnalysis.fromJson(
        json['analysis'] as Map<String, dynamic>,
      ),
      // ⭐ Keyed by **club short name** and by **role** — strings already, so JSON changes nothing on the
      // way in. Keying these by player id would repeat `by_gameweek`'s trap.
      kits: ((json['kits'] as Map?) ?? {}).map(
        (club, urls) => MapEntry('$club', (
          outfield: (urls as Map)['outfield'] as String? ?? '',
          gk: urls['gk'] as String? ?? '',
        )),
      ),
      fixtures: ((json['fixtures'] as Map?) ?? {}).map(
        (club, list) => MapEntry(
          '$club',
          ((list as List?) ?? const [])
              .map((f) => Fixture.fromJson((f as Map).cast<String, dynamic>()))
              .toList(),
        ),
      ),
      // ⚠️ Keyed by player id, which crosses as a string — parsed back here, once, so nothing downstream
      // sorts or compares it as text.
      prices: ((json['prices'] as Map?) ?? {}).map(
        (id, move) => MapEntry(
          int.parse('$id'),
          PriceMove.fromJson((move as Map).cast<String, dynamic>()),
        ),
      ),
      run: json['run'] as int? ?? 1,
      // ⚠️⚠️ **The run card drew three columns and had one number** (ADR-242). `by_gameweek` follows the
      // request's `horizon`, which is 1 because the headline is a this-week projection — so two of the
      // three columns always read "—". `run_xp` carries the window the card actually draws, computed
      // separately so the headline stays a one-week number.
      data: DataFreshness.fromJson(
        (json['data'] as Map<String, dynamic>?) ?? const {},
      ),
      signalKeys: [for (final k in (json['signal_keys'] as List? ?? [])) '$k'],
      swaps: {
        for (final row in (json['swaps'] as List? ?? []))
          (row as Map<String, dynamic>)['id'] as int: [
            for (final i in (row['with'] as List? ?? [])) i as int,
          ],
      },
      benchedIds: {
        for (final row in (json['swaps'] as List? ?? []))
          if ((row as Map<String, dynamic>)['benched'] == true)
            row['id'] as int,
      },
      suggestedLineup: json['suggested_lineup'] == null
          ? null
          : SuggestedLineup.fromJson(
              json['suggested_lineup'] as Map<String, dynamic>,
            ),
      runXp: {
        for (final row in (json['run_xp'] as List? ?? []))
          (row as Map<String, dynamic>)['id'] as int: {
            for (final e in ((row['by_gameweek'] as Map?) ?? {}).entries)
              int.parse('${e.key}'): (e.value as num).toDouble(),
          },
      },
      benchRoles: ((json['bench_roles'] as Map?) ?? {}).map(
        (role, id) => MapEntry('$role', id as int),
      ),
    );
  }

  final String squadName;

  /// ⭐⭐ **The server's word on whether this is the real team.** A client can forget to mention it; a field
  /// cannot — and an app that shows a plan as your squad is lying about something you can act on.
  final bool isDraft;

  /// The squad FPL actually holds, whatever is being displayed. ⭐ What a saved draft is checked against,
  /// rather than trusting that nothing moved while the app was closed.
  final List<int> fplPlayerIds;

  /// ⚠️ **Null means *not known*, never zero.** An empty bank is a real position; *"we could not read your
  /// bank"* is not, and showing the second as the first tells the affordability maths every transfer is
  /// unaffordable.
  final double? bank;

  /// FPL's team value — ⭐ **includes the bank**, which is why it exceeds what the fifteen cost.
  final double? value;

  /// ⚠️ **Supplied by the client, not by FPL**, which publishes bank and value but keeps free transfers
  /// behind a login. Echoed by the server so a header shows what the answer assumed (ADR-191).
  final int freeTransfers;

  /// `bboost` · `3xc` · `freehit` · `wildcard`, or null.
  final String? activeChip;

  final int? gameweek;

  /// ⚠️ **Rendered as given** (ADR-086). It already carries the timezone and the countdown — re-deriving
  /// *"in 18 days"* on the client would be a second clock, and the two would disagree by however long the
  /// app had been open.
  final String deadlineLabel;

  /// ⚠️ **The manager's own armbands**, not the engine's pick. `analysis.topPick` is the recommendation;
  /// these are what is actually set. ⭐ Showing one as the other is how an app tells you what you did wrong
  /// while pretending it is what you did.
  final int? captainId;
  final int? viceCaptainId;

  final SquadAnalysis analysis;
  final Map<String, ({String outfield, String gk})> kits;

  /// A club's next few fixtures, in order. ⭐ Keyed by club, so three players from one team share one list.
  final Map<String, List<Fixture>> fixtures;

  final Map<int, PriceMove> prices;

  /// How many fixtures each club's list holds.
  final int run;

  /// The deadline as two short facts — ⭐ *"Sat 10 Oct, 11:00"* and *"in 17 days, 11h"* (ADR-253).
  ///
  /// ⚠️ [deadlineLabel] is the web's 96-character prose line; on a phone it wrapped to three, spending
  /// ~40pt of the screen's most valuable space on a match count nobody acts on from the pitch.
  final String deadlineWhen;
  final String deadlineCountdown;

  /// How old this data is, and whether a finished gameweek is missing from it (ADR-248).
  final DataFreshness data;

  /// Every signal about your fifteen, by stable key — ⭐ **keys, not signals** (ADR-256). The badge is a
  /// count, and a count does not need the things it counted.
  final List<String> signalKeys;

  /// Player id → the players he may legally change places with (ADR-246).
  ///
  /// ⭐⭐ **Decided by the engine, not here.** FPL's formation limits live in `XI_FLEX` and are enforced by
  /// `legal_xi_issues`; working them out again in Dart would be a second implementation of a rule the
  /// server already owns. ⚠️ Keepers are the case that catches people — a GK may only ever change places
  /// with the other GK.
  final Map<int, List<int>> swaps;

  /// Whether a player is currently on the bench, as the server declared it.
  final Set<int> benchedIds;

  List<int> swapsFor(int playerId) => swaps[playerId] ?? const [];

  /// The best legal XI from the players you already own, or null when yours already is it (ADR-244).
  final SuggestedLineup? suggestedLineup;

  /// Player id → gameweek → xP, across the **run** window rather than the request's horizon (ADR-242).
  final Map<int, Map<int, double>> runXp;

  /// ⭐ Falls back to the player's own `byGameweek` when the server did not send a run — an older build
  /// then shows one real number and two dashes, which is what it did before, rather than nothing.
  Map<int, double> runXpFor(PlayerSummary p) => runXp[p.id] ?? p.byGameweek;

  /// Role → player id: `1st` · `2nd` · `3rd` · `GK`, the order FPL will actually substitute in.
  final Map<String, int> benchRoles;

  /// The kit for a player, keeper variant included.
  String kitFor(PlayerSummary p) {
    final club = kits[p.team];
    if (club == null) return '';
    return p.position == 'GK' ? club.gk : club.outfield;
  }

  List<Fixture> runFor(PlayerSummary p) => fixtures[p.team] ?? const [];

  Fixture? fixtureFor(PlayerSummary p) {
    final list = runFor(p);
    return list.isEmpty ? null : list.first;
  }

  PriceMove? priceFor(PlayerSummary p) => prices[p.id];

  /// A player's name from his id — ⭐ so a suggestion that travels as ids can be spoken as names.
  /// ⚠️ Empty, never a placeholder, for someone outside the squad: a strip reading "Start ???" is worse
  /// than one that leaves him out.
  String nameOf(int id) {
    for (final p in [...analysis.xi, ...analysis.bench]) {
      if (p.id == id) return p.name;
    }
    return '';
  }

  /// A copy with different armbands — ⭐ for a **draft**, whose captain the server never sees because it
  /// changes nothing the server computes.
  MyTeam withArmbands({int? captainId, int? viceCaptainId}) => MyTeam(
    squadName: squadName,
    isDraft: isDraft,
    fplPlayerIds: fplPlayerIds,
    bank: bank,
    value: value,
    freeTransfers: freeTransfers,
    activeChip: activeChip,
    gameweek: gameweek,
    deadlineLabel: deadlineLabel,
    deadlineWhen: deadlineWhen,
    deadlineCountdown: deadlineCountdown,
    captainId: captainId ?? this.captainId,
    viceCaptainId: viceCaptainId ?? this.viceCaptainId,
    analysis: analysis,
    kits: kits,
    fixtures: fixtures,
    prices: prices,
    run: run,
    runXp: runXp,
    suggestedLineup: suggestedLineup,
    data: data,
    signalKeys: signalKeys,
    swaps: swaps,
    benchedIds: benchedIds,
    benchRoles: benchRoles,
  );

  /// The bench in the order FPL will use it, rather than the order it happened to arrive in.
  List<PlayerSummary> get orderedBench {
    const order = ['1st', '2nd', '3rd', 'GK'];
    final byId = {for (final p in analysis.bench) p.id: p};
    final out = <PlayerSummary>[];
    for (final role in order) {
      final id = benchRoles[role];
      if (id != null && byId.containsKey(id)) out.add(byId.remove(id)!);
    }
    return [...out, ...byId.values];
  }
}

/// One candidate to replace an owned player (ADR-226).
class Replacement {
  Replacement({
    required this.player,
    required this.affordable,
    required this.overBy,
  });

  factory Replacement.fromJson(Map<String, dynamic> json) => Replacement(
    player: PlayerSummary.fromJson(json),
    affordable: json['affordable'] as bool? ?? true,
    overBy: (json['over_by'] as num?)?.toDouble() ?? 0.0,
  );

  final PlayerSummary player;

  /// ⚠️ **False does not mean unavailable.** An over-budget candidate is offered deliberately: FPL prices
  /// drift, and a move you cannot quite afford today is a plan rather than an error.
  final bool affordable;

  /// How far over budget, in £m. ⭐ 0.0 when affordable — one type to read, and a meaningful zero.
  final double overBy;
}

/// `POST /api/v1/squad/replacements`
class ReplacementsAnswer {
  ReplacementsAnswer({
    required this.out,
    required this.budget,
    required this.candidates,
  });

  factory ReplacementsAnswer.fromJson(Map<String, dynamic> json) =>
      ReplacementsAnswer(
        out: PlayerSummary.fromJson(json['out'] as Map<String, dynamic>),
        budget: (json['budget'] as num).toDouble(),
        candidates: ((json['candidates'] as List?) ?? [])
            .map((c) => Replacement.fromJson(c as Map<String, dynamic>))
            .toList(),
      );

  final PlayerSummary out;

  /// ⭐ Sale price **plus** bank, stated so a screen need not make the reader add two numbers that appear
  /// on different rows.
  final double budget;

  final List<Replacement> candidates;
}

/// One gameweek a player has already played.
class Appearance {
  Appearance({
    required this.gameweek,
    required this.points,
    required this.minutes,
    required this.opponent,
    required this.home,
  });

  factory Appearance.fromJson(Map<String, dynamic> json) => Appearance(
    gameweek: json['gameweek'] as int?,
    points: json['points'] as int? ?? 0,
    minutes: json['minutes'] as int? ?? 0,
    // ⭐⭐ **Who it was against** (ADR-242). A run of bare numbers cannot tell a quiet week from a hard
    // one — ⚠️ *two blanks against City and Arsenal say something completely different from two blanks
    // against the bottom two.*
    opponent: json['opponent'] as String?,
    home: json['home'] as bool? ?? true,
  );

  /// ⚠️ Null, never a guess, when the club is unknown — an away trip to "???" is worse than none.
  final String? opponent;
  final bool home;

  /// ⭐ Lower case away, upper case home — the convention the fixture ticker already uses, so a reader
  /// who has seen one has read the other.
  String get versus => opponent == null
      ? '—'
      : (home ? opponent!.toUpperCase() : opponent!.toLowerCase());

  final int? gameweek;
  final int points;

  /// ⭐ Shown because **ten points off the bench is not ten points from a starter** — a form line without
  /// minutes flatters a player who came on for the last twenty.
  final int minutes;

  bool get played => minutes > 0;
}

/// One side of a **Boot Battle**.
class Contender {
  Contender({required this.player, required this.photo, required this.recent});

  factory Contender.fromJson(Map<String, dynamic> json) => Contender(
    player: PlayerSummary.fromJson(json),
    photo: json['photo'] as String? ?? '',
    recent: ((json['recent'] as List?) ?? const [])
        .map((r) => Appearance.fromJson((r as Map).cast<String, dynamic>()))
        .toList(),
  );

  final PlayerSummary player;

  /// His mugshot — ⭐ the web's compare header has had one since ADR-110.
  final String photo;

  /// His last five gameweeks, oldest first.
  final List<Appearance> recent;
}

/// One row of the stat grid — ⭐ `winner` is decided by the engine, which knows that a **lower** expected
/// goals-conceded is the better number.
class CompareRow {
  CompareRow({
    required this.label,
    required this.a,
    required this.b,
    required this.winner,
  });

  factory CompareRow.fromJson(Map<String, dynamic> json) => CompareRow(
    label: json['label'] as String,
    a: json['a'] as String,
    b: json['b'] as String,
    winner: json['winner'] as String?,
  );

  final String label;
  final String a;
  final String b;

  /// `a` · `b` · null for a tie, a missing value, or a stat with no better direction (ownership).
  final String? winner;
}

/// `POST /api/v1/compare` — Boot Battle.
class BootBattle {
  BootBattle({
    required this.a,
    required this.b,
    required this.rows,
    required this.gameweeks,
  });

  factory BootBattle.fromJson(Map<String, dynamic> json) => BootBattle(
    a: Contender.fromJson(json['a'] as Map<String, dynamic>),
    b: Contender.fromJson(json['b'] as Map<String, dynamic>),
    rows: ((json['rows'] as List?) ?? const [])
        .map((r) => CompareRow.fromJson((r as Map).cast<String, dynamic>()))
        .toList(),
    gameweeks: ((json['gameweeks'] as List?) ?? const []).cast<int>(),
  );

  final Contender a;
  final Contender b;
  final List<CompareRow> rows;
  final List<int> gameweeks;

  /// How many rows each side wins. ⭐ A headline, not a verdict — ADR-197 gave the DNA comparison **no**
  /// verdict on purpose, and the same reasoning holds: a count of stats is not a recommendation.
  (int, int) get tally => (
    rows.where((r) => r.winner == 'a').length,
    rows.where((r) => r.winner == 'b').length,
  );
}

/// `POST /api/v1/player` — one player in full, the card behind a row (ADR-237).
class PlayerCard {
  PlayerCard({
    required this.player,
    required this.photo,
    required this.stats,
    required this.recent,
    required this.fixtures,
  });

  factory PlayerCard.fromJson(Map<String, dynamic> json) => PlayerCard(
    player: PlayerSummary.fromJson(json['player'] as Map<String, dynamic>),
    photo: json['photo'] as String? ?? '',
    stats: ((json['stats'] as List?) ?? const [])
        .map(
          (r) => (label: (r as Map)['label'] as String, value: '${r['value']}'),
        )
        .toList(),
    recent: ((json['recent'] as List?) ?? const [])
        .map((r) => Appearance.fromJson((r as Map).cast<String, dynamic>()))
        .toList(),
    fixtures: ((json['fixtures'] as List?) ?? const [])
        .map((f) => Fixture.fromJson((f as Map).cast<String, dynamic>()))
        .toList(),
  );

  final PlayerSummary player;

  /// His mugshot — ⚠️ **on a named card, never on the pitch** (ADR-255/084).
  final String photo;

  /// ⭐ **Already ordered for his position** by the server — a defender's card leads with expected goals
  /// conceded, a forward's with goals. ⚠️ Re-sorting these on the client would throw that away.
  final List<({String label, String value})> stats;

  final List<Appearance> recent;
  final List<Fixture> fixtures;
}

/// The lineup the engine would field, and what it is worth (ADR-244).
///
/// ⚠️ **Lineup only — never transfers.** Starting a player you already own is free and reversible; a
/// transfer costs points and cannot be taken back. ⭐ *One button must not do both, whatever the xP says.*
class SuggestedLineup {
  SuggestedLineup({
    required this.start,
    required this.bench,
    required this.bringIn,
    required this.drop,
    required this.gain,
  });

  factory SuggestedLineup.fromJson(Map<String, dynamic> json) =>
      SuggestedLineup(
        start: [for (final i in (json['start'] as List? ?? [])) i as int],
        bench: [for (final i in (json['bench'] as List? ?? [])) i as int],
        bringIn: [for (final i in (json['bring_in'] as List? ?? [])) i as int],
        drop: [for (final i in (json['drop'] as List? ?? [])) i as int],
        gain: (json['gain'] as num?)?.toDouble() ?? 0,
      );

  final List<int> start;
  final List<int> bench;
  final List<int> bringIn;
  final List<int> drop;

  /// Expected points, this gameweek, from making the swaps.
  final double gain;

  int get changes => bringIn.length;
}

/// One club's fingerprint (ADR-247).
///
/// ⭐ Every axis is a **percentile**, so 74 means the same thing on Attacking Threat as on Squad Depth —
/// which is what lets eight different units share one scale, and one row of bars.
class ClubDna {
  ClubDna({
    required this.team,
    required this.name,
    required this.grade,
    required this.score,
    required this.yours,
    required this.axes,
    required this.insights,
    required this.fixtures,
    required this.form,
    required this.keyPlayers,
  });

  factory ClubDna.fromJson(Map<String, dynamic> json) => ClubDna(
    team: json['team'] as String? ?? '',
    name: json['name'] as String? ?? '',
    grade: json['grade'] as String? ?? '',
    score: json['score'] as int? ?? 0,
    yours: json['yours'] as bool? ?? false,
    axes: [
      for (final a in (json['axes'] as List? ?? []))
        DnaAxis.fromJson(a as Map<String, dynamic>),
    ],
    insights: [
      for (final i in (json['insights'] as List? ?? []))
        (kind: '${(i as Map<String, dynamic>)['kind']}', text: '${i['text']}'),
    ],
    fixtures: [
      for (final f in (json['fixtures'] as List? ?? []))
        Fixture.fromJson(f as Map<String, dynamic>),
    ],
    form: [
      for (final f in (json['form'] as List? ?? []))
        (
          gameweek:
              ((f as Map<String, dynamic>)['gameweek'] as num?)?.toInt() ?? 0,
          result: '${f['result']}',
        ),
    ],
    keyPlayers: KeyPlayers.fromJson(
      (json['key_players'] as Map<String, dynamic>?) ?? const {},
    ),
  );

  final String team;
  final String name;
  final String grade;
  final int score;

  /// Whether you hold anyone from this club — ⚠️ a mark, never a filter.
  final bool yours;
  final List<DnaAxis> axes;
  final List<({String kind, String text})> insights;

  /// Where the club is going — ⭐ six, not the pitch card's three: *a club's run is a longer question
  /// than a player's next card.*
  final List<Fixture> fixtures;

  /// How it has been going — W/D/L, oldest first.
  final List<({int gameweek, String result})> form;

  /// Who to buy, and **which season the table is from**.
  final KeyPlayers keyPlayers;
}

/// The club's best FPL assets — ⚠️ **with the season named**, because the ranking needs ~900 minutes and
/// falls back to last season until about GW10 (ADR-126). ⭐ *A table from a different season that does not
/// say so is the most quietly wrong thing on a page.*
class KeyPlayers {
  KeyPlayers({required this.season, required this.players});

  factory KeyPlayers.fromJson(Map<String, dynamic> json) => KeyPlayers(
    season: json['season'] as String?,
    players: [
      for (final p in (json['players'] as List? ?? []))
        (
          name: '${(p as Map<String, dynamic>)['name']}',
          position: '${p['pos']}',
          xgi90: (p['xgi90'] as num?)?.toDouble() ?? 0,
          pts90: (p['pts90'] as num?)?.toDouble() ?? 0,
          minutesPct: (p['minpct'] as num?)?.toInt() ?? 0,
          owned: (p['own'] as num?)?.toDouble() ?? 0,
        ),
    ],
  );

  /// Null when the table is **this** season's. ⭐ A label only where it changes the reading.
  final String? season;
  final List<
    ({
      String name,
      String position,
      double xgi90,
      double pts90,
      int minutesPct,
      double owned,
    })
  >
  players;
}

class DnaAxis {
  DnaAxis({
    required this.label,
    required this.sublabel,
    required this.value,
    required this.percentile,
  });

  factory DnaAxis.fromJson(Map<String, dynamic> json) => DnaAxis(
    label: json['label'] as String? ?? '',
    sublabel: json['sublabel'] as String? ?? '',
    value: (json['value'] as num?)?.toDouble() ?? 0,
    percentile: (json['percentile'] as num?)?.toInt(),
  );

  final String label;
  final String sublabel;
  final double value;

  /// ⚠️ Null means **unranked**, not zero — there was no pool to rank against.
  final int? percentile;
}

/// How old the board is — ⭐⭐ **the thing whose absence turned a stale database into a bug report**
/// (ADR-248).
///
/// ⚠️ `refreshedAt` alone is not enough. *"Updated 20 hours ago"* is fine on a Tuesday and useless the
/// evening a gameweek finishes — what matters is whether a **completed gameweek is missing**, which is a
/// different question and the one the pipeline already knows how to answer.
class DataFreshness {
  DataFreshness({
    required this.refreshedAt,
    required this.missingGameweeks,
    required this.behind,
    required this.why,
  });

  factory DataFreshness.fromJson(Map<String, dynamic> json) => DataFreshness(
    refreshedAt: DateTime.tryParse('${json['refreshed_at']}'),
    missingGameweeks: [
      for (final g in (json['missing_gameweeks'] as List? ?? [])) g as int,
    ],
    behind: json['behind'] as bool? ?? false,
    why: json['why'] as String? ?? '',
  );

  final DateTime? refreshedAt;
  final List<int> missingGameweeks;

  /// True when a **finished** gameweek is not in the data.
  final bool behind;
  final String why;

  /// ⭐ Named so a person can act: *"missing GW5"* beats *"stale"*, which is a mood.
  String get warning => missingGameweeks.isEmpty
      ? 'The board is behind — $why'
      : 'Results for GW${missingGameweeks.join(", GW")} are missing, so points, '
            'form and projections are out of date.';

  String get age {
    final at = refreshedAt;
    if (at == null) return 'unknown';
    final ago = DateTime.now().toUtc().difference(at.toUtc());
    if (ago.inMinutes < 90) return '${ago.inMinutes} min ago';
    if (ago.inHours < 36) return '${ago.inHours} hours ago';
    return '${ago.inDays} days ago';
  }
}

/// One player's fingerprint (ADR-250).
///
/// ⭐⭐ **[poolSize] is not decoration.** A percentile is only as meaningful as the field it was measured
/// in — *"84th of 31 midfielders"* is a fact, *"84th"* alone invites over-reading. Early in a season the
/// pool can be ten players, and a reader has to be able to see that.
class PlayerDna {
  PlayerDna({
    required this.player,
    required this.photo,
    required this.axes,
    required this.insights,
    required this.poolSize,
    required this.lowMinutes,
    required this.minMinutes,
    required this.recent,
    required this.unranked,
  });

  factory PlayerDna.fromJson(Map<String, dynamic> json) => PlayerDna(
    player: PlayerSummary.fromJson(json['player'] as Map<String, dynamic>),
    photo: json['photo'] as String? ?? '',
    axes: [
      for (final a in (json['axes'] as List? ?? []))
        DnaAxis.fromJson(a as Map<String, dynamic>),
    ],
    insights: [
      for (final i in (json['insights'] as List? ?? []))
        (kind: '${(i as Map<String, dynamic>)['kind']}', text: '${i['text']}'),
    ],
    poolSize: json['pool_size'] as int? ?? 0,
    lowMinutes: json['low_minutes'] as bool? ?? false,
    minMinutes: json['min_minutes'] as int? ?? 0,
    recent: [
      for (final r in (json['recent'] as List? ?? []))
        Appearance.fromJson(r as Map<String, dynamic>),
    ],
    unranked: json['unranked'] as String?,
  );

  final PlayerSummary player;

  /// His mugshot — ⚠️ **on a named card, never on the pitch** (ADR-255/084).
  final String photo;
  final List<DnaAxis> axes;
  final List<({String kind, String text})> insights;

  /// Same-position peers past the minutes floor — the field he was ranked in.
  final int poolSize;

  /// ⚠️ He is **below** the floor himself: ranked anyway, but read the shape with care (ADR-118).
  final bool lowMinutes;
  final int minMinutes;
  final List<Appearance> recent;

  /// Why there is no fingerprint, when there is none. ⭐ Saying so beats an empty radar, which reads as
  /// "this player is bad at everything".
  final String? unranked;
}

/// One club's row in the fixture ticker (ADR-265).
class TickerRow {
  TickerRow({
    required this.team,
    required this.avgDifficulty,
    required this.cells,
  });

  factory TickerRow.fromJson(Map<String, dynamic> json) => TickerRow(
    team: json['team'] as String,
    avgDifficulty: (json['avg_difficulty'] as num?)?.toDouble(),
    cells: ((json['cells'] as Map?) ?? {}).map(
      (k, v) => MapEntry(
        int.parse(k as String),
        v == null ? null : TickerCell.fromJson(v as Map<String, dynamic>),
      ),
    ),
  );

  final String team;

  /// ⚠️ Nullable: a club whose window holds no rated fixture has no average, and 0 would read as *easy*.
  final double? avgDifficulty;

  /// ⭐ **A blank gameweek is a present key with a null value**, not a missing one — *"they do not play"*
  /// is the most valuable thing a ticker says.
  final Map<int, TickerCell?> cells;
}

class TickerCell {
  TickerCell({
    required this.opponent,
    required this.venue,
    required this.difficulty,
    required this.opponents,
    required this.venues,
  });

  factory TickerCell.fromJson(Map<String, dynamic> json) => TickerCell(
    opponent: json['opponent'] as String,
    venue: json['venue'] as String,
    difficulty: (json['difficulty'] as num?)?.toInt() ?? 3,
    opponents: [
      for (final o in (json['opponents'] as List? ?? [])) o as String,
    ],
    venues: [for (final v in (json['venues'] as List? ?? [])) v as String],
  );

  final String opponent;
  final String venue;

  /// ⚠️ For a double this is the **harder** of the two — a double is only as easy as its worse fixture.
  final int difficulty;

  final List<String> opponents;
  final List<String> venues;

  /// ⭐ A double gameweek. The ticker is the view built for spotting these.
  bool get isDouble => opponents.length > 1;

  /// `CHE (H)`, or `CHE (H) + ARS (A)` for a double.
  ///
  /// ⚠️⚠️ **Falls back to the singular fields.** This was built only from `opponents`, so a cell carrying
  /// `opponent` and no list rendered as an **empty string** — a fixture that exists, shown as nothing.
  /// ⭐ *A derived field that silently returns empty is worse than one that throws*, because the screen
  /// still lays out a row for it.
  String get label {
    if (opponents.isEmpty) {
      return opponent.isEmpty ? '' : '$opponent ($venue)';
    }
    return [
      for (var i = 0; i < opponents.length; i++)
        '${opponents[i]} (${i < venues.length ? venues[i] : "?"})',
    ].join(' + ');
  }
}

class FixtureTicker {
  FixtureTicker({required this.gameweeks, required this.rows});

  factory FixtureTicker.fromJson(Map<String, dynamic> json) => FixtureTicker(
    // ⚠️ The order lives here, never in the cell map's keys.
    gameweeks: [for (final g in (json['gameweeks'] as List? ?? [])) g as int],
    rows: [
      for (final r in (json['rows'] as List? ?? []))
        TickerRow.fromJson(r as Map<String, dynamic>),
    ],
  );

  final List<int> gameweeks;

  /// ⭐ Easiest run first — the server ranks them, so every client agrees on what "easiest" means.
  final List<TickerRow> rows;
}

/// One row on a crowd leaderboard (ADR-266).
class TrendingRow {
  TrendingRow({
    required this.player,
    required this.photo,
    required this.value,
    required this.ownedBy,
    required this.tier,
    required this.owned,
    this.reasons = const [],
    this.group = '',
  });

  factory TrendingRow.fromJson(Map<String, dynamic> json) => TrendingRow(
    player: PlayerSummary.fromJson(json['player'] as Map<String, dynamic>),
    photo: json['photo'] as String? ?? '',
    value: (json['value'] as num?)?.toDouble() ?? 0,
    ownedBy: (json['owned_by'] as num?)?.toDouble(),
    tier: json['tier'] as String? ?? '',
    owned: json['owned'] as bool? ?? false,
    reasons: [for (final r in (json['reasons'] as List? ?? [])) '$r'],
    group: json['group'] as String? ?? '',
  );

  final PlayerSummary player;

  /// ⭐ A named card carries the real face (ADR-084) — the pitch deliberately does not.
  final String photo;

  /// ⚠️ **Four different quantities share this field** — net transfers, ownership %, or form, depending
  /// on the board. The board says which in its `column`; ⭐ *a number with no unit is not information.*
  final double value;

  /// ⭐ Ownership travels on every board, because *"200k bought him"* means something different at 4%
  /// than at 40%.
  final double? ownedBy;

  /// `differential` · `popular` · `template` · `essential`, or empty.
  final String tier;

  /// ⭐ Whether this is one of yours — flagged by the server so the client never matches ids itself.
  final bool owned;

  /// ⭐⭐ **Why he is here** — only the *worth a look* board carries these, and they are the board.
  /// ⚠️ Each line names its own season, because *most of the evidence is last season's and a reason
  /// without its vintage is the most misleading kind of true statement* (ADR-167).
  final List<String> reasons;

  /// ⭐ The heading this row sits under, on the boards that have them. ⚠️ Carried **per row** so the
  /// order cannot come apart from the grouping — *two lists that have to be zipped are two lists that
  /// will be.*
  final String group;
}

class TrendingBoard {
  TrendingBoard({
    required this.by,
    required this.label,
    required this.column,
    required this.caveat,
    required this.rows,
  });

  factory TrendingBoard.fromJson(Map<String, dynamic> json) => TrendingBoard(
    by: json['by'] as String? ?? 'in',
    label: json['label'] as String? ?? '',
    column: json['column'] as String? ?? '',
    caveat: json['caveat'] as String? ?? '',
    rows: [
      for (final r in (json['rows'] as List? ?? []))
        TrendingRow.fromJson(r as Map<String, dynamic>),
    ],
  );

  final String by;

  /// "most transferred in" — ⭐ the board's own words, so the screen cannot describe it differently.
  final String label;

  /// The column header for `value` — "Net in", "Own%", "Form".
  final String column;

  /// ⚠️⚠️ **Carried with the numbers, not written into the app**, so the warning cannot drift from what
  /// it is warning about.
  final String caveat;

  final List<TrendingRow> rows;
}

/// One classic league a manager is in (ADR-267).
class LeagueSummary {
  LeagueSummary({
    required this.id,
    required this.name,
    required this.size,
    required this.rank,
    required this.private,
  });

  factory LeagueSummary.fromJson(Map<String, dynamic> json) => LeagueSummary(
    id: (json['id'] as num?)?.toInt() ?? 0,
    name: json['name'] as String? ?? '',
    size: (json['size'] as num?)?.toInt() ?? 0,
    rank: (json['rank'] as num?)?.toInt(),
    private: json['private'] as bool? ?? false,
  );

  final int id;
  final String name;
  final int size;

  /// ⚠️ Nullable — a manager who has not been ranked yet has no rank, and 0 would read as *first*.
  final int? rank;

  /// ⭐ A league somebody created, rather than one FPL put you in. These lead, because *sorting by size
  /// buries the only leagues anyone means.*
  final bool private;
}

/// One row of a league table.
class LeagueStanding {
  LeagueStanding({
    required this.entry,
    required this.manager,
    required this.team,
    required this.rank,
    required this.movement,
    required this.gwPoints,
    required this.total,
  });

  factory LeagueStanding.fromJson(Map<String, dynamic> json) => LeagueStanding(
    entry: (json['entry'] as num?)?.toInt() ?? 0,
    manager: json['manager'] as String? ?? '',
    team: json['team'] as String? ?? '',
    rank: (json['rank'] as num?)?.toInt() ?? 0,
    movement: (json['movement'] as num?)?.toInt(),
    gwPoints: (json['gw_points'] as num?)?.toInt() ?? 0,
    total: (json['total'] as num?)?.toInt() ?? 0,
  );

  /// The manager's FPL entry id — ⭐ the handle a head-to-head needs.
  final int entry;
  final String manager;
  final String team;
  final int rank;

  /// Positive means climbing. ⚠️ **Null means new**, not "did not move": a manager with no previous rank
  /// has not fallen 400 places.
  final int? movement;

  final int gwPoints;
  final int total;
}

/// A player the league captained, and how many went with him.
class LeagueCaptain {
  LeagueCaptain({
    required this.player,
    required this.count,
    required this.share,
    required this.effectiveOwnership,
  });

  factory LeagueCaptain.fromJson(Map<String, dynamic> json) => LeagueCaptain(
    player: PlayerSummary.fromJson(json['player'] as Map<String, dynamic>),
    count: (json['count'] as num?)?.toInt() ?? 0,
    share: (json['share'] as num?)?.toDouble() ?? 0,
    effectiveOwnership: (json['effective_ownership'] as num?)?.toDouble() ?? 0,
  );

  final PlayerSummary player;
  final int count;

  /// ⭐ The share, not just the count — *"9 of 12"* is a different fact from *"9"*, and the reader is
  /// deciding whether to differ from a crowd.
  final double share;

  /// Ownership counting the armband twice — ⚠️ it can exceed 100%.
  final double effectiveOwnership;
}

class LeagueTable {
  LeagueTable({
    required this.leagueId,
    required this.name,
    required this.gameweek,
    required this.rows,
    required this.captainsFrom,
    required this.captains,
  });

  factory LeagueTable.fromJson(Map<String, dynamic> json) => LeagueTable(
    leagueId: (json['league_id'] as num?)?.toInt() ?? 0,
    name: json['name'] as String? ?? '',
    gameweek: (json['gameweek'] as num?)?.toInt(),
    rows: [
      for (final r in (json['rows'] as List? ?? []))
        LeagueStanding.fromJson(r as Map<String, dynamic>),
    ],
    captainsFrom: (json['captains_from'] as num?)?.toInt() ?? 0,
    captains: [
      for (final c in (json['captains'] as List? ?? []))
        LeagueCaptain.fromJson(c as Map<String, dynamic>),
    ],
  );

  final int leagueId;
  final String name;
  final int? gameweek;
  final List<LeagueStanding> rows;

  /// ⚠️ **How many squads were actually read.** A manager whose fetch fails is absent rather than fatal,
  /// and ⭐ *a partial read must never present itself as the whole league.*
  final int captainsFrom;

  final List<LeagueCaptain> captains;
}

/// One differential in a head-to-head (ADR-161/267).
class EdgePlayer {
  EdgePlayer({
    required this.player,
    required this.multiplier,
    required this.xp,
  });

  factory EdgePlayer.fromJson(Map<String, dynamic> json) => EdgePlayer(
    player: PlayerSummary.fromJson(json['player'] as Map<String, dynamic>),
    multiplier: (json['multiplier'] as num?)?.toInt() ?? 1,
    xp: (json['xp'] as num?)?.toDouble() ?? 0,
  );

  /// ⭐ The **one player shape** (ADR-227) — so a doubtful differential can be flagged as one, which the
  /// engine's own row could not do.
  final PlayerSummary player;

  /// 2 means he is that side's captain.
  final int multiplier;

  /// ⚠️ Already multiplied — what this differential is worth to that side.
  final double xp;

  bool get isCaptain => multiplier > 1;
}

class HeadToHead {
  HeadToHead({
    required this.gameweek,
    required this.gap,
    required this.sharedCount,
    required this.sharedXp,
    required this.myEdge,
    required this.theirEdge,
    required this.sameCaptain,
    required this.note,
  });

  factory HeadToHead.fromJson(Map<String, dynamic> json) => HeadToHead(
    gameweek: (json['gameweek'] as num?)?.toInt(),
    gap: (json['gap'] as num?)?.toDouble() ?? 0,
    sharedCount: (json['shared_count'] as num?)?.toInt() ?? 0,
    sharedXp: (json['shared_xp'] as num?)?.toDouble() ?? 0,
    myEdge: [
      for (final e in (json['my_edge'] as List? ?? []))
        EdgePlayer.fromJson(e as Map<String, dynamic>),
    ],
    theirEdge: [
      for (final e in (json['their_edge'] as List? ?? []))
        EdgePlayer.fromJson(e as Map<String, dynamic>),
    ],
    sameCaptain: json['same_captain'] as bool? ?? false,
    note: json['note'] as String? ?? '',
  );

  final int? gameweek;

  /// ⭐ **Positive means you are ahead.** On projection, not on points already scored.
  final double gap;

  /// ⚠️⚠️ **Reported and then set aside.** The shared players are usually most of both totals and the
  /// part you can do nothing about — ⭐ *printing the shared total is what makes the small gap believable
  /// rather than looking like a rounding error on two big numbers.*
  final int sharedCount;
  final double sharedXp;

  final List<EdgePlayer> myEdge;
  final List<EdgePlayer> theirEdge;
  final bool sameCaptain;

  /// ⭐ One sentence from the server, built from these same numbers — so the headline and the rows can
  /// never disagree.
  final String note;

  bool get iAmAhead => gap > 0;
}

/// One player in a built squad (ADR-268).
class BuiltPlayer {
  BuiltPlayer({
    required this.player,
    required this.bench,
    required this.forced,
  });

  factory BuiltPlayer.fromJson(Map<String, dynamic> json) => BuiltPlayer(
    player: PlayerSummary.fromJson(json),
    bench: json['bench'] as bool? ?? false,
    forced: json['forced'] as bool? ?? false,
  );

  final PlayerSummary player;

  /// ⚠️ The solver's bench, not FPL's ordered one.
  final bool bench;

  /// ⭐ **You asked for him.** A kept player is in the squad because you said so, not because he won a
  /// place — ⚠️ *and a draft that cannot tell you which is which invites you to trust a choice you made
  /// yourself.*
  final bool forced;
}
