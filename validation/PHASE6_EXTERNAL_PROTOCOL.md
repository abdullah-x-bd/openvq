# Phase 6 external validation protocol

## Status

This protocol is now the next eligible validation stage.

The Phase 6.2G candidate has passed the model-side engineering and deployment-parity requirements and has an immutable qualified development bundle.

Frozen candidate:

- source commit `9c59fec790e0490c22b363474dd75b476f891f8f`;
- pipeline ID `openvq-phase62g-749eaa80ea0a796cc15c`;
- qualification artifact `10980470659`;
- artifact ZIP SHA-256 `407b04a1130b559ef59d54c63f3d40c02d24fb08c106ef80dc7fdf8f654d645c`.

URGENT 2026 subjective labels remain unconsumed.

The reserve must stay unopened until the remaining external-run inputs, especially the verified full-reference source map, exclusions, and bootstrap unit, are frozen.

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

## Phase 6.2G eligibility record

The following model-side preconditions are complete:

- frozen candidate source commit;
- immutable candidate artifact;
- fixed three-seed ensemble rule;
- passed PyTorch-to-ONNX parity;
- passed independent protected engineering gate;
- frozen development evidence and no-regression results.

The following reserve-side items must be verified and frozen before subjective-label consumption:

- exact full-reference source map;
- source-map SHA-256;
- final inclusion/exclusion ledger;
- fixed statistics implementation;
- fixed source-cluster bootstrap unit.

No candidate tuning is permitted from URGENT results without reclassifying URGENT as development evidence.

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
