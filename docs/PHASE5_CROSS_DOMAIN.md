# Phase 5 cross-domain redesign

Phase 5 begins because the frozen Phase 4 v3 candidate failed its untouched external tests.

## Frozen Phase 4 external results

NISQA TEST_FOR, native Phase 4, n=240:

- Pearson 0.6148
- Spearman 0.5892
- RMSE 0.7503 MOS
- MAE 0.5878 MOS
- bias +0.1005 MOS

The RMSE criterion passed, but the predeclared Pearson and Spearman thresholds did not.

TMHINT-QI version II full-reference subset, n=1455:

- Pearson 0.2116
- Spearman 0.2580
- RMSE 2.1336 MOS
- MAE 2.0072 MOS
- bias -1.9891 MOS

This is a major cross-domain failure, especially for noisy and enhancement-system speech.

Phase 4 v3 is permanently retained with those results. It will not be retuned and described as having passed those holdouts.

## Phase 5 development data

Phase 5 may use the following as development evidence:

- TCD-VoIP
- NISQA TEST P501
- EARS-EMO-OpenACE
- NISQA TEST_FOR
- TMHINT-QI version II test full-reference subset
- the deterministic engineering matrix

NISQA TEST_FOR and TMHINT ceased to be untouched when their Phase 4 results were observed.

## Primary Phase 5 direction

The primary Phase 5 score is native-only.

The first Phase 5 trainer compares:

- a strongly regularized linear native model
- a strongly regularized degree-two native model

Both must satisfy the same engineering inequalities used for Phase 4:

- high identity quality
- sample-rate identity quality
- pure-delay tolerance
- non-increasing quality under worsening dropout, noise, low-pass restriction, clipping, attenuation, clock drift, time scaling, and mixed impairments

Each subjective domain receives equal total fitting weight.

Model selection maximizes the weakest grouped cross-validated Pearson or Spearman correlation across all five subjective domains. This prevents a strong result on one corpus from hiding collapse on another.

## Validation rule

Phase 5 cannot be validated on TEST_FOR or TMHINT.

A new model ID and a new untouched subjective corpus are required before any Phase 5 generalization claim. The current preferred reserve is the simulated, reference-capable portion of the ICASSP 2026 URGENT Track 1 blind subjective test. The exact pairing and subset protocol must be frozen before any Phase 5 score is computed.
