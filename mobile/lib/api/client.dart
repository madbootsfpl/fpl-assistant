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
  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
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
      // ⚠️ FastAPI answers a malformed body with 422 and a *list* of errors, and a refused squad with 400
      // and a string. Both are the caller's fault and both belong in the same exception.
      final decoded = jsonDecode(response.body);
      final detail = decoded is Map ? decoded['detail'] : decoded;
      throw ApiException(response.statusCode, '$detail');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  /// What a manager should know about his own fifteen, strongest evidence first.
  Future<Map<String, dynamic>> signals(List<int> playerIds) =>
      _post('squad/signals', {'player_ids': playerIds, 'horizon': 1});

  /// Send a note to the owner.
  ///
  /// ⚠️ **Check `sent`.** It is the relay's own verdict — `false` with a `reason` is a real outcome, and a
  /// blind "thanks, sent!" is the bug the server side exists to avoid.
  Future<Map<String, dynamic>> feedback({
    required String message,
    String contact = '',
    String screen = '',
    String version = '',
  }) =>
      _post('feedback', {
        'message': message,
        'contact': contact,
        'screen': screen,
        'version': version,
      });

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

  /// When to play each chip, and what a wildcard is worth.
  ///
  /// ⚠️ There is no `horizon`: a chip's window is its **deadline**, decided by the server (ADR-166).
  /// ⚠️ Pass [managerId] or each chip's `available` comes back **null** — *unknown*, never *true*.
  Future<Map<String, dynamic>> chips(List<int> playerIds,
          {List<int> benchIds = const [], double bank = 0.0, int? managerId}) =>
      _post('squad/chips', {
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
  }) async =>
      MyTeam.fromJson(await _post('squad/my-team', {
        'manager_id': managerId,
        'horizon': horizon,
        'free_transfers': freeTransfers,
        'draft_player_ids': draftPlayerIds,
        'draft_bench_ids': draftBenchIds,
      }));

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
  String get _notRunning =>
      'The service is not answering on $baseUrl.\n\n'
      'Start it with:\n'
      '  venv/bin/python -m uvicorn src.service.http:app --port 8078 --reload --reload-dir src';

  Future<SquadAnalysis> analysis(List<int> playerIds,
          {List<int> benchIds = const [], int horizon = 5}) async =>
      SquadAnalysis.fromJson(await _post('squad/analysis', {
        'player_ids': playerIds,
        'bench_ids': benchIds,
        'horizon': horizon,
      }));

  /// [count] above 1 asks for a **coordinated plan** whose moves share the bank, not a menu.
  Future<TransfersAnswer> transfers(List<int> playerIds,
          {List<int> benchIds = const [],
          int horizon = 5,
          double bank = 0.0,
          int count = 1,
          int limit = 5}) async =>
      TransfersAnswer.fromJson(await _post('squad/transfers', {
        'player_ids': playerIds,
        'bench_ids': benchIds,
        'horizon': horizon,
        'bank': bank,
        'count': count,
        'limit': limit,
      }));

  /// ⚠️ Always the **next** gameweek, whatever horizon is sent.
  Future<CaptainAnswer> captain(List<int> playerIds, {int limit = 5}) async =>
      CaptainAnswer.fromJson(await _post('squad/captain', {
        'player_ids': playerIds,
        'limit': limit,
      }));

  /// The whole week: captain · lineup · transfers · timing · flags.
  ///
  /// ⚠️ **Returned raw**, deliberately. It is the richest answer and the one most likely to change shape as
  /// the first screens decide what they need — modelling it before a screen exists would be guessing.
  Future<Map<String, dynamic>> gameweekPlan(List<int> playerIds,
          {List<int> benchIds = const [],
          int horizon = 5,
          double bank = 0.0,
          int free = 1}) =>
      _post('squad/gameweek-plan', {
        'player_ids': playerIds,
        'bench_ids': benchIds,
        'horizon': horizon,
        'bank': bank,
        'free': free,
      });

  Future<RouteAnswer> route(List<int> playerIds, int targetId,
          {int horizon = 5, double bank = 0.0}) async =>
      RouteAnswer.fromJson(await _post('squad/route', {
        'player_ids': playerIds,
        'target_id': targetId,
        'horizon': horizon,
        'bank': bank,
      }));

  /// Who could replace [outId] — ⚠️ **including players you cannot afford**, flagged rather than hidden.
  Future<ReplacementsAnswer> replacements(
    List<int> playerIds,
    int outId, {
    List<int> benchIds = const [],
    int horizon = 1,
    double bank = 0.0,
    int limit = 40,
  }) async =>
      ReplacementsAnswer.fromJson(await _post('squad/replacements', {
        'player_ids': playerIds,
        'bench_ids': benchIds,
        'out_id': outId,
        'horizon': horizon,
        'bank': bank,
        'limit': limit,
      }));

  Future<BuildAnswer> build(
          {double budget = 100.0,
          int horizon = 5,
          List<int> includeIds = const [],
          List<int> excludeIds = const []}) async =>
      BuildAnswer.fromJson(await _post('squad/build', {
        'budget': budget,
        'horizon': horizon,
        'include_ids': includeIds,
        'exclude_ids': excludeIds,
      }));

  void close() => _client.close();
}
