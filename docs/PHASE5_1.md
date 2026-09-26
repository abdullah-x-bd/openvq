# Phase 5.1 measurement and validation repair

**Status: complete as a measurement, evidence, and validation milestone.**

Phase 5.1 is not a POLQA-parity claim and is not a production MOS release.

The final results and interpretation are in [Phase 5.1 final results](PHASE5_1_RESULTS.md).

## Why Phase 5.1 was necessary

Phase 5 v1 showed that retraining the original 19 native features across five corpora still left poor cross-domain performance. Before moving to a neural Phase 6 model, an audit identified problems in both the evidence chain and the native measurement path.

Phase 5.1 therefore repaired the measurement and validation substrate first.

## 5.1A Evidence correction

Completed:

- restored an independent pure-delay engineering assertion that had been disabled by an escaped-newline/comment defect;
- detected TMHINT release identity from archive contents;
- corrected TMHINT score handling to the observed 1-to-5 scale;
- recorded archive, raw metadata, manifest, feature, schema, evaluator, and source hashes;
- retained historical results with an explicit erratum rather than rewriting them.

See [Phase 5.1 evidence erratum](PHASE5_1_EVIDENCE_ERRATUM.md).

## 5.1B Shared preprocessing

Completed:

- one windowed-sinc resampler;
- one DC-removal path;
- one prepared reference/degraded pair shared by base and advanced analysis;
- dedicated preprocessing tests;
- the same preprocessing source compiled into the Android native library.

## 5.1C Shared alignment, coverage, and active level

Completed:

- piecewise-continuous alignment map with bounded local movement;
- global delay and clock-drift metadata;
- common alignment use across multi-resolution, envelope, and residual features;
- explicit active-reference coverage;
- explicit lost-active-speech fraction;
- matched active-speech level measurement;
- alignment coverage and confidence;
- missing out-of-range active speech counted as missing rather than silently skipped.

Alignment is treated as nuisance correction, not permission to hide a missing word.

## 5.1D Rich representation

Two schemas are retained side by side.

### legacy19

The exact 19 utterance summaries used by Phase 5 v1.

### rich-v2

The 19 legacy features plus:

- lost active speech;
- active coverage;
- alignment uncertainty;
- raw matched active-level delta;
- 10th and 50th percentile similarity loss;
- 90th percentile discontinuity;
- longest bad interval;
- severe-frame fraction;
- absolute clock drift;
- raw clipping ratio;
- confidence deficit.

The rich-v2 schema contains 31 features.

## 5.1E Evaluation repair

Completed evaluation axes:

- grouped within-corpus transfer;
- nested leave-corpus-out transfer;
- processing-family transfer;
- synthetic engineering validation;
- independent real-speech engineering validation;
- saturation reporting;
- normalized absolute error for mixed subjective protocols.

The held corpus is excluded from inner model selection in leave-corpus-out evaluation.

URGENT 2026 was not consumed.

## 5.1F Fixed-evidence ablations

On identical repaired evidence:

1. legacy19 + constrained linear/quadratic mapper;
2. rich-v2 + constrained linear/quadratic mapper;
3. rich-v2 + small MLP diagnostic.

Summary:

- legacy19 constrained worst correlation: 0.3897
- rich-v2 constrained worst correlation: 0.4337
- rich-v2 MLP diagnostic worst correlation: 0.5304

The MLP result is evidence for the Phase 6 direction. It is not an exported product scorer.

The constrained rich-v2 export is retained for reproducibility, but it was deliberately not promoted into the native product path after leave-corpus-out evaluation showed severe unseen-domain failures.

## Completion criterion

Phase 5.1 is considered complete because its purpose was to repair and audit the measurement/validation foundation and determine whether that foundation was ready for Phase 6.

The final answer is:

- measurement/evidence repair: complete;
- engineering validation: passes;
- richer representation: useful;
- fixed-evidence neural diagnostic: promising;
- cross-corpus generalization: still insufficient;
- product promotion of the Phase 5.1 mapper: intentionally withheld;
- next research milestone: Phase 6.

This supersedes the earlier draft wording that required promoting the constrained Phase 5.1 mapper into production before Phase 5.1 could close. The completed Phase 5.1 evidence shows that such a promotion would be scientifically unjustified.

## Canonical run

- source commit: `4f96463411da8f9f6aecb370e8ac69ae2c228273`
- PR: `#12`
- workflow: `validation-phase51`
- run: `36219037262`
- conclusion: `success`
- artifact ID: `10899193034`
- artifact SHA-256: `7e1e244074520e3e9e620fc29a602b99b094c6592a4bb954407b3e98b4949426`

See [Phase 5.1 final results](PHASE5_1_RESULTS.md) for the complete evidence.
