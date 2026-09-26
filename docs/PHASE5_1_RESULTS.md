# Phase 5.1 final results

Phase 5.1 is the measurement and validation repair milestone that follows the Phase 5 v1 cross-domain experiment.

It is complete as a research and validation milestone. It is **not** a claim that OpenVQ has reached POLQA parity, and it did not promote a new product MOS model into the native runtime.

## Why Phase 5.1 existed

Phase 5 v1 showed that simply refitting the existing 19 native features across more corpora did not solve generalization. An independent audit then found two additional problems that made a clean Phase 6 experiment impossible:

1. an intended independent pure-delay assertion in the engineering validation source had been disabled by a literal escaped-newline/comment defect;
2. the TMHINT material had been identified as version II and its listener scores were transformed from 0..5 to 1..5, but the downloaded archive is the original TMHINT-QI release and its observed quality ratings are already on a 1..5 scale.

Phase 5.1 therefore repaired the evidence chain, preprocessing, alignment, representation, and evaluation protocol before any neural Phase 6 work.

## 5.1A Evidence correction

Completed:

- restored the independent pure-delay validation assertion;
- detected the TMHINT release from the archive contents rather than from an assumed label;
- identified the downloaded corpus as `TMHINT_QI_ORIGINAL`;
- detected an observed score range of 1.0 to 5.0 and stopped applying the historical affine score transform;
- recorded archive, raw-metadata, manifest, feature-schema, evaluator, and source hashes;
- retained the earlier results as historical records instead of silently rewriting them.

TMHINT provenance from the final run:

- test WAVs: 2,297
- deterministic non-clean full-reference pairs: 1,455
- unresolved non-clean files: 331
- unique reference IDs: 192
- archive SHA-256: `cda6581c9fb0ea634b8bac4c6503e772feb080629a5d95eb84f3d1888876912b`
- raw metadata SHA-256: `832ac3fdaf393e77f62edb096770f8ade9f52fbb574e9bebcab0bf9ba02732a5`
- manifest SHA-256: `8af544f59d9f192d51ebc6837e5c50022576e0c5534618e36405ab4334835072`

### Consequence for older TMHINT results

The old TMHINT Pearson and Spearman values remain numerically meaningful because the mistaken label transform was positive and affine, so it did not change correlation or rank correlation.

The old TMHINT RMSE, MAE, and bias are **not corrected metrics** and should not be used as evidence.

Phase 5 v1 was also fitted using the transformed TMHINT target. It remains useful as a diagnostic historical experiment, but it is not a clean release candidate.

## 5.1B Shared preprocessing

The native analyzer now uses one shared preprocessing path for base and advanced analysis:

- one windowed-sinc resampler;
- one DC-removal path;
- one prepared reference/degraded pair;
- the same prepared buffers for base and advanced feature extraction.

A dedicated preprocessing test target is built by both desktop CMake and the Android native build.

## 5.1C Shared alignment, coverage, and active level

The repaired analyzer adds:

- a piecewise-continuous local alignment map;
- bounded local path movement so alignment cannot freely jump across missing speech;
- common alignment use across multi-resolution, envelope, and residual features;
- explicit active-reference coverage;
- explicit lost-active-speech fraction;
- matched active-speech level measurement;
- alignment coverage and confidence;
- out-of-range active speech counted as missing instead of silently skipped.

The central design rule is that alignment may correct nuisance timing, but it may not erase a real speech loss.

## 5.1D Rich representation

Phase 5.1 preserves the old `legacy19` representation and introduces `rich-v2`.

`rich-v2` contains the 19 legacy features plus:

- lost active speech;
- active coverage;
- alignment uncertainty;
- raw active-level delta;
- 10th-percentile similarity loss;
- median similarity loss;
- 90th-percentile discontinuity;
- longest bad interval;
- severe-frame fraction;
- absolute clock drift;
- raw clipping ratio;
- confidence deficit.

The exported rich model uses 31 features in total.

## 5.1E Evaluation repair

Phase 5.1 no longer treats one grouped cross-validation number as sufficient evidence.

It evaluates:

- grouped within-corpus transfer;
- leave-one-corpus-out transfer with the held corpus excluded from inner model selection;
- processing-family transfer;
- synthetic engineering monotonicity;
- a real-speech engineering suite;
- floor and ceiling saturation;
- normalized absolute error across corpora with different subjective protocols.

All five subjective corpora are development evidence in Phase 5.1:

- TCD-VoIP: 384
- NISQA TEST P501: 240
- NISQA TEST_FOR: 240
- OpenACE: 144
- TMHINT-QI original paired subset: 1,455

URGENT 2026 was not consumed and remains available as a future untouched validation source.

## 5.1F Fixed-evidence ablations

Three model families were evaluated on the same repaired evidence.

| Model | Worst correlation | Mean correlation | Worst normalized RMSE |
| --- | ---: | ---: | ---: |
| repaired frontend + legacy19 constrained poly2 | 0.3897 | 0.6257 | 0.2052 |
| repaired frontend + rich-v2 constrained poly2 | 0.4337 | 0.6370 | 0.1977 |
| repaired frontend + rich-v2 small MLP diagnostic | 0.5304 | 0.6772 | 0.1914 |

The richer representation therefore improved the constrained native model.

