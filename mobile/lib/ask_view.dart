/// Ask — a question in words (ADR-302, on ADR-036/054).
///
/// ⭐⭐⭐ **The routing is a year old and no phone could reach it.** `src/ask.py` matches a question to one
/// of fifteen intents, loads what that intent needs, and returns a decision, the facts behind it and a
/// rendered detail block. It was the one capability the web had and the app did not.
///
/// ⚠️⚠️ **There is no chat here, and that is on purpose.** No history, no thread, no "typing…" — one
/// question, one answer, replaced by the next. ⭐ *A conversation implies the thing remembers, and this
/// does not*: every question is routed from scratch, which is exactly what `ask.answer` is.
library;

import 'dart:async';

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class AskView extends StatefulWidget {
  const AskView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<AskView> createState() => _AskViewState();
}

class _AskViewState extends State<AskView> {
  final TextEditingController _question = TextEditingController();
  Future<Answer>? _answer;

  /// ⭐ Real questions in the engine's own vocabulary, because *a free-text box with no examples is a
  /// box people type one thing into and give up on.* Tapping one asks it.
  static const List<String> _examples = [
    'Who should I captain?',
    'What should I do this week?',
    'Who should I transfer?',
    'How do chips work?',
  ];

  @override
  void dispose() {
    _question.dispose();
    super.dispose();
  }

  void _ask([String? preset]) {
    final q = (preset ?? _question.text).trim();
    if (q.isEmpty) return;
    _question.text = q;
    FocusScope.of(context).unfocus();
    final pending = widget.client.ask(
      q,
      playerIds: [
        for (final p in [
          ...widget.team.analysis.xi,
          ...widget.team.analysis.bench,
        ])
          p.id,
      ],
      benchIds: [for (final p in widget.team.analysis.bench) p.id],
      // ⚠️ The real numbers. Asking against £0 and one transfer would answer a question about a
      // position the manager is not in — the exact defect `ask.py` records at its own call site.
      free: widget.team.freeTransfers,
      bank: widget.team.bank ?? 0,
    );
    // ⚠️⚠️⚠️ **A no-op listener, attached at creation, and it fixes a real crash.** `FutureBuilder`
    // subscribes on the *next* frame; a **fast** failure — an immediate 500, or being offline — rejects
    // before then, and Dart reports a rejection nobody was listening to as an **unhandled error**. The
    // screen still renders the message correctly, and the app still dies.
    //
    // ⭐ Found by a test that returned 500 from a mock, which completes in microseconds. *A network
    // error is normally slow enough to hide this, which is exactly why it would have shipped.*
    unawaited(pending.then((_) {}, onError: (Object _, StackTrace _) {}));
    // ⚠️ A block body, not an arrow: `=> _answer = pending` **returns** the assignment, and Flutter
    // refuses a `setState` callback that returns a Future — *the arrow is shorter and says something
    // different.*
    setState(() {
      _answer = pending;
    });
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 0),
        child: TextField(
          controller: _question,
          textInputAction: TextInputAction.send,
          onSubmitted: (_) => _ask(),
          maxLength: 500,
          style: const TextStyle(color: Colors.white, fontSize: 14),
          decoration: InputDecoration(
            hintText: 'Ask about your squad…',
            hintStyle: const TextStyle(color: Colors.white38),
            counterText: '',
            filled: true,
            fillColor: Colors.white10,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(Brand.radiusMd),
              borderSide: BorderSide.none,
            ),
            suffixIcon: IconButton(
              icon: const Icon(Icons.arrow_upward, color: Brand.purple),
              onPressed: _ask,
            ),
          ),
        ),
      ),
      // ⭐ The examples stay visible until something has been asked, then get out of the way.
      if (_answer == null)
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 0),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final example in _examples)
                GestureDetector(
                  onTap: () => _ask(example),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 7,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white10,
                      borderRadius: BorderRadius.circular(Brand.radiusPill),
                    ),
                    child: Text(
                      example,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      Expanded(
        child: _answer == null
            ? const _Empty()
            : FutureBuilder<Answer>(
                future: _answer,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snap.hasError) {
                    return _Note(
                      text: 'That did not reach the engine.\n${snap.error}',
                    );
                  }
                  return _Rendered(answer: snap.data!);
                },
              ),
      ),
    ],
  );
}

class _Rendered extends StatelessWidget {
  const _Rendered({required this.answer});

  final Answer answer;

  @override
  Widget build(BuildContext context) {
    // ⚠️⚠️ **A fallback is shown INSTEAD of a headline, never beside one.** An unrecognised question
    // routes to `chat`, whose whole answer is a list of what it *can* be asked — ⭐ *a free-text box that
    // only ever says "I don't understand" teaches people to stop typing.*
    if (answer.isFallback) {
      return _Note(
        text: answer.message.isEmpty ? answer.detail : answer.message,
      );
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 24),
      children: [
        if (answer.headline.isNotEmpty)
          Text(
            answer.headline,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              height: 1.4,
              fontWeight: FontWeight.w600,
            ),
          ),
        if (answer.detail.isNotEmpty) ...[
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 14),
            decoration: BoxDecoration(
              color: Colors.white10,
              borderRadius: BorderRadius.circular(Brand.radiusMd),
            ),
            // ⭐ The engine's own layout, kept. It indents and bullets in plain text, and *a renderer
            // that re-flows it would be a second opinion about how the answer reads* — the service
            // already strips the markdown that would have printed literally (ADR-274).
            child: SelectableText(
              answer.detail,
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 12.5,
                height: 1.5,
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty();

  @override
  Widget build(BuildContext context) => const Center(
    child: Padding(
      padding: EdgeInsets.all(28),
      child: Text(
        'Captaincy, transfers, a plan for the week, chips, the rules — '
        'in your own words.',
        textAlign: TextAlign.center,
        style: TextStyle(color: Colors.white38, height: 1.5, fontSize: 13),
      ),
    ),
  );
}

class _Note extends StatelessWidget {
  const _Note({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
    children: [
      Text(
        text,
        style: const TextStyle(
          color: Colors.white54,
          fontSize: 13,
          height: 1.6,
        ),
      ),
    ],
  );
}
