# Phase 6 frozen external validation protocol

This protocol is implemented before any Phase 6 candidate is allowed to consume the reserved URGENT 2026 subjective labels.

## Preconditions

A Phase 6 external run requires:

1. a frozen source commit;
2. an immutable model bundle;
3. the SHA-256 of that bundle;
4. a verified full-reference source map for the simulated URGENT utterances;
5. the SHA-256 of that source map;
6. fixed pairing and exclusion rules;
7. fixed statistics and bootstrap unit.

The GitHub workflow has no push trigger and requires an explicit confirmation string.

## Reserve

Subjective source:

`urgent-challenge/urgent2026-sqa`, ACR test split.

Only rows marked `is_simulated=true` are eligible, and only if a separately verified reference map supplies an exact clean reference for the same `utterance_id`.

The SQA release's enhanced audio is **not** treated as self-referencing.

Rows without a verified reference are excluded with a recorded reason.

## Primary metrics

On the OpenVQ 1..5 output and URGENT 1..5 ACR MOS:

- Pearson
- Spearman
- RMSE
- MAE
- signed bias
- near-floor/near-ceiling mass
- per-system and per-language diagnostics
- invalid/excluded coverage

Primary uncertainty uses 10,000 source-cluster bootstrap resamples with the utterance/reference source as the sampling unit.

## Research screen

Historical OpenVQ research screen:

- Pearson >= 0.70
- Spearman >= 0.70
- RMSE <= 0.80 MOS

This is a project screen, not an ITU threshold and not sufficient by itself for a replacement claim.

## POLQA comparison

A direct comparison is performed only when lawful POLQA outputs exist for the **exact same sample IDs and waveforms**.

Define:

`delta_RMSE = RMSE(OpenVQ,human) - RMSE(POLQA,human)`

The historical project non-inferiority margin is +0.10 MOS.

With a source-cluster paired bootstrap:

- non-inferiority requires the upper 95% confidence bound on delta_RMSE to be below +0.10;
- superiority evidence requires that bound to be below 0.

These are Project OpenVQ statistical criteria. They do not establish P.863 conformance.

## Failure rule

If the reserve result changes model architecture, preprocessing, normalization, calibration, or thresholds, the reserve becomes development evidence.

A changed candidate requires a new genuinely reserved evaluation source.

## Claim boundary

No Phase 6 result may be described as POLQA-equivalent, P.863-compliant, or generally superior to POLQA without the corresponding lawful paired evidence and appropriate scope.
