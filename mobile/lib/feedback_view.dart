/// Feedback — its own destination, because it is the one thing a closed beta most needs (ADR-238).
///
/// ⭐⭐ **A tester on a phone is more likely to notice something and less likely to be near a laptop.** The
/// competitor's app sends you back to the desktop to say anything; that loses the report, not just the
/// convenience.
///
/// ⭐ It is a **directory row of its own** rather than a section inside Settings. Settings is where you go
/// having decided to change something; feedback is where you go having just seen something. ⚠️ *One door,
/// though* — it is deliberately not also duplicated into Settings, because two doors to one room drift
/// apart (ADR-184).
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'brand.dart';

class FeedbackView extends StatefulWidget {
  const FeedbackView({required this.client, super.key});

  final ServiceClient client;

  @override
  State<FeedbackView> createState() => _FeedbackViewState();
}

class _FeedbackViewState extends State<FeedbackView> {
  final TextEditingController _message = TextEditingController();
  bool _sending = false;
  String? _outcome;
  bool _ok = false;

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
  }

  /// ⚠️ **It never says "sent" unless the relay said so** (ADR-231) — *a success message that cannot fail
  /// is not a success message.* When it fails it hands over the email address rather than the error.
  Future<void> _send() async {
    final text = _message.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _outcome = null;
    });
    try {
      final result = await widget.client.feedback(
        message: text,
        screen: 'mobile',
        version: '0.0.1',
      );
      final sent = result['sent'] == true;
      setState(() {
        _ok = sent;
        _outcome = sent
            ? 'Thanks — that reached us.'
            : 'Not sent — ${result['reason'] ?? 'the service refused it'}. '
                  'Email ${result['email'] ?? 'us'} instead and it will not be lost.';
        if (sent) _message.clear();
      });
    } catch (e) {
      setState(() {
        _ok = false;
        _outcome = 'Not sent — ${friendlyError(e)}';
      });
    } finally {
      setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
    children: [
      const Text(
        'What worked? What broke? What would you add?',
        style: TextStyle(color: Colors.white, fontSize: 14, height: 1.5),
      ),
      const Padding(
        padding: EdgeInsets.only(top: 6, bottom: 12),
        child: Text(
          'Screen and app version travel with it, so you do not have to describe where you were.',
          style: TextStyle(color: Colors.white38, fontSize: 11.5, height: 1.5),
        ),
      ),
      TextField(
        controller: _message,
        maxLines: 6,
        maxLength: 4000,
        autofocus: true,
        style: const TextStyle(color: Colors.white, fontSize: 13.5),
        decoration: InputDecoration(
          counterStyle: const TextStyle(color: Colors.white24, fontSize: 10),
          filled: true,
          fillColor: Colors.white10,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(Brand.radiusSm),
            borderSide: BorderSide.none,
          ),
        ),
      ),
      const SizedBox(height: 4),
      Align(
        alignment: Alignment.centerRight,
        child: TextButton(
          onPressed: _sending ? null : _send,
          style: TextButton.styleFrom(
            backgroundColor: Brand.purple,
            foregroundColor: Colors.white,
            disabledBackgroundColor: Colors.white10,
            padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 10),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(Brand.radiusSm),
            ),
          ),
          child: Text(
            _sending ? 'Sending…' : 'Send',
            style: const TextStyle(fontSize: 13.5),
          ),
        ),
      ),
      if (_outcome != null)
        Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Text(
            _outcome!,
            style: TextStyle(
              color: _ok ? Brand.good : Brand.warn,
              fontSize: 12,
              height: 1.5,
            ),
          ),
        ),
    ],
  );
}
