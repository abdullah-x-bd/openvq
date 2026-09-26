# OpenVQ algorithm

OpenVQ is independently designed. It is not an implementation of POLQA and does not use ITU-T P.863 reference code.

This page describes the native measurement path after the Phase 5.1 repair.

## Processing path

1. Decode supported WAV PCM/float input and downmix to mono.
2. Prepare reference and degraded signals through the same shared preprocessing path.
3. Resample to the internal fullband rate using the shared windowed-sinc resampler.
4. Remove DC through the shared preparation path.
5. Estimate coarse global delay from envelope correlation.
6. Estimate clock drift from timing measurements across multiple temporal regions.
7. Build a bounded piecewise-continuous local alignment map.
8. Prevent local alignment from making arbitrary jumps through low-correlation or missing-speech regions.
9. Run reference voice activity analysis.
10. Measure active-reference duration and how much of that active speech is covered by the degraded signal.
11. Record lost-active-speech fraction explicitly.
12. Measure matched active-speech reference and degraded levels.
13. Compute frame spectral analysis and perceptual band representations.
14. Calculate missing and added disturbance, coloration, level mismatch, discontinuity, and clipping.
15. Compute ERB auditory comparison.
16. Compare at 20 ms, 80 ms, and 200 ms resolutions using the shared alignment map.
17. Measure temporal-envelope and modulation-spectrum similarity.
18. Measure asymmetric disturbance, spectral tilt, active-level error, echo, choppiness, residual intrusion, and worst-interval severity.
19. Pool interpretable utterance statistics.
20. Return native diagnostics, confidence, alignment metadata, and score-path outputs.

## Why shared preprocessing matters

Before Phase 5.1, base and advanced analysis could make partially different frontend assumptions.

Phase 5.1 introduced a single prepared signal pair used across both layers.

This makes a feature difference more likely to represent an actual acoustic/perceptual difference rather than a frontend mismatch.

## Why bounded alignment matters

Full-reference quality metrics need to compensate for nuisance delay and small timing changes.

But overly flexible alignment can create a different problem: it can align around missing speech and make a true deletion look harmless.

Phase 5.1 therefore uses a bounded continuous alignment map and records alignment confidence/coverage.

The algorithm treats missing active reference speech as evidence.

## Feature representations

### legacy19

The exact 19 aggregate measurements used by the Phase 5 v1 family.

It is retained for historical comparison and ablation.

### rich-v2

The 19 legacy values plus:

1. lost active speech
2. active coverage
3. alignment uncertainty
4. raw active-level delta
5. similarity p10 loss
6. similarity p50 loss
7. discontinuity p90
8. longest bad interval
9. severe-frame fraction
10. absolute clock drift
11. raw clipping ratio
12. confidence deficit

The Phase 5.1 fixed-evidence experiment showed that rich-v2 improved the constrained model's weakest development correlation from 0.3897 to 0.4337.

A small MLP using rich-v2 improved the weakest development correlation to 0.5304.

These are development diagnostics, not product validation.

## Mapping philosophy

The project has learned that a single scalar mapping must not be judged only on pooled fit.

A mapping can look strong when it has seen examples from every domain and still collapse on a new corpus.

For this reason, future mapping work must consider:

- corpus-balanced fitting;
- grouped validation;
- leave-corpus-out validation;
- processing-family transfer;
- saturation;
- independent engineering behavior.

## Current product model status

The Phase 5.1 constrained rich-v2 export is reproducible but is not promoted into the product runtime.

The reason is scientific: held-out OpenACE and TMHINT transfer is poor.

The small MLP is also diagnostic only.

Phase 6 is expected to test learned representation/mapping approaches while preserving this repaired native measurement path.

## Bandwidth and diagnostics

The native engine continues to expose bandwidth classification and impairment dimensions independently of the research mapper.

These diagnostics can remain operationally useful even while scalar MOS modeling evolves.

## Separation from root-cause analysis

RF, RTP, IMS, codec, and mobility telemetry are intentionally excluded from the perceptual speech-quality input.

They belong in downstream root-cause models.

This prevents non-audio network metadata from artificially improving an audio-quality score and keeps the perceptual metric independently testable.
