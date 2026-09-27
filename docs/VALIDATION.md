# Validation framework

OpenVQ treats four requirements separately:

1. frontend correctness;
2. engineering sanity;
3. subjective development generalization;
4. untouched external validation.

Success in one class does not imply success in the others.

## Engineering evidence

The engineering suites test controlled transformations including:

- identity;
- pure delay;
- dropout;
- repeated dropout;
- noise;
- low-pass restriction;
- clipping;
- attenuation;
- clock drift;
- time scaling;
- mixed impairments.

Phase 6A froze the frontend only after native tests and real-speech transport-delay checks passed.

Phase 6F then applied a separate learned-model engineering gate. The selected hybrid sequence candidate failed this gate even though ONNX parity passed.

## Development subjective evidence

The current development corpora are:

- TCD;
- NISQA P501;
- NISQA TEST_FOR;
- OpenACE;
- TMHINT-QI original.

Total Phase 6 development rows:

2,463.

## Leave-one-corpus-out evaluation

One entire corpus is excluded from fitting and early stopping.

Phase 6E applies this to all three sequence architectures with three fixed seeds per held corpus.

The architecture selection rule is:

1. maximize weakest held-corpus Pearson/Spearman;
2. maximize mean held-corpus correlation;
3. minimize worst normalized RMSE.

Hybrid won under this rule with worst held-corpus correlation -0.1392.

That is a relative architecture-selection result, not a claim of acceptable generalization.

## Seed stability

Per-seed outcomes remain an explicit diagnostic.

Phase 6E showed large seed variation, including positive and negative transfer on the same held corpus. Ensemble averages are therefore reported together with individual-seed evidence in the artifacts.

## Engineering promotion gate

A full-development learned candidate is not promotable unless it satisfies independent engineering behavior.

The Phase 6.1 hybrid candidate:

- passed pure-delay invariance;
- passed clipping monotonicity;
- passed low-pass monotonicity;
- failed identity;
- failed dropout monotonicity;
- failed repeated-dropout monotonicity;
- failed mixed-impairment monotonicity;
- failed noise monotonicity.

The failed gate blocks product bundling and external-reserve consumption.

## Untouched external evidence

URGENT 2026 subjective labels remain unconsumed.

The external protocol requires a frozen model bundle, verified full-reference pairing, fixed exclusions, fixed metrics, and fixed bootstrap units before labels are used.

## Subjective targets

Human ratings remain the prediction target.

Cross-corpus absolute error is labelled normalized error when MOS and MUSHRA protocols are combined. Normalized error is not described as MOS RMSE.

## Direct POLQA comparison

POLQA is a benchmark only when lawful outputs exist for the exact same audio pairs.

The repository contains a historical locked protocol and a Phase 6 external protocol. Neither establishes P.863 conformance.

OpenACE also contains published per-file POLQA values, but OpenACE is development evidence and cannot serve as untouched Phase 6.1 validation.

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
- engineering failures;
- evidence status and provenance.

Failures remain part of the scientific record.
