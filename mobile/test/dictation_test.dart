/// Asking a question out loud (ADR-315).
///
/// ⭐ The microphone's states are tested without a microphone, because *a control whose states only exist
/// on a device is a control nothing checks.*
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/ask_view.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/dictation.dart';

/// A microphone that is whatever the test needs it to be.
class FakeMic implements Dictation {
  FakeMic({this.canListen = true});

  final bool canListen;
  bool listening = false;
  int stops = 0;
  void Function(String, bool)? _sink;

  @override
  Future<bool> available() async => canListen;

  @override
  Future<void> start({required void Function(String, bool) onWords}) async {
    listening = true;
    _sink = onWords;
  }

  @override
  Future<void> stop() async {
    listening = false;
    stops += 1;
  }

  @override
  bool get isListening => listening;

  /// Pretend somebody said something.
  void say(String words, {bool done = false}) => _sink?.call(words, done);
}

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

Future<void> pump(WidgetTester tester, FakeMic mic) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: AskView(
          client: ServiceClient(
            baseUrl: 'http://x',
            client: MockClient((_) async => http.Response('{"headline":"ok"}', 200)),
          ),
          team: sampleTeam(),
          dictation: mic,
        ),
      ),
    ),
  );
  await tester.pump();
}

void main() {
  testWidgets('a microphone is offered when the device has one', (tester) async {
    await pump(tester, FakeMic());

    expect(find.byIcon(Icons.mic_none), findsOneWidget);
  });

  testWidgets('no microphone, no button — and the keyboard still works', (tester) async {
    // ⚠️⚠️ **Hidden, not disabled.** ⭐ *A control that cannot work is worse than no control: it invites a
    // tap and answers with nothing.* The field must remain the ordinary way in.
    await pump(tester, FakeMic(canListen: false));

    await tester.tap(find.byIcon(Icons.mic_none));
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.mic_none), findsNothing);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.byIcon(Icons.arrow_upward), findsOneWidget, reason: 'send is still there');
  });

  testWidgets('listening looks unmistakably different', (tester) async {
    // ⭐⭐ *A microphone that is on and does not look on is the one thing a person will not forgive.*
    // ⚠️ Orange, not purple: purple is this app's ordinary "yours", and listening is not ordinary.
    final mic = FakeMic();
    await pump(tester, mic);

    await tester.tap(find.byIcon(Icons.mic_none));
    await tester.pumpAndSettle();

    expect(mic.listening, isTrue);
    expect(find.byIcon(Icons.stop_circle), findsOneWidget);
    final icon = tester.widget<Icon>(find.byIcon(Icons.stop_circle));
    expect(icon.color, Brand.orange);
  });

  testWidgets('the words land in the field as they are spoken', (tester) async {
    // ⭐ Partial results, deliberately: a name coming out wrong is visible **before** the question is sent,
    // rather than after the answer is about somebody else.
    final mic = FakeMic();
    await pump(tester, mic);
    await tester.tap(find.byIcon(Icons.mic_none));
    await tester.pumpAndSettle();

    mic.say('who should i');
    await tester.pump();
    expect(find.text('who should i'), findsOneWidget);

    mic.say('who should i captain', done: true);
    await tester.pump();

    expect(find.text('who should i captain'), findsOneWidget);
    expect(find.byIcon(Icons.mic_none), findsOneWidget, reason: 'listening ended, so the mic resets');
  });

  testWidgets('tapping again stops it', (tester) async {
    // ⭐ Tap to talk, tap to stop — not press-and-hold: a question takes seconds to say, and a held finger
    // covers the field it is filling.
    final mic = FakeMic();
    await pump(tester, mic);

    await tester.tap(find.byIcon(Icons.mic_none));
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.stop_circle));
    await tester.pumpAndSettle();

    expect(mic.stops, 1);
    expect(find.byIcon(Icons.mic_none), findsOneWidget);
  });

  testWidgets('leaving the screen stops the microphone', (tester) async {
    // ⚠️⚠️ **The one that matters.** A microphone left listening after the screen is gone is the failure
    // nobody reports and everybody minds.
    final mic = FakeMic();
    await pump(tester, mic);
    await tester.tap(find.byIcon(Icons.mic_none));
    await tester.pumpAndSettle();

    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: SizedBox())));
    await tester.pumpAndSettle();

    expect(mic.stops, greaterThanOrEqualTo(1), reason: 'dispose did not stop it');
  });
}