The small MLP improved the fixed-evidence development results more substantially, which is evidence that nonlinear representation learning is worth testing in Phase 6. It is diagnostic only and is not a product scorer.

### Diagnostic MLP grouped results

The diagnostic network used hidden layers `[48, 24]` and regularization `alpha = 0.1`.

| Corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.7229 | 0.7146 | 0.1790 |
| NISQA TEST_FOR | 0.5854 | 0.5649 | 0.1914 |
| OpenACE | 0.7810 | 0.7589 | 0.1487 |
| TCD | 0.7779 | 0.7813 | 0.1568 |
| TMHINT | 0.5549 | 0.5304 | 0.1803 |

These are development cross-validation results, not untouched external validation.

## Most important finding: leave-corpus-out transfer is still poor

The selected constrained `rich-v2` model was retrained while excluding one complete corpus at a time.

| Held-out corpus | Pearson | Spearman | normalized RMSE | floor fraction |
| --- | ---: | ---: | ---: | ---: |
| NISQA P501 | 0.6656 | 0.6547 | 0.1905 | 0.004 |
| NISQA TEST_FOR | 0.5296 | 0.5175 | 0.2229 | 0.042 |
| OpenACE | -0.4904 | -0.4114 | 0.3760 | 0.042 |
| TCD | 0.3893 | 0.4438 | 0.2350 | 0.000 |
| TMHINT | -0.0269 | 0.0590 | 0.5047 | 0.774 |

This is the key scientific result of Phase 5.1.

The richer measurements help when the model has seen examples from a domain, but the current hand-engineered representation plus constrained quadratic mapper still does not learn a corpus-invariant notion of perceptual quality.

The TMHINT held-out result is especially revealing: 77.4 percent of predictions hit the floor.

Therefore Phase 5.1 does **not** justify promoting the exported constrained model as the next production MOS scorer.

## Processing-family transfer

Processing-family transfer also remains uneven.

Examples from the selected rich constrained model:

- NISQA P501 fold worst correlation: 0.4067
- NISQA TEST_FOR fold worst correlation: 0.4066
- TCD family worst correlation: 0.4232
- OpenACE codec worst correlation: -0.0310
- TMHINT family worst correlation: 0.1235

The weakest OpenACE family was Opus. The weakest TMHINT family was unenhanced noisy speech.

This reinforces the leave-corpus-out conclusion: the remaining problem is not merely calibration. The representation/model must become more robust to unseen processing families and domains.

## Engineering validation

The repaired synthetic engineering suite completed with no failures and produced 151 feature rows.

The independent real-speech suite used six TCD reference utterances and predeclared:

- identity MOS >= 4.4;
- absolute pure-delay MOS change <= 0.2;
- worsening-severity Spearman <= -0.2.

The final real-speech run reported no failures.

The selected constrained rich export also reported no engineering failures.

This means Phase 5.1 repaired engineering correctness without solving statistical cross-domain generalization. Those are separate properties and both are now measured explicitly.

## Exported constrained model

For reproducibility, Phase 5.1 exports:

- model ID: `phase5.1-native-repaired-2026-09-26-v1`
- feature schema: `rich_v2`
- basis: degree-two polynomial
- alpha: 3.0
- exact feature order
- normalization mean and scale
- coefficients
- a generated C++ include artifact
- a standalone Python predictor

The export is a reproducible research artifact. It was **not promoted into the main native runtime**, because the same Phase 5.1 evaluation demonstrates that its unseen-corpus transfer is not strong enough.

That is an intentional scientific decision, not an unfinished build step.

## Reproducibility record

Final Phase 5.1 source commit:

`4f96463411da8f9f6aecb370e8ac69ae2c228273`

Pull request:

`#12 Phase 5.1: measurement and validation repair`

Final full workflow:

`validation-phase51`

GitHub Actions run:

`36219037262`

Result:

`success`

Artifact:

`openvq-phase51`

Artifact ID:

`10899193034`

Artifact SHA-256:

`7e1e244074520e3e9e620fc29a602b99b094c6592a4bb954407b3e98b4949426`

The artifact contains the complete report, exported model, synthetic and real engineering reports, manifests, feature tables, provenance, and dataset revision information.

## What Phase 5.1 proved

Phase 5.1 established that:

1. the evidence chain can be reproduced and audited;
2. the frontend and alignment path had real defects or ambiguities worth repairing;
3. richer temporal, coverage, alignment, and saturation features improve the known-domain model;
4. a small neural model can use those measurements better than the constrained quadratic mapper on the five known development corpora;
5. engineering sanity and statistical generalization must be validated separately;
6. the current feature/mapping family still fails true unseen-corpus transfer;
7. the next phase should focus on learned representation/generalization rather than another round of coefficient tuning.

## Handoff to Phase 6

Phase 6 should start from the repaired Phase 5.1 frontend and evidence chain.

It should not start by changing the holdout or weakening thresholds.

The recommended direction is to investigate a compact ANN or similarly regularized learned mapper/representation while:

- preserving the repaired shared preprocessing and alignment;
- retaining rich-v2 measurements as interpretable inputs or auxiliary features;
- keeping the deterministic engineering gates;
- using corpus-aware and processing-family-aware validation during development;
- keeping the chosen URGENT 2026 subset untouched until the Phase 6 candidate and protocol are frozen.

A direct POLQA comparison remains a separate later gate using lawful POLQA scores on the exact same audio pairs.
