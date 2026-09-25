# Phase 4 external validation protocol

This protocol is frozen before OpenVQ Phase 4 is scored on NISQA TEST_FOR or
NISQA TEST_NSC.

## Candidate

Model ID:

`phase4-native-poly2-anchored-2026-09-25-v2`

The candidate is the native-first Phase 4 v2 model embedded in `src/phase4_model.inc`. The learned cross-domain predictor is constrained to a 20 percent correction around the engineered native OpenVQ score. This anchor rule was fixed before TEST_FOR or TEST_NSC scoring.

The candidate may not be changed after any TEST_FOR or TEST_NSC OpenVQ score or
aggregate result is examined. Any later coefficient, feature, normalization,
expert-gating, clipping, or model-architecture change requires a new model ID
and a new untouched subjective corpus.

## Preconditions

External scoring must not begin until all of the following pass for the exact
candidate source:

1. Native C++ build and CTest.
2. Android AAR/JNI build.
3. Existing engineering validation matrix.
4. Phase 4 engineering validation matrix.

The exact source commit and model blob are recorded in the Phase 4 freeze file
before external results are interpreted.

## Untouched external sets

### NISQA TEST_FOR

Expected size: 240 degraded utterances.

This set has not been used for Phase 4 fitting, feature selection, model
selection, threshold selection, or previous OpenVQ scoring.

### NISQA TEST_NSC

Expected size: 240 degraded utterances.

This set has not been used for Phase 4 fitting, feature selection, model
selection, threshold selection, or previous OpenVQ scoring.

The two sets are evaluated separately. They must not be pooled to hide a weak
result on one set.

## Primary candidate

The primary external test is **native Phase 4**, invoked with `--phase4`
without ViSQOL expert inputs.

This deliberately tests whether OpenVQ can generalize as an independent native
metric.

Optional external experts may be evaluated later as a separately labelled
secondary analysis, but they cannot replace or alter the native Phase 4 result.

## Human target

Human MOS on its original 1 to 5 scale is the target.

For each external set report:

- utterance-level Pearson correlation
- utterance-level Spearman correlation
- RMSE
- MAE
- signed bias
- condition-level Pearson, Spearman, RMSE, MAE, and bias when condition IDs are
  available

No post-hoc score mapping is allowed for the primary result.

## Predeclared external-generalization criterion

This is a Project OpenVQ research criterion, not an ITU threshold.

For Phase 4 to pass this external-generalization gate, **both** TEST_FOR and
TEST_NSC must independently satisfy:

- Pearson >= 0.70
- Spearman >= 0.70
- RMSE <= 0.80 MOS

All metrics are still reported even if the gate fails.

Passing this gate means only that the frozen candidate generalized adequately
to these two untouched sets. It does not establish POLQA parity or P.863
conformance.

## POLQA

POLQA is not used for fitting Phase 4.

A POLQA-parity claim requires lawful per-utterance POLQA outputs for the exact
same reference/degraded pairs and a separately frozen paired comparison
protocol. Correlation to human MOS alone cannot establish POLQA parity.

## After unblinding

Once TEST_FOR or TEST_NSC results are observed:

- this Phase 4 model is frozen permanently for those results
- neither test set may be used to retune the same model and still be described
  as an untouched holdout
- a failure leads to a new model version and a different untouched corpus
