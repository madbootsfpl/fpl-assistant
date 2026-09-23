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
import 'contact_store.dart';

class FeedbackView extends StatefulWidget {
  const FeedbackView({required this.client, this.from = '', super.key});

  final ServiceClient client;

  /// ⭐ **The screen the tester was actually on**, so the report says where it happened.
  ///
  /// ⚠️⚠️ This used to be the literal string `'mobile'`, hardcoded — while the screen's own copy promised
  /// *"Screen and app version travel with it, so you do not have to describe where you were."* ⭐ *Every
  /// report said "mobile", and the promise on the page was the reason nobody thought to add the detail
  /// by hand* (ADR-263).
  final String from;

  @override
  State<FeedbackView> createState() => _FeedbackViewState();
}

class _FeedbackViewState extends State<FeedbackView> {
  final TextEditingController _message = TextEditingController();
  final TextEditingController _contact = TextEditingController();
  final ContactStore _contacts = ContactStore();
  bool _sending = false;
  String? _outcome;
  bool _ok = false;

  @override
  void initState() {
    super.initState();
    _contacts.load().then((saved) {
      if (mounted && saved.isNotEmpty) _contact.text = saved;
    });
  }

  @override
  void dispose() {
    _message.dispose();
    _contact.dispose();
    super.dispose();
  }

  /// What the report says it is about. ⭐ Falls back to naming the app rather than claiming a screen we
  /// do not know — ⚠️ *an invented location is worse than none, because it is believed.*
  String get _screen =>
      widget.from.trim().isEmpty ? 'mobile' : widget.from.trim();

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
      final contact = _contact.text.trim();
      // ⚠️ Saved before the send, not after: a tester whose report fails still typed their address once.
      await _contacts.save(contact);
      final result = await widget.client.feedback(
        message: text,
        contact: contact,
        screen: _screen,
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
      Padding(
        padding: const EdgeInsets.only(top: 6, bottom: 12),
        child: Text(
          // ⭐ It names the screen rather than claiming one travels along. ⚠️ *A promise the reader can
          // check is worth more than a promise they must take on trust* — and this one was false.
          'Sent as a report about $_screen, with the app version.',
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 11.5,
            height: 1.5,
          ),
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
      const SizedBox(height: 10),
      TextField(
        controller: _contact,
        keyboardType: TextInputType.emailAddress,
        autocorrect: false,
        style: const TextStyle(color: Colors.white, fontSize: 13.5),
        decoration: InputDecoration(
          // ⭐ Labelled by what it BUYS the tester, not by what it is. *"Email (optional)" asks for data;
          // "so we can reply" says why it is worth giving* — and a beta runs on replies.
          hintText: 'Email, so we can reply (optional)',
          hintStyle: const TextStyle(color: Colors.white24, fontSize: 12.5),
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
