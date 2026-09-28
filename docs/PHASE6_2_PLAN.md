# Phase 6.2 execution plan

## Objective

Phase 6.2 establishes a mathematically verified local trace and measures its effect before changing the learning procedure.

## 6.2A trace correctness

- preserve all Phase 6.1 artifacts;
- record the Trace V1 erratum;
- correct the trace FFT;
- add FFT/DFT oracle tests;
- add Parseval and auditory-band fixtures;
- keep the Phase 6A frontend frozen.

## 6.2B Trace V2

- schema `openvq-trace-v2-2026-09-27`;
- implementation ID `openvq-trace-spectral-v2-fft-corrected-2026-09-27`;
- regenerate all 2,463 development traces;
- regenerate learned-model engineering traces;
- reject old schema/implementation combinations;
- freeze new trace provenance after correctness tests pass.

## 6.2C corrected-trace baseline

Run exactly 45 seeded fits:

- 3 architectures;
- 5 completely held corpora;
- 3 fixed seeds.

Keep fixed:

- data and source groups;
- model architectures;
- optimizer;
- loss;
- hyperparameters;
- early stopping;
- maximum epochs;
- ensemble aggregation;
- architecture selection rule.

Only the trace changes.

## 6.2D training-contract diagnostics

The corrected-trace baseline is complete.

The next controlled experiments are:

- D1: measure batch/padding-context invariance without changing training;
- D2: test fold-fitted global-feature z-score normalization in hybrid only.

If D1 fails, a padding-safe temporal-normalization change is evaluated as its own ablation before property losses.

If D2 does not recover hybrid, learned_bands remains the preferred representation for subsequent training work.

## 6.2E padding-safe learned-bands

D1 confirmed a small but real padding-context defect.

Phase 6.2E therefore changes only the current winning learned-bands architecture:

- mask padded frames after every spectral-encoder convolution;
- mask padded frames after every TCN stage;
- replace BatchNorm1d with per-frame channel LayerNorm;
- require same-utterance batch-context invariance within 0.0001 MOS;
- rerun the same five held corpora and three seeds.

No property loss is introduced until this ablation is recorded.

## 6.2E result

Phase 6.2E is complete.

The padding-safe learned-bands architecture passed the padding-invariance gate and improved the frozen cross-domain objective to:

- worst held-corpus correlation 0.1900;
- mean held-corpus correlation 0.4551;
- worst normalized RMSE 0.3062.

All five held corpora have positive ensemble Pearson and Spearman correlation.

## 6.2F aligned engineering qualification

The qualification candidate must match the evaluation model family and ensemble rule.

Phase 6.2F therefore:

- fits the padding-safe learned-bands model on all development evidence for seeds 20260926, 20260927, and 20260928;
- exports all three models to ONNX;
- checks PyTorch-to-ONNX parity for all three;
- averages raw quality predictions across the three ONNX models;
- applies the independent engineering promotion gate to that ensemble;
- creates an immutable candidate bundle only if the gate passes.

If the engineering gate fails, the next controlled experiment introduces scoped identity, delay, and severity property losses while keeping Trace V2, development data, held-corpus folds, and the padding-safe architecture fixed.

URGENT 2026 remains untouched until an aligned candidate passes the engineering gate.
