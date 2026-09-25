# Reproducibility guide

## Core rule

Every scientific claim should be traceable to:

- a source commit
- a model ID
- a frozen protocol
- a dataset revision or source
- a GitHub Actions run
- a downloadable result artifact

## Frozen Phase 3 model

Model ID:

`phase3-tcd-only-2026-09-24-f099129`

Freeze record:

`validation/frozen/phase3-freeze.json`

The freeze record contains the source commit, artifact identity, coefficients, training rule, and observed TCD/NISQA metrics.

## Main validation workflows

### Engineering matrix

Workflow:
`.github/workflows/validation-engineering.yml`

Purpose:
Deterministic stress tests for timing, dropout, noise, filtering, clipping, gain, drift, time scaling, mixed impairments, bounds, and fuzz cases.

### Phase 3 hybrid

Workflow:
`.github/workflows/validation-visqol-baseline.yml`

Purpose:
Build pinned Google ViSQOL v3.3.3, prepare TCD and NISQA P501, compute expert scores, fit the Phase 3 mapper on TCD train/development only, and evaluate the locked test sets.

### OpenACE external benchmark

Workflow:
`.github/workflows/validation-openace-polqa.yml`

Purpose:
Evaluate the already frozen Phase 3 candidate on EARS-EMO-OpenACE and compare it with published POLQA and ViSQOL against human MUSHRA.

The first OpenACE run exposed a WAV subtype compatibility issue before any OpenVQ result was produced. The compatibility fix converted the source WAV representation to mono PCM16 at the original sample rate. The model and evaluation criterion remained unchanged. This is documented in `validation/OPENACE_PROTOCOL.md`.

### Phase 4 forensics

Workflow:
`.github/workflows/validation-phase4-forensic.yml`

Purpose:
Reuse the already computed OpenACE expert artifact, extract native OpenVQ features, decompose Phase 3 contributions, and measure which feature families retain predictive information.

This is development analysis, not untouched validation.

## Direct POLQA comparison

Protocol:
`validation/LOCKED_POLQA_PROTOCOL.md`

Comparison script:
`validation/locked_compare.py`

Primary statistic:
RMSE to human MOS.

Predeclared practical non-inferiority margin:
+0.10 MOS RMSE.

A formal comparison requires lawful POLQA outputs for the exact same reference/degraded pairs.

## Rules for new model versions

A new model version must receive a new model ID if any of the following changes:

- feature definition
- coefficient
- model architecture
- expert-gating rule
- calibration mapping
- clipping rule
- input normalization that changes numerical features

If an evaluation dataset was inspected during those changes, it cannot remain an untouched holdout for the new version.

## Result reporting

Always report:

- sample count
- Pearson correlation
- Spearman correlation
- RMSE and MAE when prediction and subjective target share a meaningful numerical scale
- signed bias when relevant
- condition-level results where conditions repeat
- confidence intervals for direct paired comparisons
- known failure modes

Do not report only the strongest metric.
