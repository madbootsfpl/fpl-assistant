/// The pitch fills the screen (ADR-253).
///
/// ⭐⭐⭐ **These measure heights, because the whole change is a height.** The pitch was 747px of a 1932px
/// screen — chrome above it, the bench floating on the dark below it, and 140px of dead space under that.
/// A competitor gave its pitch twice the room, and the owner was right that it reads better for it.
///
/// ⚠️ A test asserting "the widgets render" would pass on every version of this screen, including the one
/// being replaced. *If the change is a measurement, so is the test.*
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/pitch.dart';
import 'package:madboots/pitch_markings.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

/// A phone-shaped surface: the pitch gets whatever is left, as it does in the app.
Widget screen(Widget child) => MaterialApp(
  home: Scaffold(
    backgroundColor: const Color(0xFF17131F),
    body: SizedBox(
      width: 390,
      height: 760,
      child: Column(children: [Expanded(child: child)]),
    ),
  ),
);

void main() {
  testWidgets('the green fills the space it is given', (tester) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
        ),
      ),
    );
    expect(tester.takeException(), isNull);

    final pitch = tester.getSize(find.byType(PitchMarkings));
    // ⚠️ **A proportion, not a pixel count.** Pinning 640 would fail on the next phone; the claim is that
    // the pitch is the screen, and a screen where the main subject gets less than half is not.
    expect(
      pitch.height,
      greaterThan(760 * 0.6),
      reason:
          'the pitch got ${pitch.height} of 760 — the chrome has crept back',
    );
  });

  testWidgets('the bench sits inside the green, not beneath it', (
    tester,
  ) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
        ),
      ),
    );

    final green = tester.getRect(find.byType(PitchMarkings));
    final bench = tester.getRect(find.text('BENCH'));
    // ⭐ Integrated and still plainly separate — the thing the owner asked for. A bench *below* the green
    // reads as a different screen that happens to be nearby.
    expect(bench.top, greaterThan(green.top));
    expect(bench.bottom, lessThan(green.bottom));
  });

  testWidgets('the footer rides on the pitch too', (tester) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          footer: const Text('FOOTER'),
        ),
      ),
    );
    final green = tester.getRect(find.byType(PitchMarkings));
    final footer = tester.getRect(find.text('FOOTER'));
    expect(footer.bottom, lessThanOrEqualTo(green.bottom));
  });

  testWidgets('the header is one line, not three', (tester) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
        ),
      ),
    );
    // ⚠️ The web's prose line is 96 characters and wrapped to three here. The phone composes its own from
    // the parts — ⭐ *a client too narrow for a prose line needs the facts, not a second prose line.*
    expect(find.textContaining(team.deadlineLabel), findsNothing);
    expect(find.textContaining(team.deadlineWhen), findsOneWidget);
    expect(find.textContaining(team.deadlineCountdown), findsOneWidget);
  });

  testWidgets('the wordmark is on the pitch', (tester) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
        ),
      ),
    );
    final green = tester.getRect(find.byType(PitchMarkings));
    final mark = tester.getRect(find.textContaining('MAD').first);
    // ⭐ Inside the green: present, and costing no row of its own.
    expect(mark.top, greaterThan(green.top));
  });

  test('the server sends the deadline in parts, not only as prose', () {
    // ⚠️ The one-line header is only possible because the API sends `when` and `countdown`. If it stops,
    // the header silently falls back to the 96-character line and wraps again.
    final json = jsonDecode(
      File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
          .readAsStringSync(),
    ) as Map<String, dynamic>;
    final deadline = json['deadline'] as Map<String, dynamic>;
    expect(deadline['when'], isNotEmpty);
    expect(deadline['countdown'], isNotEmpty);
    expect(
      '${deadline['when']} · ${deadline['countdown']}'.length,
      lessThan('${deadline['label']}'.length),
      reason: 'the parts should be shorter than the prose they replace',
    );
  });
}
