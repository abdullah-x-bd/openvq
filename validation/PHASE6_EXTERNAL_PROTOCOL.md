# Phase 6 external validation protocol

## Status

This protocol remains reserved.

The Phase 6.1 hybrid development candidate is **not eligible** to consume the external reserve because it failed the independent engineering promotion gate.

URGENT 2026 subjective labels remain unconsumed.

## Preconditions

An external run requires:

1. a frozen source commit;
2. an immutable model bundle;
3. the bundle SHA-256;
4. a verified full-reference source map;
5. the source-map SHA-256;
6. fixed pairing and exclusion rules;
7. fixed statistics and bootstrap unit;
8. a passed independent engineering promotion gate.

## Reserve

Subjective source:

`urgent-challenge/urgent2026-sqa`, ACR test split.

Only rows marked `is_simulated=true` are eligible, and only when a separately verified source map supplies the exact clean reference for the same utterance.

Enhanced audio is not treated as self-reference.

Rows without verified references are excluded with recorded reasons.

## Metrics

On OpenVQ 1-to-5 output and 1-to-5 human MOS:

- Pearson;
- Spearman;
- RMSE;
- MAE;
- signed bias;
- floor/ceiling behavior;
- per-system and per-language diagnostics;
- invalid/excluded coverage.

Primary uncertainty uses 10,000 source-cluster bootstrap resamples.

## Research screen

Historical project screen:

- Pearson at least 0.70;
- Spearman at least 0.70;
- RMSE at most 0.80 MOS.

This is an OpenVQ research criterion, not an ITU threshold.

## POLQA comparison

A direct comparison is allowed only when lawful POLQA outputs exist for the exact same samples.

Define:

`delta_RMSE = RMSE(OpenVQ,human) - RMSE(POLQA,human)`

Historical project non-inferiority margin:

+0.10 MOS.

With a source-cluster paired bootstrap:

- non-inferiority requires the upper 95 percent bound below +0.10;
- superiority evidence requires the upper 95 percent bound below 0.

These criteria do not establish P.863 conformance.

## Failure rule

If external results influence architecture, frontend, calibration, normalization, or thresholds, the reserve becomes development evidence.

A changed candidate requires genuinely new reserved evidence.
