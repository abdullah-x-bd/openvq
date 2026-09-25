# Validation history

This file records negative results as well as positive ones.

## Engineering validation

OpenVQ has deterministic regression and impairment tests covering delay,
dropouts, noise, filtering, clipping, attenuation, drift, time scaling,
sample-rate handling, mixed impairments, bounds, and fuzz cases.

## Phase 2

TCD-VoIP was used to expose under-penalized telecom failures such as echo and
choppiness. Native diagnostics were extended accordingly.

## Phase 3

Model ID: `phase3-tcd-only-2026-09-24-f099129`.

The mapper was fitted using TCD train plus development data. NISQA TEST P501
was kept external to fitting.

Observed frozen results:

| Dataset | n | Pearson | Spearman | RMSE |
| --- | ---: | ---: | ---: | ---: |
| TCD test | 60 | 0.9541 | 0.9375 | 0.4335 |
| NISQA TEST P501 | 240 | 0.8185 | 0.8209 | 0.6011 |

TCD condition-level Pearson was 0.9800 after correcting a reporting-only
condition-grouping bug.

## Phase-3 OpenACE external test

The frozen Phase-3 candidate was evaluated on EARS-EMO-OpenACE without
refitting.

| Metric against human MUSHRA | OpenVQ Phase 3 | POLQA | published ViSQOL |
| --- | ---: | ---: | ---: |
| Pearson | 0.1607 | 0.7939 | 0.7034 |
| Spearman | 0.1465 | 0.7818 | 0.6631 |

The paired OpenVQ-minus-POLQA Pearson difference on the 143 shared samples was
-0.6328. A 10,000-resample speaker-by-emotion cluster bootstrap gave a 95%
interval of approximately [-0.7965, -0.4813].

This is a clear failure of Phase-3 cross-domain generalization.

## Phase-3 forensic findings

Phase 3 correlated about 0.85 with recomputed ViSQOL speech mode on OpenACE.
That expert itself correlated only about 0.33 with human MUSHRA. ViSQOL audio
mode correlated about 0.66.

The four codec means also exposed severe score compression. Human MUSHRA
strongly separated EVS and Opus from LC3 and LC3Plus, while Phase-3 OpenVQ
means stayed in a narrow band around 3.42 to 3.54 MOS.

The result showed two separate problems:

1. Phase-3 fusion relied too heavily on one expert.
2. Native feature relationships learned on earlier domains did not transfer
   cleanly to codec-only emotional speech.

The project therefore does not claim POLQA parity.

## Phase 4 v1

The first robust-fusion attempt used native OpenVQ as an anchor and allowed
only bounded movement from the median of native, ViSQOL speech and ViSQOL
audio.

It did not use OpenACE labels for fitting.

Results:

| Dataset | Pearson | RMSE |
| --- | ---: | ---: |
| NISQA P501 | 0.7337 | 0.6932 MOS |
| TCD test | 0.9281 | 0.4667 MOS |
| OpenACE diagnostic | 0.0931 | not comparable on raw MUSHRA scale |

Phase 4 v1 did not repair the OpenACE failure and was rejected.

## Phase 4 v2

Phase 4 v2 treats TCD, P501 and OpenACE as development domains. It predicts a
common normalized subjective-quality target and uses regularized
multi-domain fitting with grouped cross-validation.

OpenACE can now influence Phase-4 development because its external Phase-3
result has already been observed. It can no longer serve as a Phase-4
holdout.

The next untouched evaluation sets remain NISQA TEST FOR and NISQA TEST NSC.

See `validation/PHASE4_PROTOCOL.md` for the frozen-data rules and exact
development gate.
