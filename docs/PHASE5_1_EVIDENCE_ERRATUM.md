# Phase 5.1A evidence erratum

Date: 2026-09-26

This document preserves the historical Phase 4 and Phase 5 v1 records and
appends corrections discovered during the Phase 5.1 audit.

## Delay engineering gate

The Phase 5 snapshot inherited literal `\\n` text inside a Python comment in
`validation/engineering_matrix.py`. As a result, the intended independent
delay-invariance `if` statement was part of the comment and did not execute.

This is a validation-code defect. It does not prove that a historical candidate
failed the delay cases. Historical green engineering runs must not be cited as
evidence that the independent delay threshold was exercised.

Phase 5.1 restores the independent condition and reruns it.

## TMHINT identity and MOS scale

The historical 1,455-row manifest was labelled
`TMHINT_QI_V2_TEST` and transformed ratings with:

`human_mos = 1 + 0.8 * mean_quality_score`

Inspection shows DDAE and KLT families in the downloaded material. Those
families identify the original TMHINT-QI material rather than the documented
version-II test composition. Observed listener ratings are already on a 1-to-5
quality scale.

Phase 5.1 therefore detects the release from the archive contents and, for the
original release, uses the listener mean directly as 1-to-5 MOS.

The historical Phase 4 TMHINT Pearson and Spearman correlations remain useful
diagnostic evidence because a positive affine label transform does not change
those correlations. Historical RMSE, MAE and bias values based on the incorrect
scale are retained only as historical outputs and must not be treated as
corrected metrics.

Phase 5 v1 also used the transformed TMHINT targets during fitting. It is
therefore preserved as a diagnostic baseline and is not the Phase 5.1 release
candidate.

## Provenance requirement

New Phase 5.1 TMHINT manifests record:

- detected release identity
- observed score range
- method counts
- archive SHA-256 when available
- raw metadata SHA-256
- manifest SHA-256
- resolved and unresolved pair counts
