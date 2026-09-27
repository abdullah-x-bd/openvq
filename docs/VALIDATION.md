# Validation status

OpenVQ separates engineering correctness from subjective prediction.

A model can fit human-rated development data and still violate basic quality behavior. Phase 6.1 demonstrated this directly.

## Current evidence

Development corpora used by the Phase 6 research branch:

- TCD;
- NISQA P501;
- NISQA TEST_FOR;
- OpenACE;
- TMHINT-QI original.

Total development rows:

2,463.

## Phase 6.1 result

Three compact sequence architectures were tested with every corpus held out in turn and three fixed seeds.

The frozen rule selected hybrid.

The candidate improved held-out OpenACE to Pearson 0.3990 and Spearman 0.4390, but transfer remained weak elsewhere.

A final full-development hybrid model passed PyTorch-to-ONNX parity and then failed independent engineering sanity.

The failure included low identity quality and worsening dropout/noise conditions receiving better scores.

The candidate was not promoted.

## Untouched evidence

URGENT 2026 subjective labels remain unconsumed.

A future candidate must pass engineering promotion gates before opening the external reserve.

## POLQA comparison

POLQA is a benchmark only when lawful outputs correspond to the exact same audio pairs and human targets.

OpenACE contains public per-file POLQA values and supports historical paired benchmarking. It is development evidence, not untouched Phase 6.1 proof.

No current OpenVQ result establishes P.863 conformance or general POLQA superiority.
