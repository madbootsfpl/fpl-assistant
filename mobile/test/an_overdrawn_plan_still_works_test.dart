/// Planning past your bank does not break the app (ADR-338).
///
/// 🔴 **Reported straight after ADR-337 shipped**: the bank correctly went red at −£8.6m, and then every
/// player tap answered with
/// `[{type: greater_than_equal, loc: [body, bank], msg: Input should be greater than or equal to 0, …}]`.
///
/// ⚠️⚠️ Two faults in one screenshot: a guard written when a negative bank was impossible, and a raw
/// validation payload printed where a sentence belonged.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/client.dart';

void main() {
  test('a validation failure reads as a sentence, not a payload', () {
    // ⭐ The exact body FastAPI returns for the reported case.
    const body =
        '{"detail":[{"type":"greater_than_equal","loc":["body","bank"],'
        '"msg":"Input should be greater than or equal to 0","input":-8.6,'
        '"ctx":{"ge":0.0}}]}';

    final said = errorDetail(422, body);

    expect(said, contains('bank'));
    expect(said, contains('Input should be greater than or equal to 0'));
    // ⚠️ None of the machinery a reader cannot act on.
    expect(said, isNot(contains('greater_than_equal')));
    expect(said, isNot(contains('loc')));
    expect(said, isNot(contains('ctx')));
  });

  test('several complaints are all reported, one per line', () {
    const body =
        '{"detail":[{"loc":["body","bank"],"msg":"too low"},'
        '{"loc":["body","horizon"],"msg":"out of range"}]}';

    final said = errorDetail(422, body);

    expect(said, contains('bank — too low'));
    expect(said, contains('horizon — out of range'));
  });

  test('a plain string detail is still passed straight through', () {
    // ⭐ The ordinary case the old code handled, which must not regress.
    expect(
      errorDetail(400, '{"detail":"That manager id is not public yet."}'),
      'That manager id is not public yet.',
    );
  });

  test('an empty validation list falls back rather than saying nothing', () {
    final said = errorDetail(422, '{"detail":[]}');
    expect(said.trim(), isNotEmpty);
    expect(said, contains('422'));
  });
}
