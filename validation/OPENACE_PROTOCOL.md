# Frozen EARS-EMO-OpenACE external comparison protocol

This protocol is frozen before OpenVQ is scored on EARS-EMO-OpenACE.

## Candidate

The candidate is `phase3-tcd-only-2026-09-24-f099129`.

Its coefficients are embedded in the native OpenVQ Phase-3 implementation and
recorded in `validation/frozen/phase3-freeze.json`. No coefficient, feature
definition, ViSQOL mode, clipping rule, or MOS mapping may be changed after
OpenACE results are examined.

## Dataset

Use `mcernak/EARS-EMO-OpenACE` from Hugging Face. The workflow resolves the
dataset repository revision before downloading any audio and writes that exact
revision to the result artifact.

Only the four coded conditions with objective scores are evaluated:

- EVS
- LC3
- LC3Plus
- Opus

The MUSHRA anchors are excluded from the objective comparison.

The expected evaluation set is 144 coded samples from 6 speakers, 6 emotions,
and 4 codecs. Published POLQA is expected on 143 of those samples.

## OpenVQ scoring

For every reference/degraded pair:

1. Recompute Google ViSQOL v3.3.3 in speech mode.
2. Recompute Google ViSQOL v3.3.3 in audio mode.
3. Pass both scores to the frozen OpenVQ Phase-3 candidate.
4. Record the resulting OpenVQ MOS without any refitting.

The published OpenACE ViSQOL score remains a separate benchmark column and is
not substituted for either frozen Phase-3 expert input.

## Human target

The subjective target is the published distorted MUSHRA rating on its native
0 to 100 scale.

Because MUSHRA and MOS-LQO use different numerical scales, the primary OpenACE
comparison is association with human judgments rather than raw cross-scale
RMSE.

Primary statistic:

- Pearson correlation with distorted MUSHRA.

Secondary statistics:

- Spearman correlation with distorted MUSHRA.
- Per-codec Pearson and Spearman.
- Per-emotion Pearson and Spearman.
- Paired differences between OpenVQ and POLQA correlations.

Confidence intervals use a paired cluster bootstrap over the 36
speaker-by-emotion source items, preserving the codec observations belonging
to each source item within each bootstrap draw.

## POLQA

Use the POLQA scores already published in EARS-EMO-OpenACE. These are external
benchmark data. OpenVQ does not implement ITU-T P.863 and this comparison does
not establish P.863 conformance.

## Interpretation

OpenACE is an independent external cross-check because it was not used to fit
the frozen candidate. It is not by itself the repository's formal POLQA parity
gate because its human target is MUSHRA rather than the MOS target used by the
locked NISQA/TCD protocol.

The formal parity gate remains `validation/LOCKED_POLQA_PROTOCOL.md`.

## No post-hoc fitting

OpenACE audio, human ratings, published ViSQOL, and published POLQA are
evaluation-only for this frozen candidate. Any later model tuned using OpenACE
requires a new model ID and another untouched subjective corpus.
