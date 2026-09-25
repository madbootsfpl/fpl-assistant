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
  _landscape();
  _scaling();
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

/// The pitch scales to the screen it is on (ADR-285).
///
/// ⭐⭐ **The owner's report was "portrait stretches the pitch and leaves dead green space", and the
/// measurement is what showed what that meant.** The pitch filled 91% of a 1280pt tablet and drew the
/// same 70×86 card it draws on a 390pt phone — ⚠️ *the green stretched and the players did not.*
void _scaling() {
  group('how wide a card is drawn', () {
    test('a phone is left exactly as it was', () {
      // ⚠️⚠️ **The whole safety of this change.** ADR-253 tuned the phone pitch against the owner's own
      // screenshots; ⭐ *changing it as a side effect of a tablet fix is how a report about one screen
      // becomes a surprise on another.*
      for (final width in [320.0, 390.0, 430.0, 599.0]) {
        expect(
          PitchView.cardWidthFor(width - 8, 5, shortestSide: width),
          70,
          reason: 'a $width-wide phone must draw the design card',
        );
        expect(
          PitchView.cardWidthFor(width - 8, 4, shortestSide: width),
          70,
          reason: 'a four-across row on a $width phone must not grow either',
        );
      }
    });

    test('a tablet draws the same fraction of the screen a phone does', () {
      // ⭐ The phone draws 70 on 390 — 18%. A tablet drawing 18% fills the rows vertically for the same
      // reason it fills them across: *a tablet is not a phone with more room for whitespace.*
      final tablet = PitchView.cardWidthFor(792, 4, shortestSide: 800);

      expect(tablet / 800, closeTo(70 / 390, 0.02));
      expect(tablet, greaterThan(70));
    });

    test('a tablet is the same size in portrait and landscape', () {
      // ⚠️ Driven by `shortestSide`, so turning the device does not resize the team.
      expect(
        PitchView.cardWidthFor(792, 4, shortestSide: 800),
        PitchView.cardWidthFor(1272, 4, shortestSide: 800),
      );
    });

    test('a crowded row still bounds it', () {
      // ⭐ Proportion is what it wants; the slot is what it can have. Five across on a narrow tablet
      // must not overlap whatever the proportion says.
      final five = PitchView.cardWidthFor(400, 5, shortestSide: 800);
      expect(five * 5, lessThan(400));
    });

    test('it never runs away on a very large surface', () {
      expect(PitchView.cardWidthFor(4000, 4, shortestSide: 3000), 70 * 2.4);
    });

    test('a degenerate row falls back rather than dividing by zero', () {
      expect(PitchView.cardWidthFor(800, 0, shortestSide: 800), 70);
      expect(PitchView.cardWidthFor(double.infinity, 4, shortestSide: 800), 70);
    });
  });

  group('what the screen actually draws', () {
    Future<List<Size>> cards(WidgetTester tester, double w, double h) async {
      tester.view.physicalSize = Size(w, h);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PitchView(
              team: sampleTeam(),
              mode: PitchMode.nextGw,
              onMode: (_) {},
              onTapPlayer: (_) {},
            ),
          ),
        ),
      );
      await tester.pump();
      expect(tester.takeException(), isNull);
      // ⚠️⚠️ **The painted kit, not the card's box.** Measuring the box let a mutation survive that
      // removed the up-scaling entirely: the `SizedBox` was still 143pt wide while the shirt inside it
      // stayed phone-sized. ⭐ *A layout test that measures the container rather than the thing in it
      // will pass on an empty container.*
      //
      // ⚠️⚠️ **And `getRect`, not `getSize`.** A `FittedBox` scales by a **transform**, so its child's
      // layout size never changes — `getSize` reported 22.3×31 on a tablet and a phone alike, which is
      // the same blind spot one level down. `getRect` goes through `localToGlobal` and sees what is
      // actually on the screen: ⭐ *if the change is something the eye can see, the test has to look
      // where the eye looks.*
      return [
        for (final e in find.byType(Image).evaluate())
          if (tester.getRect(find.byWidget(e.widget)).width > 20)
            tester.getRect(find.byWidget(e.widget)).size,
      ];
    }

    testWidgets('every card on a tablet is the same width', (tester) async {
      // ⚠️⚠️ **Written per row first, which gave the lone goalkeeper a card half again as wide as the
      // defenders below him.** ⭐ The code already said why: *"a five-DEF row and a one-FWD row must draw
      // the same card, or the eye reads the wider one as more important."*
      final sizes = await cards(tester, 800, 1280);

      expect(
        sizes.length,
        greaterThanOrEqualTo(15),
        reason: 'eleven and a bench of four',
      );
      expect(sizes.map((s) => s.width.round()).toSet().length, 1);
    });

    testWidgets('the bench is drawn at the same width as the eleven', (
      tester,
    ) async {
      // ⭐ They have always matched on a phone. *A fix that stops at the edge of the thing that was
      // reported is a fix that creates the next report.*
      final sizes = await cards(tester, 800, 1280);
      final phone = await cards(tester, 390, 760);
      // ⭐ Every kit on the tablet is bigger than every kit on the phone, and they all agree with
      // each other — the XI and the bench alike.
      expect(
        sizes.map((s) => s.width.round()).toSet().single,
        greaterThan(phone.map((s) => s.width.round()).toSet().single),
      );
    });

    testWidgets('a phone still draws the design card', (tester) async {
      final sizes = await cards(tester, 390, 760);
      // ⭐ One size across the whole squad, and it is the size ADR-253 tuned.
      expect(sizes.map((s) => s.width.round()).toSet().length, 1);
      expect(sizes.first.width, closeTo(22.3, 1));
    });
  });
}

