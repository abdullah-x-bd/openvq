# Validation history

This document is the chronological scientific record of OpenVQ.

Failures are retained. Once a holdout has been inspected and influences later design, it is reclassified as development evidence and is not reused as untouched proof for a new model.

## Phase 1: native engine

Phase 1 established the independent C++ full-reference engine, Android integration, deterministic impairment tests, timing analysis, perceptual spectral comparison, and initial telecom diagnostics.

The initial score weights were engineering bootstrap values.

No POLQA-parity claim was made.

## Phase 2: telecom diagnostics

Early human-MOS and deterministic testing exposed under-treatment of several audible failure modes.

Phase 2 added or strengthened:

- delayed-copy echo analysis;
- choppiness and local temporal edits;
- residual intrusion;
- clipping;
- silence-region diagnostics;
- codec and network laboratories;
- NISQA TEST P501 evaluation.

The main lesson was that useful speech-quality measurement needs both spectral and temporal/network evidence.

## Phase 3: expert fusion

Phase 3 tested whether optional external perceptual experts could improve mapping to human quality.

Google ViSQOL v3.3.3 was pinned and run independently in speech and audio modes. A monotonic mapper was fitted using TCD train/development evidence.

Frozen model:

`phase3-tcd-only-2026-09-24-f099129`

### Frozen TCD held-out test

Utterance level, n = 60:

- Pearson 0.9541
- Spearman 0.9375
- RMSE 0.4335 MOS
- MAE 0.3665 MOS
- bias +0.2830 MOS

Condition level, n = 15:

- Pearson 0.9800
- Spearman 0.9571
- RMSE 0.3844 MOS

### NISQA TEST P501 external holdout

Utterance level, n = 240:

- Pearson 0.8185
- Spearman 0.8209
- RMSE 0.6011 MOS
- MAE 0.4904 MOS
- bias +0.1348 MOS

Condition level, n = 60:

- Pearson 0.8721
- Spearman 0.8725
- RMSE 0.5003 MOS

These results were strong but did not establish POLQA parity.

## Phase 3 external failure: OpenACE

EARS-EMO-OpenACE was introduced after Phase 3 was frozen.

The benchmark contains 144 codec-processed samples across EVS, LC3, LC3Plus, and Opus with human MUSHRA ratings and published POLQA for 143 samples.

Association with human MUSHRA:

| System | Pearson | Spearman |
| --- | ---: | ---: |
| frozen Phase 3 OpenVQ | 0.1607 | 0.1465 |
| published POLQA | 0.7939 | 0.7818 |
| published OpenACE ViSQOL | 0.7034 | 0.6631 |
| recomputed ViSQOL speech | 0.3305 | 0.3129 |
| recomputed ViSQOL audio | 0.6644 | 0.6254 |

The failure analysis showed that Phase 3 had learned to trust speech-mode ViSQOL heavily because it was useful on TCD/NISQA. That expert generalized poorly to OpenACE, and the frozen fusion followed it.

The lesson was that fixed expert trust is fragile across domains.

OpenACE became development evidence after this result.

## Phase 4: native-first constrained model

Phase 4 moved the main score back to native OpenVQ measurements.

Forensic development work showed that native features contained substantial codec-quality signal when modeled directly. Phase 4 then fitted a constrained degree-two native model and kept external expert influence optional and capped.

Early Phase 4 candidates produced physically wrong behavior such as quality increasing under worsening noise or stronger low-pass restriction. The final Phase 4 family therefore added explicit engineering inequalities.

Frozen candidate:

`phase4-native-poly2-constrained-2026-09-25-v3`

The frozen candidate passed the deterministic engineering suite.

### Phase 4 untouched NISQA TEST_FOR

n = 240:

- Pearson 0.6148
- Spearman 0.5892
- RMSE 0.7503 MOS
- MAE 0.5878 MOS
- bias +0.1005 MOS

Predeclared gate:

- Pearson >= 0.70
- Spearman >= 0.70
- RMSE <= 0.80 MOS

RMSE passed. Pearson and Spearman failed.

Run: `36208421278`

Artifact ID: `10894988692`

### Phase 4 TMHINT fallback holdout

A second holdout was frozen after the public NISQA archive failed to expose the documented TEST_NSC directory.

The historical Phase 4 TMHINT result on 1,455 paired files was:

- Pearson 0.2116
- Spearman 0.2580

Phase 5.1 later established that this archive is the original TMHINT-QI release, not the assumed version-II set, and that listener scores were already on a 1-to-5 scale.

Therefore:

- the historical Pearson/Spearman remain useful because the mistaken target mapping was positive affine;
- the historical Phase 4 TMHINT RMSE, MAE, and bias are not corrected metrics and are not repeated here.

Run: `36208883292`

Artifact ID: `10894734342`

Phase 4 was therefore an engineering-valid but scientifically failed generalization candidate.

## Phase 5 v1: five-domain cross-domain fitting

Phase 5 v1 asked whether the existing 19 native features could be made robust simply by fitting across more known domains with equal corpus weighting and worst-domain model selection.

Development corpora:

- TCD
- NISQA P501
- NISQA TEST_FOR
- OpenACE
- TMHINT

Selected model:

`phase5-native-crossdomain-2026-09-26-v1`

Basis: degree-two polynomial

Alpha: 10

Grouped development results:

| Corpus | Pearson | Spearman |
| --- | ---: | ---: |
| NISQA P501 | 0.6800 | 0.6812 |
| NISQA TEST_FOR | 0.5921 | 0.5715 |
| OpenACE | 0.7505 | 0.7838 |
| TCD | 0.6674 | 0.6748 |
| TMHINT | 0.3608 | 0.3510 |

