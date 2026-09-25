# Locked Phase 4 v2 holdout protocol

This protocol was committed after the Phase-4 v2 model was frozen and before
NISQA TEST FOR or NISQA TEST NSC was scored by that model.

## Frozen candidate

Model ID:

`phase4-v2-multidomain-ridge-2026-09-25`

Frozen record:

`validation/frozen/phase4-v2-freeze.json`

The freeze commit predates the holdout workflow.

The candidate contains the complete feature order, normalization values,
regularized regression coefficients, target mapping and development
cross-validation record.

## Untouched holdouts

Two independent NISQA test subsets are evaluated:

1. NISQA TEST FOR, 240 utterances and 60 conditions.
2. NISQA TEST NSC, 240 utterances and 60 conditions.

Neither subset was used to choose the Phase-4 v2 architecture, features,
regularization strength, coefficients or development gate.

## Locked scoring procedure

For each holdout:

1. Extract only the named NISQA subset from the public NISQA corpus archive.
2. Resolve the original reference/degraded pairs and human MOS.
3. Recompute Google ViSQOL v3.3.3 speech mode on every pair.
4. Recompute Google ViSQOL v3.3.3 audio mode on every pair.
5. Extract the native OpenVQ feature vector.
6. Apply the frozen Phase-4 v2 JSON model without fitting.
7. Report utterance-level and condition-level statistics.

No post-hoc monotonic mapping is applied.

## Primary evidence

The human MOS is the target.

For Phase-4 v2, report:

- Pearson correlation
- Spearman correlation
- RMSE
- MAE
- signed bias
- 95 percent bootstrap intervals for Pearson, Spearman and RMSE

ViSQOL speech and audio modes are reported as contextual baselines on the same
pairs.

## Predeclared generalization gate

A holdout passes the project generalization gate only if all three conditions
are met at utterance level:

- Pearson >= 0.75
- Spearman >= 0.75
- RMSE <= 0.80 MOS

The gate is a Project OpenVQ research criterion. It is not an ITU standard and
does not establish POLQA equivalence.

The strongest Phase-4 generalization statement requires both TEST FOR and
TEST NSC to pass.

## Immutability

After either holdout is scored, no coefficient, feature definition,
normalization value, ViSQOL mode, target mapping or result-dependent exclusion
may be changed for this model ID.

Any later model that uses these holdout results for development requires a new
model ID and another untouched subjective corpus.

## POLQA

These two holdouts test prediction of human MOS. They do not contain a newly
licensed, paired POLQA run in this protocol.

Passing them would strengthen the case that OpenVQ generalizes across unseen
subjective corpora. It would not, by itself, establish POLQA parity or P.863
conformance.
