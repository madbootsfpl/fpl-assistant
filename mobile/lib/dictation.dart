/// Asking a question out loud (ADR-315).
///
/// ⭐⭐ **The platform's own recogniser** — iOS Speech, Android SpeechRecognizer, the Web Speech API in a
/// browser. It runs on the device, costs nothing, needs no server and adds no key to manage. ⚠️ *A hosted
/// transcriber would have been the expensive way to do the cheapest item on the list.*
///
/// ⭐ This holds no UI. It is the microphone as a small state machine, so `ask_view` can render it and the
/// tests can drive it without a device.
library;

import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Where the microphone is, from the reader's point of view.
enum Listening {
  /// Not listening — the ordinary state.
  idle,

  /// Listening. ⭐ The screen must say so unmistakably: *a microphone that is on and does not look on is
  /// the one thing a person will not forgive.*
  live,

  /// The device has no recogniser, or permission was refused.
  unavailable,
}

/// A thin seam over `speech_to_text` so the view can be tested without a microphone.
///
/// ⚠️ The plugin is asked for permission **at the moment the microphone is first tapped**, never at launch —
/// ⭐ *a permission asked before it is needed is a permission denied.*
class Dictation {
  Dictation({SpeechToText? speech}) : _speech = speech ?? SpeechToText();

  final SpeechToText _speech;
  bool _ready = false;

  /// Whether this device can listen at all. Safe to call repeatedly.
  Future<bool> available() async {
    if (_ready) return true;
    try {
      _ready = await _speech.initialize(
        onError: (e) => debugPrint('dictation: ${e.errorMsg}'),
        // ⚠️ `debugLogging` off: the plugin logs the partial transcript, and *a person's words are not
        // debug output.*
        debugLogging: false,
      );
    } catch (_) {
      _ready = false;
    }
    return _ready;
  }

  /// Start listening. [onWords] fires with the transcript so far, then a final time when speech stops.
  Future<void> start({
    required void Function(String words, bool done) onWords,
  }) async {
    if (!await available()) return;
    await _speech.listen(
      onResult: (r) => onWords(r.recognizedWords, r.finalResult),
      listenOptions: SpeechListenOptions(
        // ⭐ Dictation, not conversation: a question is one utterance and the field should fill as it is
        // spoken, so the reader can see it going wrong before they finish.
        partialResults: true,
        // ⚠️⚠️ **On-device where the platform offers it** (ADR-309 flagged this as a decision, not a
        // default). iOS will otherwise send audio to Apple for recognition; asking for on-device keeps a
        // person's voice on their phone. ⭐ It degrades rather than fails where the option is unsupported.
        onDevice: true,
        cancelOnError: true,
        // ⭐ Long enough for a full question, short enough that a forgotten microphone stops itself.
        listenFor: const Duration(seconds: 20),
        pauseFor: const Duration(seconds: 3),
      ),
    );
  }

  Future<void> stop() => _speech.stop();

  bool get isListening => _speech.isListening;
}
