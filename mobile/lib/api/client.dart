/// Calling the MADBOOTS service (ADR-219/220).
///
/// ⭐ **Ids out, analysis back.** The client never sends player rows — that would put it in the position of
/// defining the engine's input, which is how one rule becomes two implementations (audit §4.2).
library;

import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

/// Raised when the service refuses a request. ⭐ **400 is the caller's mistake, not a server fault**, and
/// the server says why — so this carries the reason rather than a status code alone.
class ApiException implements Exception {
  ApiException(this.statusCode, this.detail);

  final int statusCode;
  final String detail;

  @override
  String toString() => 'ApiException($statusCode): $detail';
}

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
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/$path'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (response.statusCode != 200) {
      // ⚠️ FastAPI answers a malformed body with 422 and a *list* of errors, and a refused squad with 400
      // and a string. Both are the caller's fault and both belong in the same exception.
      final decoded = jsonDecode(response.body);
      final detail = decoded is Map ? decoded['detail'] : decoded;
      throw ApiException(response.statusCode, '$detail');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

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
  Future<Map<String, dynamic>> chips(List<int> playerIds,
          {List<int> benchIds = const [], double bank = 0.0}) =>
      _post('squad/chips', {
        'player_ids': playerIds,
        'bench_ids': benchIds,
        'bank': bank,
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
    final response = await _client.get(Uri.parse('$baseUrl/api/v1/health'));
    return response.statusCode == 200;
  }

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
