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

## OpenACE external test

The frozen Phase-3 candidate was then evaluated on EARS-EMO-OpenACE without
refitting.

| Metric against human MUSHRA | OpenVQ Phase 3 | POLQA | published ViSQOL |
| --- | ---: | ---: | ---: |
| Pearson | 0.1607 | 0.7939 | 0.7034 |
| Spearman | 0.1465 | 0.7818 | 0.6631 |

The paired OpenVQ-minus-POLQA Pearson difference on the 143 shared samples was
-0.6328. A 10,000-resample speaker-by-emotion cluster bootstrap gave a 95%
interval of approximately [-0.7965, -0.4813].

This is a clear failure of Phase-3 cross-domain generalization.

## Forensic interpretation

Phase 3 correlated about 0.85 with the recomputed ViSQOL speech-mode expert on
OpenACE. That expert itself correlated only about 0.33 with human MUSHRA.
ViSQOL audio mode correlated about 0.66.

The codec means exposed severe score compression. Human MUSHRA strongly
separated EVS/Opus from LC3/LC3Plus, while Phase-3 OpenVQ means remained in a
narrow band around 3.42 to 3.54 MOS.

The project therefore does not claim POLQA parity.

## Phase 4

OpenACE is now development evidence. The Phase-4 design makes native OpenVQ the
anchor and bounds the influence of external experts.

The next untouched holdouts are NISQA TEST FOR and NISQA TEST NSC.
See `validation/PHASE4_PROTOCOL.md`.