/// Landscape: the bench beside the pitch, not below it (ADR-293).
///
/// ⭐⭐ **The substitutes were drawn larger than the team.** The XI rows are `Expanded` and divide
/// whatever height is left, so each card shrinks to fit its row; the bench is not height-constrained and
/// kept its full size. On the owner's tablet in landscape that was **32pt kits against a 46pt bench** —
/// and a phone in landscape was worse still, at 9pt.
void _landscape() {
  Future<({List<double> kits, int cards})> pump(
    WidgetTester tester,
    double w,
    double h,
  ) async {
    tester.view.physicalSize = Size(w, h);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PitchView(
            team: sampleTeam(),
            mode: PitchMode.nextGw,
            onMode: (_) {},
            onTapPlayer: (_) {},
          ),
        ),
      ),
    );
    await tester.pump();
    // ⚠️ `takeException`, because the first version of this layout overflowed by 3.7px — ⭐ *a layout
    // that fits on the device you tested is not a layout that fits.*
    expect(tester.takeException(), isNull);
    final kits = [
      for (final e in find.byType(Image).evaluate())
        if (tester.getRect(find.byWidget(e.widget)).width > 16)
          tester.getRect(find.byWidget(e.widget)).width,
    ];
    return (kits: kits, cards: kits.length);
  }

  group('the bench never outgrows the eleven', () {
    for (final (w, h, name) in const [
      (390.0, 760.0, 'phone portrait'),
      (760.0, 390.0, 'phone landscape'),
      (800.0, 1280.0, 'tablet portrait'),
      (1280.0, 800.0, 'tablet landscape'),
    ]) {
      testWidgets('on a $name', (tester) async {
        final r = await pump(tester, w, h);

        expect(
          r.cards,
          greaterThanOrEqualTo(15),
          reason: 'eleven and a bench of four',
        );
        // ⭐ Within a point of each other. *A bench bigger than the XI is a screen that has its
        // priorities the wrong way round*, and it is the shape of the bug this fixes.
        final biggest = r.kits.reduce((a, b) => a > b ? a : b);
        final smallest = r.kits.reduce((a, b) => a < b ? a : b);
        expect(
          biggest - smallest,
          lessThan(2),
          reason:
              'kits range $smallest..$biggest — the bench and the XI disagree',
        );
      });
    }
  });

  testWidgets('landscape is no longer a punishment', (tester) async {
    // ⚠️⚠️ **The numbers, because the change is a size.** Portrait was always fine; landscape was the
    // screen that could not be read.
    final portrait = await pump(tester, 800, 1280);
    final landscape = await pump(tester, 1280, 800);

    expect(
      landscape.kits.first,
      greaterThan(40),
      reason: 'was 32 before the bench moved',
    );
    expect(
      (landscape.kits.first - portrait.kits.first).abs(),
      lessThan(2),
      reason: 'turning the tablet should not resize the team',
    );
  });

  testWidgets('a phone in landscape is helped too', (tester) async {
    // ⭐ I gated this to tablets first, reasoning a phone would end up with a letterbox pitch. The
    // measurement said the opposite: 9pt kits became 17. *A rule that needs a device class is a rule
    // that has not found what it depends on yet.*
    final r = await pump(tester, 760, 390);

    expect(r.kits.reduce((a, b) => a < b ? a : b), greaterThan(14));
  });

  testWidgets('each substitute is labelled with the position he can fill', (
    tester,
  ) async {
    // ⭐⭐ Owner feedback, matching FFH: *"can we have labels over each substitute, like GK, DEF, MID,
    // FWD."* ⚠️⚠️ **It does not replace the order badge**, because the two say different things:
    // `1st · 2nd · 3rd · GK` is *what FPL will do* if someone does not play; `DEF` is *what he can come
    // on for*. A bench read to answer "who covers my injured defender?" needs the second.
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

    final bench = tester.getRect(find.text('BENCH'));
    for (final p in team.orderedBench) {
      // The label sits with its own card, below the BENCH heading.
      final labels = find.text(p.position);
      expect(
        labels,
        findsWidgets,
        reason: 'no ${p.position} label on the bench',
      );
      final onBench = tester.getRect(find.text(p.name)).top;
      expect(onBench, greaterThan(bench.top));
    }
    // ⭐ And the order badge is still there — this added a fact, it did not swap one.
    expect(find.text('1st'), findsOneWidget);
  });

  testWidgets('the labels do not cost the eleven their size in landscape', (
    tester,
  ) async {
    // ⚠️⚠️ **This is how the first version of the labels broke ADR-293.** Stacked above the card they
    // cost ~14pt each, and on a phone in landscape the kits shrank from 17pt to **11** — the exact bug
    // ADR-293 existed to fix. ⭐ *A label added on the scarce axis is a label paid for by the thing it is
    // labelling*, so sideways it sits beside the shirt instead.
    final team = sampleTeam();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          backgroundColor: const Color(0xFF17131F),
          body: SizedBox(
            width: 760,
            height: 390,
            child: Column(
              children: [
                Expanded(
                  child: PitchView(
                    team: team,
                    mode: PitchMode.nextGw,
                    onMode: (_) {},
                    onTapPlayer: (_) {},
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    final kits = tester
        .widgetList<Image>(find.byType(Image))
        .map((i) => i.height)
        .whereType<double>();
    expect(kits, isNotEmpty);
    final drawn = tester.getRect(find.byType(Image).first).height;
    expect(
      drawn,
      greaterThanOrEqualTo(15),
      reason: 'the labels shrank the kits to ${drawn.toStringAsFixed(1)}pt',
    );
  });
}
