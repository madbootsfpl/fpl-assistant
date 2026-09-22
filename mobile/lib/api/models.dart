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

/// ⚠️⚠️ **The API returns FOUR different player shapes, and this is the smallest.**
///
/// | where | keys |
/// |---|---|
/// | `analysis` (xi · bench · issues · weakest · top_pick) | 11, curated → [PlayerSummary] |
/// | `transfers.moves[].in` / `.out` | **5–6** → this class |
/// | `route.target` | 6 → this class |
/// | `route.blocked[].out`, `build.selected[]` | **42–45 raw database columns** |
///
/// ⭐ **Found by writing these models against the real payloads**, not by reading the server: `in` carries
/// no `position`, so a transfer card cannot show a position chip without a second lookup, and `out` carries
/// `leaving` while `in` does not — correct, since only a player you hold can be reported as going.
///
/// 🔴 **Normalising the API on one player shape is the recommendation, and it is a server change**, noted
/// in `docs/03_Architecture/Flutter_Start_Checklist.md`. Until then these classes describe what is actually
/// on the wire — ⭐ *a model that flatters the contract is how a client discovers the truth at runtime.*
class PlayerRef {
  PlayerRef({
    required this.id,
    required this.name,
    required this.team,
    required this.price,
    required this.xp,
    required this.position,
    required this.leaving,
  });

  factory PlayerRef.fromJson(Map<String, dynamic> json) => PlayerRef(
        id: json['id'] as int,
        name: json['web_name'] as String,
        team: json['team'] as String,
        price: _double(json['price']),
        xp: _double(json['xp']),
        // ⚠️ Absent on a transfer's `in`/`out`; present on `route.target`. Nullable, so the gap is visible
        // to the screen rather than defaulted into a wrong-looking chip.
        position: json['position'] as String?,
        leaving: json['leaving'] as Map<String, dynamic>?,
      );

  final int id;
  final String name;
  final String team;
  final double price;
  final double xp;
  final String? position;
  final Map<String, dynamic>? leaving;

  bool get isLeaving => leaving != null;
}

/// A player as the analysis surfaces describe them — the curated summary, not the database row.
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
      clubCounts: ((json['club_counts'] as Map?) ?? {}).map((k, v) => MapEntry('$k', v as int)),
      concentratedClubs: ((json['concentrated_clubs'] as List?) ?? []).cast<String>(),
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
  });

  factory TransferMove.fromJson(Map<String, dynamic> json) => TransferMove(
        position: json['position'] as String,
        out: PlayerRef.fromJson(json['out'] as Map<String, dynamic>),
        // ⚠️ `in` is a Dart keyword, so the field cannot share the wire's name.
        incoming: PlayerRef.fromJson(json['in'] as Map<String, dynamic>),
        gain: _double(json['gain']),
        outOnBench: json['out_on_bench'] as bool? ?? false,
      );

  final String position;
  final PlayerRef out;
  final PlayerRef incoming;

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

  factory TransfersAnswer.fromJson(Map<String, dynamic> json) => TransfersAnswer(
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
class CaptainPick {
  CaptainPick({
    required this.id,
    required this.name,
    required this.team,
    required this.xp,
    required this.opponent,
    required this.venue,
    required this.penaltyTaker,
    required this.doubtful,
    required this.chance,
    required this.minutesWeight,
  });

  factory CaptainPick.fromJson(Map<String, dynamic> json) => CaptainPick(
        id: json['id'] as int,
        name: json['web_name'] as String,
        team: json['team'] as String,
        xp: _double(json['xp']),
        opponent: json['opponent'] as String?,
        venue: json['venue'] as String?,
        penaltyTaker: json['penalty_taker'] as bool? ?? false,
        doubtful: json['doubtful'] as bool? ?? false,
        chance: json['chance'] as int?,
        minutesWeight: (json['minutes_weight'] as num?)?.toDouble() ?? 1.0,
      );

  final int id;
  final String name;
  final String team;

  /// ⚠️ **Next gameweek only**, whatever horizon was requested — captaincy is a one-week bet.
  final double xp;
  final String? opponent;

  /// `H` or `A`. Null when the fixture is unknown.
  final String? venue;
  final bool penaltyTaker;

  /// ⭐ Included and flagged, never zeroed — a doubtful player may still be the right captain.
  final bool doubtful;
  final int? chance;
  final double minutesWeight;
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
        target: PlayerRef.fromJson(json['target'] as Map<String, dynamic>),
        owned: json['owned'] as bool? ?? false,
        routes: ((json['routes'] as List?) ?? []).cast<Map<String, dynamic>>(),
        blocked: ((json['blocked'] as List?) ?? []).cast<Map<String, dynamic>>(),
        shortfall: (json['shortfall'] as num?)?.toDouble(),
      );

  final int horizon;
  final PlayerRef target;

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
  });

  factory BuildAnswer.fromJson(Map<String, dynamic> json) => BuildAnswer(
        horizon: json['horizon'] as int,
        budget: _double(json['budget']),
        status: json['status'] as String,
        selected: ((json['selected'] as List?) ?? [])
            .map((p) => PlayerSummary.fromJson(p as Map<String, dynamic>))
            .toList(),
        totalCost: _double(json['total_cost']),
        projectedXp: _double(json['projected_xp']),
      );

  final int horizon;
  final double budget;

  /// ⚠️ **The solver's own word — check it.** `Optimal` means a squad was found; anything else (`Infeasible`)
  /// means *nothing fits these constraints*, which is an answer, not a failure. ⭐ A client that ignored it
  /// would render an empty pitch with no reason given.
  final String status;
  final List<PlayerSummary> selected;
  final double totalCost;
  final double projectedXp;

  bool get isOptimal => status == 'Optimal';
}
