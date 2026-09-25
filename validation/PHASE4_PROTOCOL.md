# Phase 4 robust-fusion development protocol

## Why Phase 4 exists

Frozen Phase 3 generalized well to TCD-VoIP and NISQA TEST P501 but failed on
EARS-EMO-OpenACE. On OpenACE its Pearson correlation with human MUSHRA was
0.1607, while published POLQA reached 0.7939. The failure was not hidden or
discarded. It is the reason for Phase 4.

The principal forensic finding is that Phase 3 allowed one external expert,
Google ViSQOL speech mode, to dominate the fused score. That expert was strong
on the earlier development distribution but weak on OpenACE.

## What OpenVQ is

OpenVQ is not a wrapper around ViSQOL.

The native C++ engine independently computes alignment, bandwidth, spectral
disturbance, missing and added energy, coloration, noisiness, discontinuity,
loudness, clipping, ERB comparisons, temporal-envelope similarity,
modulation-spectrum similarity, spectral tilt, bad intervals, echo,
choppiness, and residual intrusion.

Phase 3 optionally adds two separately computed Google ViSQOL v3.3.3 scores as
expert inputs to the final fusion. The OpenACE result showed that those expert
inputs need a robustness boundary.

## Development data policy

For Phase 4, previously observed datasets are development data:

- TCD-VoIP
- NISQA TEST P501
- EARS-EMO-OpenACE

The provisional Phase-4 candidate is FIT only with the TCD and P501 feature
tables. OpenACE human ratings are not used to fit its coefficients or expert
weight. OpenACE is used only as a known-domain diagnostic after fitting.

Because P501 and TCD are now development evidence for Phase 4, they are no
longer untouched Phase-4 holdouts.

## Provisional architecture

1. Fit a native OpenVQ anchor using only native OpenVQ degradation features.
2. Constrain all native degradation weights to be non-negative.
3. Use equal total weight for the TCD and P501 development corpora.
4. Use ridge regularization 0.03 for stability.
5. Convert the two ViSQOL expert degradation features back to MOS.
6. Take the median of native MOS, ViSQOL speech MOS, and ViSQOL audio MOS.
7. Limit the expert-driven movement away from native MOS to 0.60 MOS.
8. Select only the remaining blend alpha on TCD plus P501 by equal-corpus RMSE.

This construction means a single external expert cannot control the final score.

## Untouched Phase-4 holdouts

The next final evaluation sets are:

1. NISQA TEST FOR, 240 files, 60 conditions.
2. NISQA TEST NSC, 240 files, 60 conditions.

Neither is used to choose the Phase-4 model. Once the candidate is frozen, no
coefficient or architecture change is permitted after either holdout is scored.

A later candidate that uses those results for development receives a new model
ID and requires another untouched corpus.

## POLQA claims

OpenACE contains published per-file POLQA and remains useful as development
evidence. The NISQA FOR/NSC holdouts primarily test prediction of human MOS
unless lawful paired POLQA outputs are also available.

OpenVQ never claims P.863 conformance. A statement of POLQA-level performance
requires direct paired evidence under a declared protocol.
