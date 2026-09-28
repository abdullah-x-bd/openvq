# Validation framework

OpenVQ treats five requirements separately:

1. frontend correctness;
2. engineering sanity;
3. subjective development generalization;
4. deployment parity and reproducibility;
5. untouched external validation.

Success in one class does not imply success in the others.

## Frontend and trace correctness

Phase 6A froze the native frontend only after Release tests, alignment regressions, and real-speech transport-delay checks passed.

Phase 6.2A-B then corrected the Trace V1 FFT indexing defect and froze:

- trace schema `openvq-trace-v2-2026-09-27`;
- implementation `openvq-trace-spectral-v2-fft-corrected-2026-09-27`.

Trace V2 is covered by FFT-versus-direct-DFT tests, Parseval checks, auditory-band fixtures, and exact recreation of all five development corpora.

## Development subjective evidence

Current development corpora:

- TCD;
- NISQA P501;
- NISQA TEST_FOR;
- OpenACE;
- TMHINT-QI original.

Total development rows: **2,463**.

These corpora are development evidence and are not an untouched external reserve.

## Leave-one-corpus-out evaluation

One entire corpus is excluded from fitting and early stopping.

Three fixed seeds are used:

`20260926`, `20260927`, `20260928`.

The aggregate selection rule remains:

1. maximize weakest held-corpus Pearson/Spearman;
2. maximize mean held-corpus correlation;
3. minimize worst normalized RMSE.

Phase 6.2G final ensembles:

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.6551 | 0.6384 | 0.1943 |
| NISQA TEST_FOR | 0.5640 | 0.4656 | 0.1850 |
| OpenACE | 0.4213 | 0.4659 | 0.2135 |
| TCD | 0.5901 | 0.6129 | 0.2818 |
| TMHINT | 0.3541 | 0.3281 | 0.2919 |

Aggregate:

- worst held-corpus correlation 0.3281;
- mean held-corpus correlation 0.4887;
- worst normalized RMSE 0.2919.

Every held corpus is positively correlated under both Pearson and Spearman.

## Property-constraint separation

Phase 6.2G added a clipping-order property loss only after Phase 6.2F isolated clipping as the remaining protected engineering failure.

The property fixtures are separate from the protected gate.

Training thresholds:

`0.85, 0.65, 0.45, 0.30, 0.18, 0.11`.

Protected gate thresholds:

`0.95, 0.50, 0.25, 0.08`.

The sets are disjoint.

Property fixtures do not supply subjective MOS targets. Human-only corpus-balanced validation RMSE continues to control early stopping.

## Subjective no-regression guardrails

Before Phase 6.2G results, the following limits were frozen:

- every held-corpus Pearson and Spearman must remain positive;
- worst held-corpus correlation must remain at least 90% of Phase 6.2E;
- mean held-corpus correlation must remain at least 95% of Phase 6.2E;
- worst normalized RMSE must remain within 105% of Phase 6.2E.

Phase 6.2G passed all four requirements.

## Engineering promotion gate

A full-development learned candidate is not engineering-qualified unless it satisfies independent physical behavior.

The protected gate checks:

- identity;
- pure delay;
- dropout;
- repeated dropout;
- noise;
- low-pass restriction;
- clipping;
- mixed degradation.

Phase 6.2F passed every protected check except one severe-clipping ordering relation.

Phase 6.2G reused the same protected gate unchanged and passed with zero failures:

- identity 4.6062 MOS;
- pure-delay maximum absolute change 0.00924 MOS;
- zero >0.12 MOS reversals in every protected monotonic family.

## Deployment parity

The final Phase 6.2G candidate is a three-seed ONNX ensemble.

All three models passed PyTorch-to-ONNX parity at the 0.0001 MOS tolerance.

Maximum absolute MOS differences:

- 0.00000119;
- 0.00000095;
- 0.00000167.

## Qualified development bundle

Phase 6.2G created the first immutable engineering-qualified development bundle in this sequence-model line.

- source commit `9c59fec790e0490c22b363474dd75b476f891f8f`;
- pipeline ID `openvq-phase62g-749eaa80ea0a796cc15c`;
- run `36422583627`;
- qualification artifact `10980470659`;
- artifact ZIP SHA-256 `407b04a1130b559ef59d54c63f3d40c02d24fb08c106ef80dc7fdf8f654d645c`.

Engineering qualification does not equal external validation.

## Untouched external evidence

URGENT 2026 subjective labels remain unconsumed.

The external protocol requires the exact Phase 6.2G bundle to remain frozen while the full-reference source map, exclusions, metrics, and source-cluster bootstrap unit are finalized.

If external results influence the model, the reserve becomes development evidence.

## Subjective targets

Human ratings remain the prediction target.

Cross-corpus absolute error is labelled normalized error when MOS and MUSHRA protocols are combined. Normalized error is not described as MOS RMSE.

## Direct POLQA comparison

POLQA is an external benchmark only when lawful outputs exist for the exact same audio pairs.

A direct comparison requires:

- the same reference/degraded samples;
- the same human targets;
- paired error statistics;
- a predeclared protocol.

OpenACE contains historical per-file POLQA values, but OpenACE is development evidence.

No Phase 6.2 result establishes P.863 conformance or general POLQA equivalence.

## Reporting rule

Relevant reports include:

- sample count;
- Pearson;
- Spearman;
- valid RMSE/MAE scale;
- signed bias;
- saturation;
- held-corpus results;
- seed results;
- parity;
- engineering outcomes;
- evidence status;
- provenance.

Failures remain part of the scientific record.
