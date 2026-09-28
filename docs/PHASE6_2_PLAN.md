# Phase 6.2 execution record

## Status

Phase 6.2 is complete through **Phase 6.2G**.

The outcome is an engineering-qualified three-seed development bundle based on corrected Trace V2 and the padding-safe learned-bands architecture with a narrowly scoped clipping-order property constraint.

The candidate has **not** consumed the URGENT 2026 subjective reserve and has **not** been promoted into the stable CLI or Android MOS path.

## Objective

Phase 6.2 had two objectives:

1. replace the defective Trace V1 local spectral representation with a mathematically verified Trace V2;
2. obtain a cross-domain sequence candidate that also passes independent engineering behavior before external validation.

Both development-stage objectives were achieved.

## 6.2A trace correctness

Completed.

- preserved Phase 6.1 artifacts as historical evidence;
- recorded the Trace V1 FFT indexing erratum;
- corrected the trace-only FFT butterfly indexing;
- added FFT versus direct-DFT oracle tests;
- added Parseval and auditory-band fixtures;
- kept the Phase 6A frontend frozen.

## 6.2B Trace V2

Completed.

- schema `openvq-trace-v2-2026-09-27`;
- implementation ID `openvq-trace-spectral-v2-fft-corrected-2026-09-27`;
- regenerated all 2,463 development traces;
- regenerated learned-model engineering traces;
- rejected stale schema/implementation combinations;
- froze trace provenance after correctness tests.

Canonical run `36306154897`.

## 6.2C corrected-trace baseline

Completed.

The original 45-fit Phase 6E grid was rerun with only the trace corrected:

- 3 architectures;
- 5 completely held corpora;
- 3 fixed seeds.

Data, groups, optimizer, loss, early stopping, epoch ceiling, ensemble aggregation, and selection rule remained fixed.

Corrected `learned_bands` became the preferred architecture:

- worst held-corpus correlation 0.0894;
- mean held-corpus correlation 0.4317;
- worst normalized RMSE 0.3487.

The corrected hybrid collapse showed that the Trace V1 result had materially distorted architecture conclusions.

## 6.2D training-contract diagnostics

Completed.

D1 found a real but small padding-context dependency.

D2 found that rich-v3 global feature standard deviations span roughly 95.6 million to 1. Fold-fitted z-score normalization rescued hybrid substantially but left OpenACE negative.

Result: corrected `learned_bands` remained the preferred representation.

## 6.2E padding-safe learned-bands

Completed.

Changes were limited to temporal padding and normalization:

- mask padded frames after each spectral-encoder convolution;
- mask padded frames after each TCN stage;
- replace BatchNorm1d with per-frame channel LayerNorm.

Padding invariance passed with maximum absolute MOS delta 0.0000004768 at a 0.0001 MOS tolerance.

Three-seed held-corpus objective:

- worst held-corpus correlation 0.1900;
- mean held-corpus correlation 0.4551;
- worst normalized RMSE 0.3062.

All five held corpora had positive ensemble Pearson and Spearman correlation.

Canonical run `36330893596`.

## 6.2F aligned engineering qualification

Completed with a controlled failure.

The qualification candidate matched the evaluation deployment shape:

- seeds 20260926, 20260927, and 20260928;
- full-development fit for each seed;
- one ONNX model per seed;
- arithmetic mean of raw quality predictions;
- PyTorch-to-ONNX parity per seed;
- unchanged protected engineering gate.

Observed:

- identity 4.4483 MOS, pass;
- pure-delay maximum absolute change 0.0389 MOS, pass;
- dropout pass;
- repeated dropout pass;
- noise pass under the frozen 0.12 MOS reversal criterion;
- low-pass pass;
- mixed impairment pass;
- clipping fail with one >0.12 MOS reversal.

No qualified bundle was created.

Canonical run `36397704754`.

URGENT remained untouched.

## 6.2G clipping-order property experiment

Completed successfully.

### Frozen elements

Phase 6.2G kept fixed:

