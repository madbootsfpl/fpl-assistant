/// More — the app's own housekeeping (ADR-228).
///
/// ⭐⭐ **Not a drawer for everything the web app can do.** The mobile audit §6 is explicit: *the mobile app
/// is the decision layer; the web app stays the exploration layer.* A "More" list that grew to eight items
/// would undo that positioning on the smaller screen — and this project already learned it the other way
/// round, when ADR-166 cut the web sidebar from twelve to nine **ordered by frequency** and ADR-167/170
/// answered "we need another board" with a reader instead.
///
/// ⚠️ **So this exists because the app had nowhere to put a setting**, not because there is spare room in
/// the bar. Free transfers were hard-coded to 1 with no control — ADR-191's exact failure, the app advising
/// a position the manager is not in, reintroduced on a phone.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class MoreView extends StatelessWidget {
  const MoreView({
    required this.team,
    required this.managerId,
    required this.freeTransfers,
    required this.onManagerId,
    required this.onFreeTransfers,
    required this.onOpenChips,
    required this.client,
    super.key,
  });

  final MyTeam team;
  final int managerId;
  final int freeTransfers;
  final ValueChanged<int> onManagerId;
  final ValueChanged<int> onFreeTransfers;

  /// ⭐ Chips lives here rather than in the bar — it works, and it is a handful of decisions per season.
  /// *Working earns a place; frequency earns a slot.*
  final VoidCallback onOpenChips;
  final ServiceClient client;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
        children: [
          const _Heading('Your team'),
          _ManagerIdRow(managerId: managerId, onChanged: onManagerId),
          _FreeTransfersRow(value: freeTransfers, onChanged: onFreeTransfers),

          const _Heading('This gameweek'),
          _Fact(label: 'Gameweek', value: '${team.gameweek ?? '—'}'),
          _Fact(
            label: 'In the bank',
            value: team.bank == null ? '—' : '£${team.bank!.toStringAsFixed(1)}m',
            // ⭐ Where each number comes from, because two of the three on the header are FPL's and one is
            // yours — and a reader cannot tell by looking.
            note: 'from FPL',
          ),
          _Fact(
            label: 'Squad value',
            value: team.value == null ? '—' : '£${team.value!.toStringAsFixed(1)}m',
            note: 'from FPL · includes the bank',
          ),
          if (team.activeChip != null)
            _Fact(label: 'Chip in play', value: team.activeChip!, note: 'from FPL'),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(team.deadlineLabel,
                style: const TextStyle(color: Colors.white38, fontSize: 11, height: 1.45)),
          ),

          const _Heading('Season decisions'),
          _Link(
            name: 'Chips',
            why: 'Wildcard, Bench Boost, Triple Captain and Free Hit — judged over the weeks you have '
                'left, not the next one.',
            onTap: onOpenChips,
          ),

          const _Heading('Under review'),
          const _Pending(
            name: 'Signals',
            why: 'What should I know? — official news, an unexplained transfer exodus, headlines, and '
                'community chatter, ordered by how much each source actually knows. Arguably belongs '
                'here: it is time-sensitive and actionable before a deadline, which is what a phone is '
                'for. The app already carries its conclusions on your own players — the flags and the '
                '✈ — but has no view of what CHANGED.',
          ),

          const _Heading('On the web'),
          const _Note(
            'madboots.streamlit.app carries the research surfaces: the fixture ticker, Team DNA, the '
            'player pool and stat boards, and Trending.',
          ),
          const _Note(
            // ⭐ The positioning, said out loud rather than implied by absence. Someone who cannot find
            // Team DNA here should learn that it is a decision, not an oversight.
            'That split is deliberate. This app is the decision layer — what to do this week, and what a '
            'move is worth. The web app stays the exploration layer, where a bigger screen earns its keep.',
            muted: true,
          ),

          const _Heading('Tell us something'),
          _Feedback(client: client),

          const _Heading('About'),
          const _Note(Brand.mantra, italic: true),
          const _Note(Brand.disclaimer, muted: true),
        ],
      );
}

class _Heading extends StatelessWidget {
  const _Heading(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20, bottom: 6),
        child: Text(text.toUpperCase(),
            style: const TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1.2)),
      );
}

class _ManagerIdRow extends StatefulWidget {
  const _ManagerIdRow({required this.managerId, required this.onChanged});

  final int managerId;
  final ValueChanged<int> onChanged;

  @override
  State<_ManagerIdRow> createState() => _ManagerIdRowState();
}

class _ManagerIdRowState extends State<_ManagerIdRow> {
  late final TextEditingController _controller =
      TextEditingController(text: '${widget.managerId}');

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final id = int.tryParse(_controller.text.trim());
    if (id != null && id > 0) widget.onChanged(id);
  }

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          children: [
            const Expanded(
              child: Text('FPL manager id',
                  style: TextStyle(color: Colors.white, fontSize: 14)),
            ),
            SizedBox(
              width: 110,
              height: 34,
              child: TextField(
                controller: _controller,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.end,
                onSubmitted: (_) => _submit(),
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: InputDecoration(
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  filled: true,
                  fillColor: Colors.white10,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            IconButton(
              onPressed: _submit,
              icon: const Icon(Icons.check, size: 18, color: Colors.white54),
              tooltip: 'Load this team',
            ),
          ],
        ),
      );
}

