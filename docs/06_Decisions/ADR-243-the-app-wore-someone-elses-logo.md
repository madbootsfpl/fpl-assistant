# ADR-243 — The app wore someone else's logo

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"Need both logo and MADBOOTS at the header and the logo as the app logo."*

---

## Context

The icon on the home screen was **Flutter's default blue mark**. It had been since `flutter create`, through
sixteen ADRs of feature work.

⭐⭐ **Nobody noticed until it was on a phone**, which is the observation worth keeping: on a simulator you
know which app you just launched, and on a desktop build it is a window you opened. An icon only has a job
in a grid of other icons. ⚠️ *A defect that only exists in the real setting cannot be found anywhere else,
however carefully you look.*

The header had the wordmark alone.

## Decision

**`scripts/generate_app_icon.py`**, composing the MADBOOTS badge onto the brand's ink.

⭐ **The size table is read out of Xcode's own `Contents.json`**, not written down. A hard-coded list of
Apple's idioms goes stale the next time Xcode adds one, and the symptom is a missing icon **in one place
only** — the hardest kind to notice.

⚠️⚠️ **Opaque, because iOS rejects an icon with an alpha channel.** The badge is RGBA with a transparent
surround, so it is pasted *through its own alpha* onto `brand.INK` — which is read from `brand.py`, never
typed here (ADR-103/114). The badge's own dark preview uses the same ground.

**The same script writes the header badge** as a Flutter asset — transparent this time, because the header
sits on the app's own background and an inked square would show as a box. ⭐ *One script, one master: the
mark on the home screen and the mark in the header cannot drift apart.*

**The header now carries the badge beside the wordmark.** On a phone the badge is what a person
recognises — it is what they tapped a second earlier.

## ⚠️ On resolution, plainly

The badge master is **298×298**. The largest icon iOS renders **on a device** is 180×180 (60pt @3x), so
every on-device size is a *downscale* and loses nothing.

🔴 **The 1024 asset is upscaled and will be soft.** It is used only by the App Store, which is not
something this project does yet.

📌 **Owed before any submission:** a proper 1024 render from `~/Downloads/madboots1.svg` — real vector, five
paths, checked. This machine has no SVG rasteriser installed (`rsvg-convert`, `cairosvg` and `inkscape` all
absent), and installing one is a decision for whoever does the submission, not a thing to do in passing.

## Consequences

* The app looks like itself on a home screen.
* ⭐ Regenerating is one command, so a new badge propagates to 22 icons and the header together.
* ⚠️ `mobile/assets/` is a new directory and `pubspec.yaml` now declares assets, which it did not before —
  worth knowing for anyone adding the second one.