- Phase 6A frontend;
- corrected Trace V2;
- five development corpora;
- leave-one-corpus-out folds;
- seeds 20260926, 20260927, and 20260928;
- padding-safe learned-bands architecture;
- optimizer and human-MOS objective;
- three-seed ensemble rule;
- protected engineering gate;
- URGENT external reserve.

### Added property constraint

Training added only a clipping-order hinge term.

Separate property fixtures used:

- 3 independently generated references;
- thresholds 0.85, 0.65, 0.45, 0.30, 0.18, and 0.11;
- 18 total fixture traces.

Protected gate thresholds remained:

- 0.95, 0.50, 0.25, and 0.08.

The training and protected threshold sets are disjoint.

Property configuration:

- adjacent clipping-order hinge loss;
- raw-quality margin 0.03, equal to 0.12 MOS;
- property-loss weight 0.25;
- one property contribution every four human training batches;
- human-only corpus-balanced validation RMSE for early stopping.

### Predeclared no-regression guardrails

Before results, Phase 6.2G required:

- positive Pearson and Spearman on every held corpus;
- worst held-corpus correlation at least 90% of Phase 6.2E;
- mean held-corpus correlation at least 95% of Phase 6.2E;
- worst normalized RMSE no more than 105% of Phase 6.2E.

All guardrails passed.

Observed aggregate objective:

- worst held-corpus correlation 0.3281;
- mean held-corpus correlation 0.4887;
- worst normalized RMSE 0.2919.

### Final held-corpus results

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.6551 | 0.6384 | 0.1943 |
| NISQA TEST_FOR | 0.5640 | 0.4656 | 0.1850 |
| OpenACE | 0.4213 | 0.4659 | 0.2135 |
| TCD | 0.5901 | 0.6129 | 0.2818 |
| TMHINT | 0.3541 | 0.3281 | 0.2919 |

### Final engineering qualification

The unchanged protected gate passed with zero failures.

- identity 4.6062 MOS;
- pure-delay maximum absolute change 0.00924 MOS;
- clipping 0 reversals;
- dropout 0 reversals;
- repeated dropout 0 reversals;
- noise 0 reversals;
- low-pass 0 reversals;
- mixed impairment 0 reversals.

Protected clipping sequence:

| Threshold | MOS |
| --- | ---: |
| 0.95 | 4.4760 |
| 0.50 | 2.0543 |
| 0.25 | 1.7905 |
| 0.08 | 1.5014 |

### Deployment parity

All three ONNX models passed the 0.0001 MOS parity tolerance.

Maximum absolute MOS differences:

- seed 20260926: 0.00000119;
- seed 20260927: 0.00000095;
- seed 20260928: 0.00000167.

### Qualified development bundle

- source commit `9c59fec790e0490c22b363474dd75b476f891f8f`;
- pipeline ID `openvq-phase62g-749eaa80ea0a796cc15c`;
- canonical workflow run `36422583627`;
- constraint artifact `10969564021`;
- held-corpus artifact `10975650939`;
- qualification artifact `10980470659`;
- qualification artifact ZIP SHA-256 `407b04a1130b559ef59d54c63f3d40c02d24fb08c106ef80dc7fdf8f654d645c`.

## Phase 6.2 conclusion

Phase 6.2 produced the first OpenVQ learned candidate in this line of work that simultaneously:

- uses the corrected local spectral representation;
- remains positively correlated on all five completely held-out development corpora;
- passes predeclared subjective no-regression guardrails;
- passes PyTorch-to-ONNX parity;
- passes the unchanged independent engineering gate;
- has an immutable qualified development bundle.

This is a development milestone, not external validation.

## Next stage

Phase 6.3 should keep the exact Phase 6.2G bundle frozen.

Before subjective reserve consumption:

1. verify the URGENT 2026 full-reference source map;
2. freeze pairing and exclusion rules;
3. freeze the statistical and source-cluster bootstrap protocol;
4. record all required provenance.

Then consume the URGENT reserve once.

If external results influence the model, URGENT becomes development evidence and any changed candidate requires genuinely new reserved evidence.