/// ⚠️⚠️ **The one number FPL will not tell us**, and it changes the advice.
///
/// ADR-191: the app once hard-coded this to 1 while the Transfer tab collected it three tabs away, so the
/// surface a manager read was advising a position he was not in. ⭐ It was hard-coded again on the phone —
/// because until now there was nowhere to put it.
class _FreeTransfersRow extends StatelessWidget {
  const _FreeTransfersRow({required this.value, required this.onChanged});

  final int value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text('Free transfers',
                      style: TextStyle(color: Colors.white, fontSize: 14)),
                ),
                for (var n = 0; n <= 5; n++)
                  GestureDetector(
                    onTap: () => onChanged(n),
                    behavior: HitTestBehavior.opaque,
                    child: Container(
                      width: 30,
                      height: 30,
                      margin: const EdgeInsets.only(left: 4),
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: n == value ? Brand.purple : Colors.white10,
                        borderRadius: BorderRadius.circular(Brand.radiusSm),
                      ),
                      child: Text('$n',
                          style: TextStyle(
                              color: n == value ? Colors.white : Colors.white54, fontSize: 12.5)),
                    ),
                  ),
              ],
            ),
            const Padding(
              padding: EdgeInsets.only(top: 5),
              child: Text(
                'FPL does not publish this, so the app has to ask. The week’s plan recommends this many '
                'moves.',
                style: TextStyle(color: Colors.white38, fontSize: 10.5, height: 1.45),
              ),
            ),
          ],
        ),
      );
}

class _Fact extends StatelessWidget {
  const _Fact({required this.label, required this.value, this.note});

  final String label;
  final String value;
  final String? note;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Row(
          children: [
            Expanded(
              child: Text(label, style: const TextStyle(color: Colors.white, fontSize: 14)),
            ),
            if (note != null)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: Text(note!,
                    style: const TextStyle(color: Colors.white24, fontSize: 10.5)),
              ),
            Text(value,
                style: const TextStyle(
                    color: Colors.white70, fontSize: 13.5, fontWeight: FontWeight.w600)),
          ],
        ),
      );
}

/// ⭐ Named with a reason, not greyed out. *"Not built yet" is information; an empty row is a bug report.*
class _Pending extends StatelessWidget {
  const _Pending({required this.name, required this.why});

  final String name;
  final String why;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(name, style: const TextStyle(color: Colors.white54, fontSize: 14)),
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(why,
                  style: const TextStyle(color: Colors.white24, fontSize: 11, height: 1.45)),
            ),
          ],
        ),
      );
}

/// A row that goes somewhere. ⭐ Distinct from `_Pending`, which deliberately does not.
class _Link extends StatelessWidget {
  const _Link({required this.name, required this.why, required this.onTap});

  final String name;
  final String why;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name, style: const TextStyle(color: Colors.white, fontSize: 14)),
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(why,
                          style: const TextStyle(
                              color: Colors.white38, fontSize: 11, height: 1.45)),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, size: 18, color: Colors.white38),
            ],
          ),
        ),
      );
}

/// ⭐⭐ **A tester on a phone is more likely to notice something and less likely to be near a laptop** —
/// which is why this is here and not only on the web.
///
/// ⚠️ **It never says "sent" unless the relay said so.** `relay_result` exists because the web form once
/// reported success while a relay silently refused — *a success message that cannot fail is not a success
/// message* — so the server's verdict is what this renders, failures included.
class _Feedback extends StatefulWidget {
  const _Feedback({required this.client});

  final ServiceClient client;

  @override
  State<_Feedback> createState() => _FeedbackState();
}

class _FeedbackState extends State<_Feedback> {
  final TextEditingController _message = TextEditingController();
  bool _sending = false;
  String? _outcome;
  bool _ok = false;

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _message.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _outcome = null;
    });
    try {
      final result = await widget.client.feedback(message: text, screen: 'mobile', version: '0.0.1');
      final sent = result['sent'] == true;
      setState(() {
        _ok = sent;
        _outcome = sent
            ? 'Thanks — that reached us.'
            // ⭐ The real reason, and the way through. "Something went wrong" tells a tester nothing and
            // loses the report.
            : 'Not sent — ${result['reason'] ?? 'the service refused it'}. '
                'Email ${result['email'] ?? 'us'} instead and it will not be lost.';
        if (sent) _message.clear();
      });
    } catch (e) {
      setState(() {
        _ok = false;
        _outcome = 'Not sent — $e';
      });
    } finally {
      setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _message,
            maxLines: 3,
            maxLength: 4000,
            style: const TextStyle(color: Colors.white, fontSize: 13.5),
            decoration: InputDecoration(
              hintText: 'What worked? What broke? What would you add?',
              hintStyle: const TextStyle(color: Colors.white38, fontSize: 12.5),
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
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm)),
              ),
              child: Text(_sending ? 'Sending…' : 'Send', style: const TextStyle(fontSize: 13)),
            ),
          ),
          if (_outcome != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(_outcome!,
                  style: TextStyle(
                      color: _ok ? Brand.good : Brand.warn, fontSize: 11.5, height: 1.45)),
            ),
        ],
      );
}

class _Note extends StatelessWidget {
  const _Note(this.text, {this.muted = false, this.italic = false});

  final String text;
  final bool muted;
  final bool italic;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(text,
            style: TextStyle(
              color: muted ? Colors.white24 : Colors.white54,
              fontSize: 11.5,
              height: 1.5,
              fontStyle: italic ? FontStyle.italic : FontStyle.normal,
            )),
      );
}
