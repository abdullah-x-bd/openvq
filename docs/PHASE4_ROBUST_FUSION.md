# Phase 4 robust native-first fusion

**Status: historical milestone. Phase 4 is frozen and failed its external generalization gate.**

Phase 4 was created after the frozen Phase 3 fusion failed OpenACE.

Its central change was to make native OpenVQ measurements the main score and treat external perceptual experts as optional, fallible evidence.

## Main lessons

1. Native OpenVQ features contained substantial useful codec-quality information.
2. Fixed expert weighting from Phase 3 was fragile.
3. Unconstrained learned mappings could produce physically wrong trends.
4. Explicit engineering inequalities were necessary.
5. Passing engineering tests did not guarantee cross-domain subjective generalization.

## Frozen Phase 4 candidate

`phase4-native-poly2-constrained-2026-09-25-v3`

Frozen source:

`d530382d6161d0a5dc3d019782192a047982f839`

The candidate passed its deterministic engineering suite before external scoring.

## External NISQA TEST_FOR

n = 240:

- Pearson 0.6148
- Spearman 0.5892
- RMSE 0.7503 MOS
- MAE 0.5878 MOS
- bias +0.1005 MOS

Predeclared gate:

- Pearson >= 0.70
- Spearman >= 0.70
- RMSE <= 0.80 MOS

Result:

failed correlation criteria.

## TMHINT historical fallback

A second holdout was used when the public NISQA archive did not expose the documented TEST_NSC folder.

Historical Phase 4 correlation result on 1,455 paired TMHINT files:

- Pearson 0.2116
- Spearman 0.2580

Phase 5.1 later found that the downloaded archive is the original TMHINT-QI release and that the historical workflow incorrectly transformed already-1-to-5 listener scores.

Therefore the correlations remain useful historical diagnostics, while the historical absolute-error values are not corrected metrics.

## Final interpretation

Phase 4 solved an engineering-behavior problem but not the generalization problem.

It is retained for reproducibility and should not be described as a general POLQA replacement.

Phase 5 and Phase 5.1 are the direct consequences of this result.

See:

- `docs/VALIDATION_HISTORY.md`
- `docs/PHASE5_CROSS_DOMAIN.md`
- `docs/PHASE5_1_RESULTS.md`
