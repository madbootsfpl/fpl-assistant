/// Calling the MADBOOTS service (ADR-219/220).
///
/// ⭐ **Ids out, analysis back.** The client never sends player rows — that would put it in the position of
/// defining the engine's input, which is how one rule becomes two implementations (audit §4.2).
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../telemetry.dart';
import 'models.dart';

/// Raised when a request does not come back with an answer. ⭐ **400 is the caller's mistake, not a server
/// fault**, and the server says why — so this carries the reason rather than a status code alone.
///
/// ⚠️ `statusCode == 0` means the request never reached anyone: the service is not running, or the device
/// cannot see it.
class ApiException implements Exception {
  ApiException(this.statusCode, this.detail);

  final int statusCode;
  final String detail;

  bool get unreachable => statusCode == 0;

  @override
  String toString() => detail;
}

/// What to show a human when a call fails.
///
/// ⭐⭐ **Here, in the client, because the client is the only thing that knows the base URL and what a
/// refused socket means.** ⚠️ A good version of this message already existed — in `main.dart`, on the
/// landing screen, and **nowhere else**: six other screens surfaced
/// `ClientException with SocketException: Connection refused … errno = 61` verbatim.
///
/// ⭐ *A fix scoped to where it was noticed is a fix the next screen does not get.*
/// What an error response actually *says*, for any body a server might send.
///
/// ⚠️ FastAPI answers a malformed body with 422 and a *list* of errors, and a refused squad with 400 and a
/// string. Both are the caller's fault and both belong in the same exception.
///
/// ⚠️⚠️ **But not every error body is JSON, and assuming so cost a real screen.** An unhandled exception
/// reaches the client as Starlette's default 500 — the eight plain-text bytes `Internal Server Error`.
/// Decoding that threw a `FormatException` which escaped the client entirely, so Feedback reported
/// *"Not sent — FormatException: Unexpected character (at character 1)"*: ⭐ *the parser's complaint about
/// the error, in place of the error*. A proxy or a cold host does the same thing with HTML.
///
/// ⭐ So the decode is attempted and its failure is **expected**, not exceptional — a body that is not JSON
/// is described rather than parsed, and a 5xx is named as ours rather than handed to the reader as debris.
String errorDetail(int status, String body) {
  try {
    final decoded = jsonDecode(body);
    final detail = decoded is Map ? decoded['detail'] : decoded;
    if (detail != null && '$detail'.trim().isNotEmpty) return '$detail';
  } catch (_) {
    // not JSON — fall through and say something true about it instead.
  }
  if (status >= 500) {
    // ⚠️ Deliberately not the body: "Internal Server Error" tells a tester nothing they can act on, and
    // reads as if they broke it.
    return 'The service hit a problem at its end (HTTP $status). That is ours to fix, not yours — '
        'please try again shortly.';
  }
  final trimmed = body.trim();
  if (trimmed.isEmpty) return 'The service refused that (HTTP $status).';
  return 'The service refused that (HTTP $status): '
      '${trimmed.length > 200 ? '${trimmed.substring(0, 200)}…' : trimmed}';
}

String friendlyError(Object? error) =>
    error is ApiException ? error.detail : '$error';

/// The app's version, and ⚠️ **the only place it is written down in Dart.**
///
/// ⭐ `test/version_matches_pubspec_test.dart` fails if it drifts from `pubspec.yaml` — *a version
/// number kept in two places is a version number that will disagree with itself*, and this one is what
/// tells the owner an old build is still in somebody's pocket (ADR-280).
const String kAppVersion = '1.0.0';

/// The build number — ⚠️ **the only thing that distinguishes two builds of `1.0.0`**, which during a beta
/// is most of them. ⭐ *Android ignores `versionName` for exactly this reason*, and the update check
/// compares on this for the same one.
const int kAppBuild = 13;

class ServiceClient {
  ServiceClient({required this.baseUrl, http.Client? client})
    : _client = client ?? http.Client();

