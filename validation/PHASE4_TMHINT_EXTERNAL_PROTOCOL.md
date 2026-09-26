> **Phase 5.1 evidence erratum**
>
> This file is preserved as the protocol that was frozen before the historical Phase 4 TMHINT run. Phase 5.1 later established that the downloaded archive is the **original TMHINT-QI release**, not the assumed version-II test, and that observed listener quality scores are already on a **1-to-5** scale. The historical Pearson and Spearman results remain useful because the mistaken target transform was positive affine. Historical RMSE, MAE, and bias derived from that transform are not corrected absolute-error evidence. See `docs/PHASE5_1_EVIDENCE_ERRATUM.md` and `docs/PHASE5_1_RESULTS.md`.
>
> The original protocol text below is intentionally retained for reproducibility.

# Phase 4 fallback external holdout: TMHINT-QI v2 test

This protocol is frozen before OpenVQ Phase 4 is scored on the TMHINT-QI
version II test set.

## Why this fallback exists

The primary Phase 4 external protocol named NISQA TEST_FOR and NISQA TEST_NSC.
The public NISQA documentation lists TEST_NSC, but both currently published
NISQA_Corpus.zip endpoints fail to expose TEST_NSC through their ZIP directory
listings. No Phase 4 TEST_NSC score has been produced.

Rather than weaken the requirement for a second untouched external corpus,
TMHINT-QI version II test is used as an additional frozen holdout. TEST_FOR
remains a separate result.

## Frozen candidate

Model ID:

`phase4-native-poly2-constrained-2026-09-25-v3`

Source commit:

`d530382d6161d0a5dc3d019782192a047982f839`

Model blob SHA:

`29fb517098697bf8184712a828c332984d7a2eb6`

The candidate, coefficients, feature definitions, engineering constraints, and
scoring code may not be changed after any TMHINT-QI v2 test OpenVQ result is
examined.

## Dataset

TMHINT-QI version II test is an unseen-system speech-quality evaluation set.
Its public documentation describes 1,960 test utterances spanning clean,
noisy, and enhanced speech, with seen and unseen enhancement systems and an
unseen street-noise environment.

Source used by the workflow:

`urgent-challenge/urgent26_track2_sqa`, file `TMHINTQI.zip`

The archive is a mirror of the public TMHINT-QI material used by the ICASSP
2026 URGENT Track 2 data preparation pipeline.

## Full-reference subset

OpenVQ requires a reference signal.

The primary TMHINT-QI result therefore uses every non-clean test utterance for
which a clean test reference can be deterministically resolved.

Reference resolution is fixed before scoring:

1. Read `raw_data.csv`.
2. Restrict to files physically present under the archive's `test` tree.
3. Exclude rows whose method denotes clean/None or is blank.
4. Use the metadata `uttr` value as the pairing key.
5. A reference is the unique test-row WAV with the same `uttr` whose
   `method` field denotes clean/None. The clean WAV filename itself may carry
   a prefix, so literal filename equality is not required.
6. Require exactly one such clean reference row for that utterance.
7. If a test sample cannot be paired by those rules, exclude it and report the
   count. No manual label-dependent pairing is allowed.

This clarification was made after the first execution showed that clean WAV
filenames are also prefixed. That execution stopped during manifest creation
with zero paired samples and produced no OpenVQ TMHINT score.

Individual listener quality ratings for the same file are averaged before
evaluation.

## Human scale

TMHINT-QI quality ratings use a 0 to 5 scale. OpenVQ produces 1 to 5.

Before any OpenVQ result is observed, the human score is mapped by the fixed
endpoint transformation:

`human_mos = 1 + 0.8 * mean_quality_score`

This maps 0 to 1 and 5 to 5. It is not fitted to OpenVQ predictions.

## Primary candidate

Native Phase 4 only, invoked with `--phase4`.

No ViSQOL expert scores are supplied.

## Metrics

Report:

- number of paired test samples
- Pearson correlation
- Spearman correlation
- RMSE on the fixed 1 to 5 human scale
- MAE
- signed bias
- per-method metrics where sample count permits

No post-hoc regression or monotonic mapping is allowed.

## Predeclared criterion

The same Project OpenVQ external-generalization criterion used for the NISQA
external gate is applied:

- Pearson >= 0.70
- Spearman >= 0.70
- RMSE <= 0.80 MOS

This is a research criterion, not an ITU or POLQA conformance threshold.

Passing TEST_FOR and TMHINT-QI establishes cross-corpus external generalization
for the frozen candidate under these protocols. It does not by itself establish
POLQA parity or P.863 conformance.

## After unblinding

Once any TMHINT-QI v2 test OpenVQ result is observed, the test set is no longer
untouched for this model family. A later model change requires a different
untouched corpus for its final claim.
