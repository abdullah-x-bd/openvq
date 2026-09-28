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

The current Phase 6 local representation is:

`openvq-trace-v2-2026-09-27`

with implementation:

`openvq-trace-spectral-v2-fft-corrected-2026-09-27`.

Trace V2 preserves local evidence at a 10 ms hop using:

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

Trace V2 supersedes Trace V1 after correction of the trace-only FFT butterfly indexing defect. The frozen Phase 6A native analyzer was unaffected by that historical defect.

## Mapping research

Phase 6B established that balanced neural mapping over global summaries improves known-domain development performance but does not solve leave-one-corpus-out transfer.

Corrected Trace V2 changed the sequence-model conclusion. Under the unchanged Phase 6.2C grid, `learned_bands` became the preferred architecture and raw hybrid fusion collapsed.

Phase 6.2E then made the learned-bands temporal path padding-safe by masking padded frames after each encoder and TCN stage and replacing BatchNorm1d with per-frame channel LayerNorm.

Phase 6.2F aligned full-development qualification with the same three-seed ensemble used in evaluation. It isolated one remaining protected failure: severe clipping ordering.

Phase 6.2G kept the architecture fixed and added only a clipping-order hinge constraint using property fixtures that are separate from the protected engineering gate.

The final research mapper is therefore:

- architecture `learned_bands_padding_safe_clipreg`;
- three fixed seeds;
- arithmetic mean of raw quality predictions;
- clamp ensemble quality to [0,1] before MOS conversion.

This mapper is an engineering-qualified development artifact. It is not yet the stable released quality mapping because untouched external validation is still pending.

## Engineering constraints

Model quality is evaluated independently from subjective fit.

A promotable research candidate must preserve at least:

- high identity quality;
- transport-delay invariance within the frozen tolerance;
- worsening quality under stronger dropout;
- worsening quality under repeated dropout;
- worsening quality under stronger noise;
- worsening quality under stronger low-pass restriction;
- worsening quality under stronger clipping;
- worsening quality under mixed degradation.

The Phase 6.2G three-seed ensemble passed the unchanged protected gate:

- identity 4.6062 MOS;
- pure-delay maximum absolute change 0.00924 MOS;
- zero >0.12 MOS reversals across clipping, dropout, repeated dropout, noise, low-pass, and mixed degradation.

The engineering-qualified bundle is `openvq-phase62g-749eaa80ea0a796cc15c`.

Engineering qualification is a prerequisite for external validation. It is not evidence of external subjective validity by itself.

## Downstream scope

RF, RTP, IMS, codec, and mobility telemetry are excluded from the perceptual input.

Those signals belong in downstream root-cause models, not in the full-reference perceptual quality metric.