  /// ⚠️ `http://localhost:8078` reaches the dev server from **Chrome and the iOS simulator**, which share
  /// the host's network. A **physical device** cannot, and that is the point at which the API needs hosting
  /// — not before (audit §7.1).
  final String baseUrl;
  final http.Client _client;

  /// ⚠️ `path` is everything after `/api/v1/`, **including** the `squad/` prefix where there is
  /// one. It used to assume that prefix, which made the market endpoint — the one thing that is
  /// not squad-shaped — reachable only by a `../` that depended on URL normalisation.
  /// ⭐⭐ **Three values, and the whole of what the app says about itself** (ADR-280): which platform,
  /// which build, and a random install id. ⚠️ *Not* the manager id — the server receives that on four
  /// endpoints and must never join it to these.
  ///
  /// ⚠️ **Synchronous, and reading no storage.** `Telemetry.init()` resolves the identity once before
  /// the first frame; this is a field read. ⭐ *Telemetry in the request path is telemetry that gets
  /// blamed for the app being slow* — and when it was an `await` here, eighteen unrelated tests started
  /// failing on a missing plugin binding.
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'X-Madboots-Version': kAppVersion,
    ...Telemetry.headers,
  };

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    late final http.Response response;
    try {
      response = await _client.post(
        Uri.parse('$baseUrl/api/v1/$path'),
        headers: _headers,
        body: jsonEncode(body),
      );
    } on SocketException {
      throw ApiException(0, _notRunning);
    } on http.ClientException {
      // ⚠️ On web there is no `SocketException` — a refused connection arrives as a `ClientException`.
      // Catching only the first would have left Chrome showing the raw text this message replaces.
      throw ApiException(0, _notRunning);
    } on TimeoutException {
      throw ApiException(0, 'The service did not answer in time.\n\n$baseUrl');
    }
    if (response.statusCode != 200) {
      throw ApiException(
        response.statusCode,
        errorDetail(response.statusCode, response.body),
      );
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  /// What a manager should know about his own fifteen, strongest evidence first.
  /// ⭐ `scope` is `squad` or `global` (ADR-245). ⚠️ The squad ids are sent **either way**: in global
  /// they do not narrow the sweep, they only let each signal come back flagged `owned`, so a market list
  /// can say *"you have him"* without the client matching ids itself.
  Future<Map<String, dynamic>> signals(
    List<int> playerIds, {
    String scope = 'squad',
  }) => _post('squad/signals', {
    'player_ids': playerIds,
    'horizon': 1,
    'scope': scope,
  });

  /// One player in full — the card behind a row.
  ///
  /// ⭐ Called when a row is **expanded**, not with the list: the market is 481 players and carrying every
  /// stat for all of them so that one can be opened is the opposite of the trade the list was built on.
  Future<PlayerCard> player(int playerId, {int horizon = 5}) async =>
      PlayerCard.fromJson(
        await _post('player', {'player_id': playerId, 'horizon': horizon}),
      );

  /// **Boot Battle** — two same-position players side by side.
  Future<BootBattle> compare(int aId, int bId, {int horizon = 5}) async =>
      BootBattle.fromJson(
        await _post('compare', {'a_id': aId, 'b_id': bId, 'horizon': horizon}),
      );

  /// Send a note to the owner.
  ///
  /// ⚠️ **Check `sent`.** It is the relay's own verdict — `false` with a `reason` is a real outcome, and a
  /// blind "thanks, sent!" is the bug the server side exists to avoid.
  Future<Map<String, dynamic>> feedback({
    required String message,
    String contact = '',
    String screen = '',
    String version = '',
  }) => _post('feedback', {
    'message': message,
    'contact': contact,
    'screen': screen,
    'version': version,
  });

  /// The classic leagues this manager is in (ADR-267).
  ///
  /// ⭐ Looked up from the **manager id**, because *nobody knows their league id.*
  Future<List<LeagueSummary>> leagues(int managerId) async {
    final body = await _post('leagues', {'manager_id': managerId});
    return [
      for (final l in (body['leagues'] as List? ?? []))
        LeagueSummary.fromJson(l as Map<String, dynamic>),
    ];
  }

  /// One league's table, and optionally its captain split.
  ///
  /// ⚠️⚠️ `withCaptains` costs **one FPL request per manager** — the table costs one in total. Ask for it
  /// only when the reader is looking at that panel.
  Future<LeagueTable> league(
    int leagueId, {
    bool withCaptains = false,
    int limit = 20,
  }) async => LeagueTable.fromJson(
    await _post('league', {
      'league_id': leagueId,
      'with_captains': withCaptains,
      'limit': limit,
    }),
  );

  /// You against one rival, decomposed (ADR-161).
  Future<HeadToHead> headToHead(int managerId, int rivalId) async =>
      HeadToHead.fromJson(
        await _post('h2h', {'manager_id': managerId, 'rival_id': rivalId}),
      );

  /// What the crowd is doing (ADR-266).
  ///
  /// ⚠️ `playerIds` does **not** narrow the boards — it only lets a row come back flagged `owned`, the
  /// same arrangement the market signals use (ADR-245).
  Future<TrendingBoard> trending({
    String by = 'in',
    int limit = 15,
    List<int> playerIds = const [],
  }) async => TrendingBoard.fromJson(
    await _post('trending', {
      'by': by,
      'limit': limit,
      'player_ids': playerIds,
    }),
  );

  /// The fixture-difficulty grid — every club, next few gameweeks, easiest run first (ADR-265).
  ///
  /// ⭐ **No squad.** It is a question about the league, not about you, and requiring a squad would have
  /// narrowed it to the clubs you already own.
  Future<FixtureTicker> ticker({int nextN = 6}) async =>
      FixtureTicker.fromJson(await _post('ticker', {'next_n': nextN}));

  /// Every available player, ranked by xP.
  ///
  /// ⭐ Fetched **once** and filtered on the device: the whole market is ~110 KB, and searching 481 rows
  /// locally is instant where a round trip per keystroke is not.
  ///
  /// ⚠️ Not under `/squad/` — this is the market, not your team.
  Future<List<PlayerSummary>> players({int horizon = 5}) async {
    final body = await _post('players', {'horizon': horizon, 'limit': 1000});
    return ((body['players'] as List?) ?? [])
        .map((p) => PlayerSummary.fromJson(p as Map<String, dynamic>))
        .toList();
  }

  /// One player's fingerprint, ranked **within his position** (ADR-250).
  Future<PlayerDna> playerDna(int playerId) async => PlayerDna.fromJson(
    await _post('player-dna', {'player_id': playerId, 'horizon': 5}),
  );

  /// Every club's eight-axis fingerprint, ranked across the league (ADR-247).
  ///
  /// ⚠️ Not under `/squad/` — this is the league, not your team. [playerIds] filters nothing; it only
  /// marks which clubs you hold players from.
  Future<List<ClubDna>> teamDna({List<int> playerIds = const []}) async {
    final body = await _post('team-dna', {
      'player_ids': playerIds,
      'horizon': 1,
    });
    return [
      for (final row in (body['teams'] as List? ?? []))
        ClubDna.fromJson(row as Map<String, dynamic>),
    ];
  }

  /// When to play each chip, and what a wildcard is worth.
  ///
  /// ⚠️ There is no `horizon`: a chip's window is its **deadline**, decided by the server (ADR-166).
  /// ⚠️ Pass [managerId] or each chip's `available` comes back **null** — *unknown*, never *true*.
  Future<Map<String, dynamic>> chips(
    List<int> playerIds, {
    List<int> benchIds = const [],
    double bank = 0.0,
    int? managerId,
  }) => _post('squad/chips', {
    'player_ids': playerIds,
    'bench_ids': benchIds,
    'bank': bank,
    'manager_id': ?managerId,
  });

  /// Everything the **My Team** pitch draws, in one call.
  ///
  /// ⚠️ A refusal is often not the caller's fault: a team is not public until the first deadline, and FPL
  /// is sometimes simply unreachable. [ApiException.detail] says which — show it rather than a generic
  /// "something went wrong".
  /// [draftPlayerIds] prices a squad that is **not** the one FPL holds — the manager's name, bank,
  /// deadline and armbands still come from FPL.
  Future<MyTeam> myTeam(
    int managerId, {
    int horizon = 1,
    int freeTransfers = 1,
    List<int> draftPlayerIds = const [],
    List<int> draftBenchIds = const [],
  }) async => MyTeam.fromJson(
    await _post('squad/my-team', {
      'manager_id': managerId,
      'horizon': horizon,
      'free_transfers': freeTransfers,
      'draft_player_ids': draftPlayerIds,
      'draft_bench_ids': draftBenchIds,
    }),
  );

  Future<bool> healthy() async {
    try {
      final response = await _client.get(Uri.parse('$baseUrl/api/v1/health'));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// ⭐ One string, one place. It names the address **and** the command, because "cannot connect" without
  /// either is a message that tells you only that you are stuck.
  /// ⚠️⚠️ **This message used to tell you to start uvicorn, and on a phone that is wrong twice over**:
  /// you cannot run it on the device you are holding, and the server it tells you to start is usually
  /// already running. ⭐⭐ *Advice written for the machine the developer is sitting at stops being advice
  /// the moment the client is a handset* — the same species as binding to `127.0.0.1` (ADR-239).
  ///
  /// ⭐ So it names the causes instead, and names them in the order they actually occur on a phone. The
  /// wording is [refusedMessage], shared with **More ▸ Settings ▸ Server** so the two cannot drift.
  String get _notRunning => refusedMessage(baseUrl);

  Future<SquadAnalysis> analysis(
    List<int> playerIds, {
    List<int> benchIds = const [],
    int horizon = 5,
  }) async => SquadAnalysis.fromJson(
    await _post('squad/analysis', {
      'player_ids': playerIds,
      'bench_ids': benchIds,
      'horizon': horizon,
    }),
  );

  /// [count] above 1 asks for a **coordinated plan** whose moves share the bank, not a menu.
  Future<TransfersAnswer> transfers(
    List<int> playerIds, {
    List<int> benchIds = const [],
    int horizon = 5,
    double bank = 0.0,
    int count = 1,
    int limit = 5,
  }) async => TransfersAnswer.fromJson(
    await _post('squad/transfers', {
      'player_ids': playerIds,
      'bench_ids': benchIds,
      'horizon': horizon,
      'bank': bank,
      'count': count,
      'limit': limit,
    }),
  );

  /// ⚠️ Always the **next** gameweek, whatever horizon is sent.
  Future<CaptainAnswer> captain(List<int> playerIds, {int limit = 5}) async =>
      CaptainAnswer.fromJson(
        await _post('squad/captain', {'player_ids': playerIds, 'limit': limit}),
      );

  /// The whole week: captain · lineup · transfers · timing · flags.
  ///
  /// ⚠️ **Returned raw**, deliberately. It is the richest answer and the one most likely to change shape as
  /// the first screens decide what they need — modelling it before a screen exists would be guessing.
  Future<Map<String, dynamic>> gameweekPlan(
    List<int> playerIds, {
    List<int> benchIds = const [],
    int horizon = 5,
    double bank = 0.0,
    int free = 1,
  }) => _post('squad/gameweek-plan', {
    'player_ids': playerIds,
    'bench_ids': benchIds,
    'horizon': horizon,
    'bank': bank,
    'free': free,
  });

  Future<RouteAnswer> route(
    List<int> playerIds,
    int targetId, {
    int horizon = 5,
    double bank = 0.0,
  }) async => RouteAnswer.fromJson(
    await _post('squad/route', {
      'player_ids': playerIds,
      'target_id': targetId,
      'horizon': horizon,
      'bank': bank,
    }),
  );

  /// Who could replace [outId] — ⚠️ **including players you cannot afford**, flagged rather than hidden.
  Future<ReplacementsAnswer> replacements(
    List<int> playerIds,
    int outId, {
    List<int> benchIds = const [],
    int horizon = 1,
    double bank = 0.0,
    int limit = 40,
  }) async => ReplacementsAnswer.fromJson(
    await _post('squad/replacements', {
      'player_ids': playerIds,
      'bench_ids': benchIds,
      'out_id': outId,
      'horizon': horizon,
      'bank': bank,
      'limit': limit,
    }),
  );

  /// The best legal fifteen within a budget.
  ///
  /// ⚠️⚠️ Pass  or the solver treats **all fifteen as if they play** (ADR-045) — a squad
  /// nobody fields. `0.1` is a strong XI with a cheap-but-playing bench.
  Future<BuildAnswer> build({
    double budget = 100.0,
    int horizon = 5,
    List<int> includeIds = const [],
    List<int> excludeIds = const [],
    double? benchWeight,
  }) async => BuildAnswer.fromJson(
    await _post('squad/build', {
      'budget': budget,
      'horizon': horizon,
      'include_ids': includeIds,
      'exclude_ids': excludeIds,
      'bench_weight': ?benchWeight,
    }),
  );

  void close() => _client.close();
}

/// Whether this address is a machine on the same network as the phone.
///
/// ⚠️⚠️ **The two deployments fail for completely different reasons**, and until ADR-288 they shared one
/// explanation — the developer one. A tester on the hosted service, whose only problem was a server
/// waking up, was told to check their Wi-Fi, grant a Local Network permission and see whether a shell
/// script was running on a computer they do not own.
///
/// ⭐ *An error message that describes somebody else's setup is worse than no message: it sends the
/// reader to fix something that was never broken.*
bool isLocalAddress(String baseUrl) {
  final uri = Uri.tryParse(baseUrl);
  final host = uri?.host ?? '';
  // ⭐ **The shape `scripts/serve_api.sh` produces**: plain HTTP on an explicit port. The hosted service
  // is HTTPS on 443 — ⚠️ *and iOS blocks cleartext off the LAN anyway*, so an `http://…:8078` is a
  // machine on this network whatever it calls itself. This is the case a bare hostname like
  // `http://mac:8078` falls into, which no private-range check would ever catch.
  if (uri != null && uri.scheme == 'http' && uri.hasPort) return true;
  return host == 'localhost' ||
      host == '127.0.0.1' ||
      host.endsWith('.local') ||
      host.startsWith('192.168.') ||
      host.startsWith('10.') ||
      // ⚠️ 172.16–172.31 is private; 172.32+ is not. A `startsWith('172.')` would claim half the
      // public internet is on the reader's kitchen table.
      RegExp(r'^172\.(1[6-9]|2\d|3[01])\.').hasMatch(host);
}

/// Why nothing answered — ⭐ **one wording, used by every call and by the Settings check.**
///
/// ⭐⭐ **All of these produce an identical silence from the app's side**, and only one of them is a
/// problem with the app. A bare "connection refused" sends someone hunting through code for a phone that
/// is on 4G. ⚠️ Two of the developer ones are *permissions a person has to grant*, and neither announces
/// itself afterwards: iOS asks once for the local network, macOS asks once for incoming connections, and
/// a "Don't Allow" on either is remembered silently.
String refusedMessage(String baseUrl) => isLocalAddress(baseUrl)
    ? 'Nothing answered at $baseUrl.\n\n'
          'On a phone, in the order worth checking:\n'
          '  • Settings ▸ Privacy & Security ▸ Local Network — is MADBOOTS allowed?\n'
          '  • Is the phone on the same Wi-Fi as the computer, not mobile data?\n'
          '  • Is the computer awake, with scripts/serve_api.sh running?\n'
          '  • Did the computer\'s address change? It is a Wi-Fi lease and it moves.\n\n'
          'Change the address under More ▸ Settings ▸ Server.'
    // ⭐ What is actually true for a tester: the service sleeps when nobody has used it, and waking it
    // takes longer than a request is willing to wait. ⚠️ *Naming the cause is what stops a slow morning
    // being reported as a broken app.*
    : 'The MADBOOTS service did not answer.\n\n'
          'It sleeps when nobody has used it for a while, and takes a few '
          'seconds to wake up. Tap Try again — the second attempt is usually '
          'the one that works.\n\n'
          'If it keeps happening, tell us under More ▸ Tell us something.';
