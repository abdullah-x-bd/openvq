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


## 6.2F observed qualification result

The aligned three-seed Phase 6.2F ensemble passed identity, pure-delay invariance, dropout severity, repeated-dropout severity, noise, low-pass, and mixed-impairment checks. It failed one protected clipping monotonicity relationship. The most severe protected clipping case scored more than 0.12 MOS above the preceding severity level.

No qualified bundle was created. URGENT 2026 remained untouched.

## 6.2G predeclared clipping-property experiment

Phase 6.2G changes only the training objective.

Fixed:

- corrected Trace V2;
- the five development corpora;
- leave-one-corpus-out folds;
- seeds 20260926, 20260927, and 20260928;
- padding-safe learned-bands architecture;
- optimizer and human-MOS objective;
- three-seed ensemble rule;
- protected engineering gate;
- untouched URGENT reserve.

Added:

- three separately generated clipping-property references;
- six training thresholds 0.85, 0.65, 0.45, 0.30, 0.18, and 0.11;
- no overlap with protected clipping thresholds 0.95, 0.50, 0.25, and 0.08;
- pairwise adjacent clipping-order hinge loss;
- raw-quality margin 0.03, equal to 0.12 MOS;
- property-loss weight 0.25;
- one property update contribution every four human training batches.

The property fixtures have no subjective MOS role. Early stopping remains human-only corpus-balanced validation RMSE.

Subjective no-regression guardrails are frozen before the run:

- every held-corpus Pearson and Spearman must stay positive;
- worst held-corpus correlation must remain at least 90% of Phase 6.2E;
- mean held-corpus correlation must remain at least 95% of Phase 6.2E;
- worst normalized RMSE must remain within 105% of Phase 6.2E.

Only after those guardrails pass may the full-development three-seed candidate be trained and tested on the unchanged protected engineering gate.

URGENT 2026 remains untouched.
