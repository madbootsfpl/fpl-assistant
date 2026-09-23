/// Calling the MADBOOTS service (ADR-219/220).
///
/// ⭐ **Ids out, analysis back.** The client never sends player rows — that would put it in the position of
/// defining the engine's input, which is how one rule becomes two implementations (audit §4.2).
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

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
  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    late final http.Response response;
    try {
      response = await _client.post(
        Uri.parse('$baseUrl/api/v1/$path'),
        headers: const {'Content-Type': 'application/json'},
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

  Future<BuildAnswer> build({
    double budget = 100.0,
    int horizon = 5,
    List<int> includeIds = const [],
    List<int> excludeIds = const [],
  }) async => BuildAnswer.fromJson(
    await _post('squad/build', {
      'budget': budget,
      'horizon': horizon,
      'include_ids': includeIds,
      'exclude_ids': excludeIds,
    }),
  );

  void close() => _client.close();
}

/// Why nothing answered — ⭐ **one wording, used by every call and by the Settings check.**
///
/// ⭐⭐ **All of these produce an identical silence from the app's side**, and only one of them is a
/// problem with the app. A bare "connection refused" sends someone hunting through code for a phone that
/// is on 4G. ⚠️ Two of the five are *permissions a person has to grant*, and neither announces itself
/// afterwards: iOS asks once for the local network, macOS asks once for incoming connections, and a
/// "Don't Allow" on either is remembered silently.
String refusedMessage(String baseUrl) =>
    'Nothing answered at $baseUrl.\n\n'
    'On a phone, in the order worth checking:\n'
    '  • Settings ▸ Privacy & Security ▸ Local Network — is MADBOOTS allowed?\n'
    '  • Is the phone on the same Wi-Fi as the computer, not mobile data?\n'
    '  • Is the computer awake, with scripts/serve_api.sh running?\n'
    '  • Did the computer\'s address change? It is a Wi-Fi lease and it moves.\n\n'
    'Change the address under More ▸ Settings ▸ Server.';
