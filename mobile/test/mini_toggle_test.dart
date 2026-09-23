// The compact build-style toggle (ADR-275).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/lab_view.dart';
import 'package:madboots/pill.dart';

Widget wrap(Widget child) =>
    MaterialApp(home: Scaffold(backgroundColor: Brand.ink, body: child));

Color boxOf(WidgetTester tester, String label) {
  final container = tester.widget<Container>(
    find
        .ancestor(of: find.text(label), matching: find.byType(Container))
        .first,
  );
  return ((container.decoration! as BoxDecoration).color)!;
}

void main() {
  group('MiniToggle', () {
    testWidgets('it names what the choice is about', (tester) async {
      await tester.pumpWidget(
        wrap(
          MiniToggle(
            label: 'Bench',
            options: const ['Strong 11', 'Strong 15'],
            selected: 'Strong 11',
            onPick: (_) {},
          ),
        ),
      );
      // ⚠️ A toggle with no subject is two words a reader has to infer a question from.
      expect(find.text('Bench'), findsOneWidget);
    });

    testWidgets('the selected half is filled and the other is not', (tester) async {
      await tester.pumpWidget(
        wrap(
          MiniToggle(
            label: 'Bench',
            options: const ['Strong 11', 'Strong 15'],
            selected: 'Strong 11',
            onPick: (_) {},
          ),
        ),
      );
      expect(boxOf(tester, 'Strong 11'), Brand.purple);
      expect(boxOf(tester, 'Strong 15'), Colors.transparent);
    });

    testWidgets('tapping the other half reports it', (tester) async {
      String? picked;
      await tester.pumpWidget(
        wrap(
          MiniToggle(
            label: 'Bench',
            options: const ['Strong 11', 'Strong 15'],
            selected: 'Strong 11',
            onPick: (v) => picked = v,
          ),
        ),
      );
      await tester.tap(find.text('Strong 15'));
      expect(picked, 'Strong 15');
    });

    testWidgets('tapping the selected half still reports, so a caller decides', (tester) async {
      var calls = 0;
      await tester.pumpWidget(
        wrap(
          MiniToggle(
            label: 'Bench',
            options: const ['Strong 11', 'Strong 15'],
            selected: 'Strong 11',
            onPick: (_) => calls++,
          ),
        ),
      );
      await tester.tap(find.text('Strong 11'));
      expect(calls, 1);
    });
  });

  group('the build styles', () {
    // ⭐ Two ways of writing a number in one control reads as two kinds of thing.
    test('both labels use the same numbering', () {
      final labels = [for (final s in BuildStyle.values) s.label];
      final roman = labels.where((l) => RegExp(r'\b[IVX]+\b').hasMatch(l));
      final arabic = labels.where((l) => RegExp(r'\d').hasMatch(l));
      expect(
        roman.isEmpty || arabic.isEmpty,
        isTrue,
        reason: 'mixed numbering in one control: $labels',
      );
    });

    test('they are still distinguishable and name the sizes', () {
      expect(BuildStyle.strongXi.label, contains('11'));
      expect(BuildStyle.strongFifteen.label, contains('15'));
    });
  });
}
