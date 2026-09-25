# Phase 4 development and holdout protocol

## Why Phase 4 exists

Frozen Phase 3 generalized well to TCD-VoIP and NISQA TEST P501 but failed on
EARS-EMO-OpenACE. On OpenACE its Pearson correlation with human MUSHRA was
0.1607, while published POLQA reached 0.7939.

That negative result is retained as part of the project record. Phase 3 does
not establish POLQA parity.

## What OpenVQ is

OpenVQ is not a wrapper around ViSQOL.

The native C++ engine independently computes alignment, bandwidth, spectral
disturbance, missing and added energy, coloration, noisiness, discontinuity,
loudness, clipping, ERB comparisons, temporal-envelope similarity,
modulation-spectrum similarity, spectral tilt, bad intervals, echo,
choppiness, and residual intrusion.

Phase 3 added two separately computed Google ViSQOL v3.3.3 scores, speech mode
and audio mode, as expert inputs to the final fusion. POLQA is never an input
to OpenVQ.

## Data roles after the Phase-3 OpenACE result

The following datasets have now been observed and are development data for
Phase 4:

- TCD-VoIP
- NISQA TEST P501
- EARS-EMO-OpenACE

The following are reserved as untouched Phase-4 holdouts:

- NISQA TEST FOR, 240 files and 60 conditions
- NISQA TEST NSC, 240 files and 60 conditions

The holdout labels must not be read before a Phase-4 candidate is frozen.

## Phase 4 v1

The first Phase-4 attempt made native OpenVQ the anchor and bounded the
influence of ViSQOL.

It was fitted only on TCD and P501 and did not use OpenACE labels.

Development results were:

- NISQA P501 Pearson 0.7337, RMSE 0.6932 MOS
- TCD test Pearson 0.9281, RMSE 0.4667 MOS
- OpenACE diagnostic Pearson 0.0931

The OpenACE result was worse than Phase 3. Phase 4 v1 is therefore rejected and
must not be frozen as a final candidate.

The v1 failure showed that simple bounded fusion does not solve the underlying
distribution shift. The native feature-to-quality relationship itself changes
substantially between the observed domains.

## Phase 4 v2

Phase 4 v2 treats all three observed datasets as development data and trains
one regularized multi-domain quality model.

### Common target scale

The model predicts normalized subjective quality q in [0,1].

- For MOS datasets, q = (MOS - 1) / 4.
- For OpenACE, q = MUSHRA / 100.
- Reported OpenVQ MOS is 1 + 4q.

The MUSHRA conversion is a scale normalization for development. It does not
claim that MUSHRA and ACR MOS are psychometrically identical.

### Features

The model uses:

- 19 native OpenVQ degradation features
- ViSQOL speech-mode quality
- ViSQOL audio-mode quality
- mean, minimum, maximum and disagreement between the two expert qualities
- squared native features
- limited interactions between each expert signal and selected native
  diagnostics

The interaction set is fixed in code before final holdout evaluation.

### Regularization and selection

Candidate ridge strengths are:

0.1, 0.3, 1, 3, 10, 30 and 100.

Five-fold grouped cross-validation is used. Groups are:

- NISQA P501 by condition
- TCD by degradation family plus condition
- OpenACE by speaker plus emotion

Each development corpus receives equal total weight during fitting.

The selected ridge strength minimizes the equal-corpus mean cross-validated
RMSE on q.

### Development gate

Before any Phase-4 final holdout is read, the v2 candidate must satisfy both:

- grouped-CV Pearson >= 0.70 on every development corpus
- equal-corpus mean grouped-CV RMSE_q <= 0.16

Passing this gate permits freezing and external evaluation. It is not itself a
claim of external generalization or POLQA parity.

## Frozen holdout rule

Once a v2 candidate passes the development gate, its complete coefficients,
feature normalization, feature order, source commit and artifact digest must
be written to a frozen model record before TEST_FOR or TEST_NSC is scored.

After that point:

- no coefficient may change
- no feature definition may change
- no ViSQOL mode may change
- no target mapping may change
- no result-dependent condition exclusion is allowed

If the holdout results are later used for development, the resulting model
requires a new model ID and another untouched subjective corpus.

## Final Phase-4 evaluation

NISQA TEST FOR and NISQA TEST NSC are evaluated independently.

Primary statistics:

- utterance-level Pearson correlation with human MOS
- utterance-level Spearman correlation
- RMSE
- MAE
- signed bias

Condition-level statistics are also reported.

The two holdouts are evidence about prediction of human subjective quality.
They are not, by themselves, a direct POLQA comparison.

## POLQA claims

OpenACE contains published per-file POLQA and is now development evidence.
Direct claims of POLQA-level performance require paired OpenVQ and lawful
POLQA scores on an evaluation set under a protocol declared before those
scores are examined.

OpenVQ does not implement ITU-T P.863 and does not claim P.863 conformance.
