# Validation history

This document records both successful and unsuccessful OpenVQ validation results.

## Principle

Validation failures are retained. A failed external benchmark is evidence about the model and should not be erased by retuning the same candidate on the same holdout.

## Phase 1

The project established the native C++ full-reference engine, Android integration, deterministic impairment tests, signal alignment, perceptual-band disturbance measures, and initial telecom diagnostics.

The original weights were engineering bootstrap values. No POLQA-parity claim was made.

## Phase 2

Phase 2 expanded the native telecom diagnostics after early human-MOS testing exposed under-penalization of several impairments.

Additions included:

- delayed-copy echo analysis
- choppiness and local temporal-edit analysis
- residual-intrusion analysis
- stronger clipping and silence-region diagnostics
- codec and network laboratory workflows
- NISQA TEST P501 as an external holdout

## Phase 3

Phase 3 evaluated whether external perceptual experts improved generalization.

Google ViSQOL v3.3.3 was pinned and run in:

- speech mode
- audio mode

A nonlinear monotonic mapper was fitted using TCD train and development data only. NISQA TEST P501 was kept external to that fit.

The frozen candidate is:

`phase3-tcd-only-2026-09-24-f099129`

### TCD held-out test

Utterance level:

- n = 60
- Pearson = 0.9541
- Spearman = 0.9375
- RMSE = 0.4335
- MAE = 0.3665
- bias = +0.2830 MOS

Condition level:

- n = 15
- Pearson = 0.9800
- Spearman = 0.9571
- RMSE = 0.3844

### NISQA TEST P501 external holdout

Utterance level:

- n = 240
- Pearson = 0.8185
- Spearman = 0.8209
- RMSE = 0.6011
- MAE = 0.4904
- bias = +0.1348 MOS

Condition level:

- n = 60
- Pearson = 0.8721
- Spearman = 0.8725
- RMSE = 0.5003

These results showed useful out-of-dataset performance, but did not establish POLQA parity.

## Locked POLQA protocol

Before licensed POLQA outputs were supplied for the locked TCD and NISQA sets, the repository froze a direct comparison protocol in `validation/LOCKED_POLQA_PROTOCOL.md`.

Its primary comparison is RMSE to human MOS.

The predeclared non-inferiority margin is +0.10 MOS RMSE:

`delta_RMSE = RMSE(OpenVQ, human) - RMSE(POLQA, human)`

The criterion passes only if the upper bound of the paired-bootstrap 95 percent confidence interval is below +0.10 MOS on both locked sets.

This is a Project OpenVQ experimental criterion, not an ITU conformance threshold.

## EARS-EMO-OpenACE external benchmark

OpenACE was introduced after the Phase 3 candidate had already been frozen.

The benchmark contains 144 codec-processed samples across EVS, LC3, LC3Plus, and Opus. Human subjective quality is reported on a MUSHRA scale. Published POLQA scores are available for 143 samples.

The OpenACE protocol was frozen before OpenVQ scoring.

### Result

Association with human MUSHRA:

| System | Pearson | Spearman |
| --- | ---: | ---: |
| Frozen Phase 3 OpenVQ | 0.1607 | 0.1465 |
| Published POLQA | 0.7939 | 0.7818 |
| Published OpenACE ViSQOL | 0.7034 | 0.6631 |
| Recomputed ViSQOL speech mode | 0.3305 | 0.3129 |
| Recomputed ViSQOL audio mode | 0.6644 | 0.6254 |

For the 143 paired OpenVQ/POLQA rows:

- delta Pearson, OpenVQ minus POLQA = -0.6328
- 95 percent cluster-bootstrap interval = [-0.7965, -0.4813]

This is a clear Phase 3 generalization failure on this domain.

### What failed

Phase 3 gave substantial influence to speech-mode ViSQOL. That expert was highly useful on TCD and NISQA but weak on OpenACE.

The frozen OpenVQ result consequently compressed codec quality severely. Approximate OpenVQ codec means remained close together while human MUSHRA separated the codecs strongly.

The result does not mean the native OpenVQ analyzer is equivalent to the failed fused output. It means the frozen Phase 3 fusion strategy was not robust across domains.

## Consequence

