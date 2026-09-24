# Locked OpenVQ versus POLQA protocol

This protocol was frozen before any licensed POLQA scores were supplied.

## Candidate

The candidate is `phase3-tcd-only-2026-09-24-f099129`. Its exact source
artifact, coefficients and public-holdout results are recorded in
`validation/frozen/phase3-freeze.json`.

No coefficient, feature definition, ViSQOL mode, clipping rule, condition
split or MOS mapping may be changed after POLQA scores are examined.

## Locked evaluation sets

1. Untouched NISQA TEST P501, 240 utterances and 60 conditions.
2. Locked TCD-VoIP test split, 60 utterances.

Human MOS is the reference target. OpenVQ, ViSQOL and licensed POLQA must
score the exact same reference/degraded pairs.

## Primary comparison

The primary statistic is utterance-level RMSE to human MOS. Secondary
statistics are Pearson, Spearman, MAE and signed bias, with condition-level
statistics reported separately.

The predeclared practical non-inferiority margin is +0.10 MOS RMSE. For each
locked set, paired bootstrap resamples estimate

`delta_RMSE = RMSE(OpenVQ, human) - RMSE(POLQA, human)`.

OpenVQ passes the criterion only when the upper bound of the two-sided 95
percent paired-bootstrap confidence interval is below +0.10 MOS. This margin
is a Project OpenVQ protocol choice, not an ITU conformance threshold.

A parity claim requires passing this criterion on both locked sets.
Correlation alone is not sufficient.

## POLQA

POLQA must come from a lawful licensed implementation. Record product version,
P.863 mode, bandwidth configuration and command/configuration. OpenVQ does
not implement P.863 and this protocol does not establish P.863 conformance.

## No post-hoc fitting

NISQA P501 and all POLQA outputs are evaluation-only for this frozen candidate.
Any later model tuned using them requires a new model ID and a new untouched
subjective corpus.
