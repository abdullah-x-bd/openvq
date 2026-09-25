# Phase 4 robust fusion

## Objective

Phase 4 fixes the generalization failure exposed by EARS-EMO-OpenACE without hiding or rewriting the Phase 3 result.

The design target is not to make one benchmark look good. The target is a native OpenVQ model that predicts human quality across distinct domains while remaining physically sensible on known telecom degradations.

## Why Phase 3 failed

Frozen Phase 3 gave too much influence to speech-mode ViSQOL. On OpenACE, speech-mode ViSQOL was weak and the combined OpenVQ score collapsed.

The forensic run showed that this was a fusion problem rather than a lack of native information:

- Phase 3 speech-expert contribution represented about 68.5 percent of the variable penalty on OpenACE.
- Native-only OpenVQ features reached Pearson 0.9065 and Spearman 0.8529 in a leave-one-speaker-out diagnostic model.
- The two ViSQOL experts alone reached Pearson 0.6659 and Spearman 0.6379.

Those values are development evidence, not untouched validation.

## Selected Phase 4 candidate

Model ID:

`phase4-native-poly2-constrained-2026-09-25-v3`

Development data:

- TCD-VoIP: 384 samples
- NISQA TEST P501: 240 samples
- EARS-EMO-OpenACE: 144 samples

The native predictor uses 19 normalized OpenVQ-native features plus all degree-two products.

The three subjective datasets receive equal total fitting weight.

### Engineering constraints

The regression is fitted under explicit linear inequality constraints generated from the deterministic engineering matrix.

The fitted model must satisfy:

- identity MOS at least 4.5
- supported sample-rate identity MOS at least 4.2
- pure-delay score change no larger than 0.45 MOS
- non-increasing quality with worsening dropout duration
- non-increasing quality with more repeated dropouts
- non-increasing quality with worsening additive noise
- non-increasing quality with stronger low-pass restriction
- non-increasing quality with stronger clipping
- non-increasing quality with attenuation
- non-increasing quality with clock drift
- non-increasing quality with time-scale distortion
- non-increasing quality with the predefined mixed-impairment severity

These constraints are development priors. They do not substitute for subjective validation.

### Model selection

Five-fold grouped cross-validation is used. TCD conditions and OpenACE speakers are kept grouped. The selected ridge regularization is alpha 3.0.

The optional expert layer uses the median of native quality, ViSQOL speech quality and ViSQOL audio quality, with the expert consensus capped at 40 percent of the final score.

Primary external validation remains native-only.

### Grouped development cross-validation

| Dataset | Native Pearson | Native Spearman | Optional-expert Pearson | Optional-expert Spearman |
| --- | ---: | ---: | ---: | ---: |
| NISQA P501 | 0.7099 | 0.7092 | 0.7542 | 0.7453 |
| OpenACE | 0.8403 | 0.8143 | 0.8584 | 0.8319 |
| Full TCD | 0.8068 | 0.8057 | 0.8292 | 0.8249 |

These are development cross-validation results. They are not untouched external validation.

The important improvement over Phase 3 is that the candidate no longer needs a fixed dominant ViSQOL expert and is mathematically prevented from learning several obvious engineering reversals.

## ViSQOL relationship

Phase 4 is native-first.

The native score requires no ViSQOL input.

If both ViSQOL experts are supplied, they provide a bounded secondary consensus correction. A single expert cannot determine the result.

## External validation rule

OpenACE and NISQA P501 have influenced Phase 4 development and are no longer untouched holdouts.

The next Phase 4 claim must use subjective material not used for fitting, feature selection, model selection, threshold selection or engineering tuning.

The frozen external protocol is in `validation/PHASE4_EXTERNAL_PROTOCOL.md`.

## Product implication

Until Phase 4 passes untouched external validation, OpenVQ should not be marketed as generally equivalent to or better than POLQA.

It can already be integrated experimentally in a drive-test product for:

- native OpenVQ quality scoring
- diagnostic dimensions
- side-by-side field collection
- validation data generation

A broad POLQA-replacement claim requires the external generalization gate and then a lawful paired POLQA comparison.
