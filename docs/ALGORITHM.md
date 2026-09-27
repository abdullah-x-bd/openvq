# OpenVQ algorithm

OpenVQ is independently designed. It is not an implementation of POLQA and does not use ITU-T P.863 reference code.

## Branch scope

This document describes the stable native baseline on `main`.

The newer Phase 6 frontend and sequence-model research are maintained on `validation/phase6`. The Phase 6E neural candidate has not been promoted to main because it failed its independent engineering gate.

## Stable processing path

1. Decode PCM16 or IEEE float32 WAV and downmix to mono.
2. Resample both signals to 48 kHz.
3. Remove DC offset while retaining level information.
4. Build an amplitude envelope for coarse delay estimation.
5. Estimate global delay with normalized correlation.
6. Estimate sample-clock drift from local timing measurements.
7. Track local alignment while avoiding aggressive alignment through likely missing speech.
8. Run reference voice-activity analysis.
9. Compute spectral and perceptual evidence.
10. Calculate coloration, missing and added disturbance, level error, discontinuity, clipping, and noisiness.
11. Compute an ERB auditory representation and multi-resolution comparisons.
12. Measure temporal-envelope similarity, modulation similarity, asymmetry, tilt, active-level error, and worst intervals.
13. Combine calibrated degradation features.
14. Optionally accept an independently computed ViSQOL value as a historical expert signal.
15. Return quality, confidence, temporal events, and diagnostics.

## Calibration status

The calibration utilities are research infrastructure.

Checked-in or historical weights must not be interpreted as a currently externally validated replacement for POLQA.

The latest Phase 6.1 research result indicates that quality mapping remains the primary unresolved problem even when richer local sequence information is available.

## Root-cause separation

RF, RTP, IMS, codec, and mobility telemetry are excluded from the perceptual input and belong in downstream root-cause analysis.
