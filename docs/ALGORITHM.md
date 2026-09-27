# OpenVQ algorithm

OpenVQ is independently designed. It is not an implementation of POLQA and does not use ITU-T P.863 reference code.

## Native processing path

1. Decode supported WAV PCM/float input and downmix to mono.
2. Prepare reference and degraded signals through one shared frontend.
3. Resample to 48 kHz with the shared windowed-sinc resampler.
4. Remove DC through the shared preparation path.
5. Estimate global delay.
6. Detect essentially exact transport-only delay and preserve the global alignment when appropriate.
7. Estimate clock drift.
8. Build a bounded piecewise-continuous local alignment map.
9. Compute local and global alignment confidence.
10. Run reference activity analysis.
11. Measure active coverage and lost active speech.
12. Measure matched active levels.
13. Compute spectral and perceptual-band representations.
14. Calculate missing and added disturbance, coloration, level mismatch, discontinuity, and clipping.
15. Compare 20 ms, 80 ms, and 200 ms temporal resolutions.
16. Measure temporal-envelope and modulation-spectrum similarity.
17. Measure asymmetric disturbance, spectral tilt, echo, choppiness, PLC-like repetition, residual intrusion, and worst-interval severity.
18. Pool global interpretable statistics.
19. Optionally export the Phase 6 local trace before utterance pooling.
20. Return native diagnostics, alignment metadata, and research score-path outputs.

## Frontend contract

The Phase 6A frontend is frozen as:

`openvq-frontend-phase6a-2026-09-26-v1`

The engineering contract includes active Release tests, periodic-delay regressions, six-reference real-speech checks, and independent transport-delay behavior.

## Global representations

`legacy19` retains the original 19 aggregate measurements.

`rich-v2` contains 31 aggregate features.

`rich-v3` extends the representation with raw input clipping and is bound to the frozen Phase 6A frontend.

## Local sequence representation

`openvq-trace-v1-2026-09-26` preserves local evidence at a 10 ms hop using:

- 64 reference auditory bands;
- 64 degraded auditory bands;
- reference activity;
- valid coverage;
- unmatched state;
- local alignment confidence;
- local similarity;
- reference/degraded RMS;
- mapped-time offset;
- rich-v3 global side information.

Inactive and unmatched regions remain explicit rather than being silently discarded.

## Mapping research

Phase 6B established that balanced neural mapping over global summaries improves known-domain development performance but does not solve leave-corpus-out transfer.

Phase 6E then compared three compact sequence models.

The hybrid architecture won the frozen worst-corpus selection rule, but its full-development candidate failed engineering sanity. The current algorithm therefore does not use that neural candidate as the released quality mapping.

## Engineering constraints

Model quality is evaluated independently from subjective fit.

A promotable model must preserve at least:

- high identity quality;
- transport-delay invariance within the frozen tolerance;
- worsening quality under stronger dropout;
- worsening quality under repeated dropout;
- worsening quality under stronger noise;
- worsening quality under stronger low-pass restriction;
- worsening quality under stronger clipping;
- worsening quality under mixed degradation.

The Phase 6E hybrid candidate failed identity, dropout, dropout-count, mixed, and noise checks.

## Downstream scope

RF, RTP, IMS, codec, and mobility telemetry are excluded from the perceptual input.

Those signals belong in downstream root-cause models, not in the full-reference perceptual quality metric.