Phase 3 is preserved unchanged for reproducibility.

OpenACE is now development evidence for Phase 4 and cannot be reused as untouched proof that Phase 4 generalizes.

A new external subjective corpus is required before a Phase 4 generalization claim.

## Current scientific status

OpenVQ is not currently demonstrated to be at POLQA parity.

The evidence supports:

- strong performance on the frozen TCD test
- useful external performance on NISQA P501
- a clear failure on OpenACE
- a concrete diagnosis that fixed expert weighting is fragile across domains

Phase 4 addresses that failure directly.

## Phase 4 development candidate

The selected candidate is `phase4-native-poly2-balanced-2026-09-25-v1`.

It was fitted using all currently inspected development evidence: 384 TCD samples, 240 NISQA P501 samples, and 144 OpenACE samples. The model is native-first and can run without ViSQOL.

Grouped development cross-validation produced:

- NISQA P501: native Pearson 0.7103; optional-expert Pearson 0.7529
- OpenACE: native Pearson 0.8315; optional-expert Pearson 0.8520
- full TCD: native Pearson 0.8029; optional-expert Pearson 0.8283

The optional external-expert contribution is capped at 40 percent and uses a median consensus so one bad expert cannot dominate the final score.

These numbers are development evidence only. A new untouched corpus is required before Phase 4 is described as externally validated.


## Phase 4 frozen external validation

Frozen candidate:

`phase4-native-poly2-constrained-2026-09-25-v3`

Frozen source commit:

`d530382d6161d0a5dc3d019782192a047982f839`

The Phase 4 candidate passed the native build, Android/native regression tests, codec and network laboratories, and the deterministic engineering matrix before external scoring.

### NISQA TEST_FOR

This set was not used in Phase 4 fitting or model selection before unblinding.

Utterance level, n = 240:

- Pearson = 0.6148
- Spearman = 0.5892
- RMSE = 0.7503 MOS
- MAE = 0.5878 MOS
- bias = +0.1005 MOS

Condition level, n = 60:

- Pearson = 0.7323
- Spearman = 0.6598
- RMSE = 0.5842 MOS
- MAE = 0.4717 MOS
- bias = +0.1005 MOS

The predeclared utterance-level criterion required Pearson >= 0.70, Spearman >= 0.70, and RMSE <= 0.80. RMSE passed, but Pearson and Spearman did not. Phase 4 therefore failed the TEST_FOR gate.

GitHub Actions run:

`36208421278`

Artifact:

`openvq-phase4-external-v3`, artifact ID `10894988692`

Artifact SHA-256:

`a9f0482f3eb2913918e162b3217bf07891b9bf6da58c6cd16aa070f1e7f19bb4`

### NISQA TEST_NSC

The public NISQA documentation identifies TEST_NSC as a 240-file test set, but the public NISQA archive endpoints used by the workflow did not expose a TEST_NSC path in their ZIP directory listings.

No OpenVQ TEST_NSC score was produced.

The workflow was changed only to diagnose upstream packaging and to allow TEST_FOR to run independently. The frozen model and TEST_FOR criteria were not changed.

### TMHINT-QI version II test fallback

Because TEST_NSC could not be obtained, a second independent holdout protocol was frozen before any Phase 4 TMHINT score existed.

The deterministic full-reference subset contained 1,455 non-clean test files paired with the unique clean test row sharing the same dataset utterance ID.

Overall result:

- Pearson = 0.2116
- Spearman = 0.2580
- RMSE = 2.1336 MOS
- MAE = 2.0072 MOS
- bias = -1.9891 MOS

This is a clear cross-domain failure.

GitHub Actions run:

`36208883292`

Artifact:

`openvq-phase4-tmhint-external-v3`, artifact ID `10894734342`

Artifact SHA-256:

`800b1b927f42818d8202bc160c6de6eb15eff6341472ad53e0a24babeae23fc2`

### Phase 4 conclusion

Phase 4 v3 is an engineering-valid but scientifically failed generalization candidate.

It must not be described as a general POLQA replacement or as externally validated across speech-quality domains.

NISQA TEST_FOR and TMHINT-QI are now development evidence for any later model. They cannot be reused as untouched validation for Phase 5.
