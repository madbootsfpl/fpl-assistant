/// First run: whose team is this? (ADR-279)
///
/// ⭐⭐ **The app asks rather than assuming.** It used to open on the author's squad — which a tester
/// reads as *"why am I looking at someone else's team?"*, and reads it before anything else the app
/// might say for itself.
///
/// ⚠️ **Not an account, deliberately.** An FPL manager id is public, needs no password, and is the only
/// thing the API takes. ⭐ *Asking for the minimum that works beats asking for the maximum that might be
/// useful later* — the accounts question is ADR-259's and is still open.
library;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'brand.dart';

class WelcomeView extends StatefulWidget {
  const WelcomeView({required this.onManagerId, super.key});

  final Future<void> Function(int) onManagerId;

  @override
  State<WelcomeView> createState() => _WelcomeViewState();
}

class _WelcomeViewState extends State<WelcomeView> {
  final TextEditingController _id = TextEditingController();
  String? _problem;

  @override
  void dispose() {
    _id.dispose();
    super.dispose();
  }

  void _submit() {
    final id = int.tryParse(_id.text.trim());
    // ⚠️ Checked here rather than left to the API. ⭐ *"That is not a number" answers faster and more
    // usefully than a round trip returning "manager not found".*
    setState(() {
      _problem = id == null || id < 1
          ? 'That does not look like a manager id — it is just digits, e.g. 1234567.'
          : null;
    });
    if (_problem == null) widget.onManagerId(id!);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: Brand.ink,
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(28, 24, 28, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'MAD',
                    style: TextStyle(
                      color: Brand.purpleLight,
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                    ),
                  ),
                  Text(
                    'BOOTS',
                    style: TextStyle(
                      color: Brand.orange,
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 22),
              const Text(
                'What is your FPL manager ID?',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                // ⭐ Says what it is for and what it is not — *an app asking for an identifier owes the
                // reader both.*
                'It is the number in your FPL team URL. Public, no password, and it only ever reads — '
                'nothing here can change your real team.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white54,
                  fontSize: 12.5,
                  height: 1.55,
                ),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _id,
                keyboardType: TextInputType.number,
                autofocus: true,
                textAlign: TextAlign.center,
                onSubmitted: (_) => _submit(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
                decoration: InputDecoration(
                  // ⭐ An obviously illustrative number, not a real manager's. ⚠️ *An example that is also a
                  // working value is one somebody will submit* — and the guard against a baked-in id is
                  // stronger with no exceptions in it.
                  hintText: '1234567',
                  hintStyle: const TextStyle(color: Colors.white24),
                  filled: true,
                  fillColor: Colors.white10,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
              if (_problem != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    _problem!,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Brand.warn, fontSize: 11.5),
                  ),
                ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: _submit,
                style: TextButton.styleFrom(
                  backgroundColor: Brand.purple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 13),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                  ),
                ),
                child: const Text(
                  'Show me my team',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),
              ),
              const SizedBox(height: 14),
              TextButton(
                // ⚠️ A way to *find* it, because "the number in your team URL" is only obvious to
                // someone who already knows. ⭐ *An instruction that assumes the answer is not help.*
                onPressed: () => launchUrl(
                  Uri.parse('https://fantasy.premierleague.com/my-team'),
                  mode: LaunchMode.externalApplication,
                ),
                child: const Text(
                  'Where do I find it?',
                  style: TextStyle(color: Colors.white38, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