Worst correlation: 0.3510.

This showed that broader refitting helped but did not solve the representation/generalization problem.

Phase 5.1 later found that Phase 5 v1 had also been fitted using the incorrectly transformed TMHINT target. It is retained as a diagnostic historical baseline, not a clean release candidate.

## Phase 5.1A: evidence correction

The audit found two important evidence defects.

### Independent delay gate

A literal escaped-newline sequence inside a Python comment had caused the intended independent pure-delay assertion in the historical engineering validator not to execute.

Historical green runs therefore cannot be cited as proof that this independent assertion was exercised.

Phase 5.1 restored the assertion and reran it.

### TMHINT identity and scale

Archive inspection detected:

- release: `TMHINT_QI_ORIGINAL`
- listener scale: 1 to 5
- paired non-clean full-reference files: 1,455
- unique reference IDs: 192

Phase 5.1 stopped applying the historical target transform and recorded full provenance hashes.

See `docs/PHASE5_1_EVIDENCE_ERRATUM.md`.

## Phase 5.1B-C: preprocessing and alignment repair

The native analyzer was changed to share one preprocessing path between base and advanced analysis:

- shared windowed-sinc resampler;
- shared DC removal;
- shared prepared buffers.

Alignment was reworked around a bounded piecewise-continuous map.

New explicit measurements include:

- active-reference coverage;
- lost active speech;
- alignment coverage;
- alignment confidence;
- matched active-speech levels.

Out-of-range active speech is treated as missing instead of silently disappearing from feature calculations.

## Phase 5.1D: rich-v2 representation

The old `legacy19` feature schema was retained for exact ablation.

The new `rich-v2` schema adds 12 features:

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

Total features: 31.

## Phase 5.1E: evaluation repair

The Phase 5.1 evaluator reports:

- grouped within-corpus transfer;
- nested leave-one-corpus-out transfer;
- processing-family transfer;
- synthetic engineering validation;
- real-speech engineering validation;
- floor/ceiling saturation;
- normalized absolute error across heterogeneous subjective protocols.

An entire held corpus is excluded from inner selection during leave-corpus-out evaluation.

URGENT 2026 remains untouched.

## Phase 5.1F: fixed-evidence ablations

All models were compared on the same repaired data.

| Model | Worst correlation | Mean correlation | Worst normalized RMSE |
| --- | ---: | ---: | ---: |
| legacy19 constrained poly2 | 0.3897 | 0.6257 | 0.2052 |
| rich-v2 constrained poly2 | 0.4337 | 0.6370 | 0.1977 |
| rich-v2 MLP diagnostic | 0.5304 | 0.6772 | 0.1914 |

The rich feature set improved the constrained model.

The diagnostic MLP improved the five-domain development result further.

### Diagnostic MLP by corpus

| Corpus | Pearson | Spearman |
| --- | ---: | ---: |
| NISQA P501 | 0.7229 | 0.7146 |
| NISQA TEST_FOR | 0.5854 | 0.5649 |
| OpenACE | 0.7810 | 0.7589 |
| TCD | 0.7779 | 0.7813 |
| TMHINT | 0.5549 | 0.5304 |

These are development results only.

## Phase 5.1 decisive result: leave-corpus-out failure

The selected constrained rich-v2 model was also tested by holding out one complete corpus.

| Held corpus | Pearson | Spearman | normalized RMSE | floor fraction |
| --- | ---: | ---: | ---: | ---: |
| NISQA P501 | 0.6656 | 0.6547 | 0.1905 | 0.004 |
| NISQA TEST_FOR | 0.5296 | 0.5175 | 0.2229 | 0.042 |
| OpenACE | -0.4904 | -0.4114 | 0.3760 | 0.042 |
| TCD | 0.3893 | 0.4438 | 0.2350 | 0.000 |
| TMHINT | -0.0269 | 0.0590 | 0.5047 | 0.774 |

This is the central scientific finding of Phase 5.1.

The repaired measurements help on known domains, but the current constrained hand-engineered mapper still does not learn a domain-invariant quality function.

## Phase 5.1 engineering result

The repaired synthetic suite produced 151 feature rows and completed without failure.

The real-speech suite used six TCD reference utterances with:

- identity MOS >= 4.4
- pure-delay absolute MOS change <= 0.2
- severity Spearman <= -0.2

Final result: no failures.

Engineering sanity and cross-domain subjective generalization are therefore explicitly separated.

## Phase 5.1 completion and export decision

Phase 5.1 is complete as an evidence, measurement, and validation milestone.

It exports a constrained rich-v2 model for reproducibility:

`phase5.1-native-repaired-2026-09-26-v1`

The export is **not promoted into the main CLI or Android MOS path** because the same Phase 5.1 evidence shows severe unseen-corpus failure.

The small MLP is also diagnostic only.

This is an intentional decision based on the evidence.

Canonical record:

- source commit `4f96463411da8f9f6aecb370e8ac69ae2c228273`
- PR `#12`
- run `36219037262`
- artifact ID `10899193034`
- artifact SHA-256 `7e1e244074520e3e9e620fc29a602b99b094c6592a4bb954407b3e98b4949426`

## Current scientific status

OpenVQ is not demonstrated to be at POLQA parity.

What has been established:

- the native analyzer is independent of POLQA and ViSQOL;
- engineering behavior is substantially better tested than in early phases;
- known evidence defects are documented and corrected;
- richer measurement features improve development performance;
- small learned models appear promising;
- current mappings still fail true unseen-corpus transfer.

The next phase should address learned representation/generalization while keeping a new subjective corpus untouched until the candidate is frozen.
