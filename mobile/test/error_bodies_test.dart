// What the app says when the server answers with something other than an answer.
//
// ⚠️ Every test here is a body a real server actually sent. The 500 case is the one that shipped broken:
// Feedback reported "Not sent — FormatException: Unexpected character (at character 1)", which is the
// JSON parser's complaint *about* the error standing in for the error.
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/client.dart';

void main() {
  group('errorDetail', () {
    test('a FastAPI 400 shows the refusal it carries', () {
      expect(
        errorDetail(400, '{"detail": "that squad has 12 players"}'),
        contains('that squad has 12 players'),
      );
    });

    test('a FastAPI 422 shows its list of complaints rather than swallowing them', () {
      final said = errorDetail(422, '{"detail": [{"loc": ["body", "fpl_id"], "msg": "field required"}]}');
      expect(said, contains('field required'));
    });

    // ⭐ The bug. Starlette's default 500 body is plain text, not JSON.
    test('a plain-text 500 never leaks a parser error', () {
      final said = errorDetail(500, 'Internal Server Error');
      expect(said, isNot(contains('FormatException')));
      expect(said, isNot(contains('character')));
      expect(said, contains('500'));
    });

    test('a 500 is named as ours, and does not repeat the unhelpful body', () {
      final said = errorDetail(500, 'Internal Server Error');
      expect(said.toLowerCase(), contains('ours to fix'));
      // ⚠️ "Internal Server Error" reads to a tester as though they broke something.
      expect(said, isNot(contains('Internal Server Error')));
    });

    test('a proxy answering HTML does not reach the reader as tags', () {
      final said = errorDetail(502, '<html><head><title>502 Bad Gateway</title></head></html>');
      expect(said, isNot(contains('FormatException')));
      expect(said, contains('502'));
    });

    test('an empty body still says something true', () {
      expect(errorDetail(404, ''), contains('404'));
      expect(errorDetail(404, '   ').trim(), isNotEmpty);
    });

    test('a long non-JSON body is trimmed rather than dumped', () {
      final said = errorDetail(400, 'x' * 5000);
      expect(said.length, lessThan(300));
      expect(said, contains('…'));
    });

    test('a 4xx body that is JSON but has no detail still names the status', () {
      expect(errorDetail(403, '{"error": "nope"}'), contains('403'));
    });

    // ⚠️ friendlyError is what the Feedback screen prints, so the wiring matters as much as the helper.
    test('friendlyError passes an ApiException detail through unchanged', () {
      final detail = errorDetail(500, 'Internal Server Error');
      expect(friendlyError(ApiException(500, detail)), detail);
    });
  });
}
