# Validation framework

OpenVQ treats engineering correctness and subjective generalization as separate requirements.

A model can pass deterministic signal-processing tests and still fail to predict human quality on an unseen corpus. Phase 4 and Phase 5.1 demonstrated exactly that.

## Evidence classes

### Engineering evidence

Used to verify that the analyzer behaves sensibly under known transformations.

Examples:

- identity;
- pure delay;
- dropout;
- repeated dropout;
- additive noise;
- low-pass restriction;
- clipping;
- attenuation;
- clock drift;
- time scaling;
- mixed impairments.

### Development subjective evidence

Used for model selection and diagnosis.

At the end of Phase 5.1:

- TCD
- NISQA P501
- NISQA TEST_FOR
- OpenACE
- TMHINT-QI original

are all development evidence.

### Untouched external evidence

Must not influence architecture, preprocessing, hyperparameters, stopping, or calibration before the candidate is frozen.

URGENT 2026 remains untouched at the end of Phase 5.1.

## Phase 5.1 validation axes

### Grouped within-corpus transfer

Groups repeated conditions/sources so near-duplicate evidence does not leak trivially across folds.

Useful for model development, but not sufficient for a generalization claim.

### Leave-one-corpus-out transfer

One entire subjective corpus is excluded from both fitting and inner model selection.

This is the strongest development diagnostic currently in the repository.

Phase 5.1 showed severe failures on held-out OpenACE and TMHINT despite reasonable grouped within-corpus metrics.

Therefore future model selection must inspect leave-corpus-out performance rather than reporting only pooled or within-domain cross-validation.

### Processing-family transfer

Systems or impairment families are held apart to test whether a model learns actual quality structure rather than a corpus/system signature.

Phase 5.1 found uneven transfer, including weak OpenACE codec and TMHINT noisy-family results.

### Synthetic engineering suite

Tests deterministic degradation families and monotonic behavior.

The Phase 5.1 repaired suite also restores the independent pure-delay assertion that historical green runs had not actually exercised.

### Real-speech engineering suite

Uses six real TCD reference utterances and predeclared gates:

- identity MOS >= 4.4;
- absolute pure-delay MOS change <= 0.2;
- worsening-severity Spearman <= -0.2.

The canonical Phase 5.1 run passed with no failures.

## Subjective targets

Human judgments remain the target.

Different corpora may use different protocols such as MOS or MUSHRA.

Phase 5.1 normalizes targets to 0..1 for mixed-corpus fitting and labels cross-corpus error as **normalized error**, not interchangeable MOS error.

Do not call normalized MUSHRA/MOS error “MOS RMSE.”

## Required reporting

For every relevant evaluation report:

- n;
- Pearson;
- Spearman;
- RMSE/MAE on a valid shared scale or clearly labelled normalized scale;
- signed bias;
- floor fraction;
- ceiling fraction;
- processing-family results where possible;
- leave-corpus-out results for model-family decisions;
- engineering failures;
- dataset/evidence status.

## Final frozen validation

Before a future Phase 6 generalization claim:

1. choose and document the untouched corpus/subset;
2. freeze the candidate implementation and model ID;
3. freeze pairing and preprocessing rules;
4. freeze acceptance criteria;
5. score without tuning;
6. publish all failures.

Do not inspect the final holdout repeatedly while changing the model.

## Direct POLQA comparison

Human subjective scores remain the target.

POLQA is a benchmark only when lawful outputs are available for exactly the same audio pairs.

Use:

`validation/LOCKED_POLQA_PROTOCOL.md`

The existing Project OpenVQ direct-comparison rule uses paired bootstrap confidence intervals around RMSE difference and a predeclared +0.10 MOS non-inferiority margin.

Passing that project criterion would not establish ITU-T P.863 conformance.
