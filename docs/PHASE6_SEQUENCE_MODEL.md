# Phase 6 sequence model

## Status

The Phase 6 sequence experiment is complete.

It was started after Phase 6B showed that fair balanced summary models still failed true unseen-corpus transfer.

## Architecture family

All models remain below one million trainable parameters.

### native_temporal

Uses native local masks, alignment, coverage, and temporal evidence without the learned auditory-band encoder.

Parameters:

158,337.

### learned_bands

Uses shared reference/degraded 1-D auditory encoders and local native evidence.

Parameters:

260,961.

### hybrid

Uses the learned local sequence representation plus rich-v3 global features.

Parameters:

263,009.

## Learned local path

The learned auditory modes use:

1. shared reference/degraded encoders;
2. pairwise reference, degraded, absolute-difference, and product features;
3. local alignment and coverage evidence;
4. residual temporal convolution blocks with dilations 1, 2, and 4;
5. masked timeline pooling;
6. explicit activity, unmatched, disturbance, and confidence statistics;
7. a 64-unit regression head.

Training uses Huber loss and corpus-balanced weights.

## Evaluation protocol

Every architecture is tested by completely holding out each of the five development corpora.

The held corpus is absent from fitting and early stopping.

Three fixed seeds are averaged:

- 20260926
- 20260927
- 20260928

Selection maximizes weakest held-corpus Pearson/Spearman, then mean held-corpus correlation, then lower worst normalized RMSE.

## Result

The frozen rule selected `hybrid`.

Architecture objectives:

| Model | worst held-corpus correlation | mean held-corpus correlation | worst normalized RMSE |
| --- | ---: | ---: | ---: |
| native temporal | -0.3733 | 0.2159 | 0.3677 |
| learned bands | -0.3088 | 0.1842 | 0.3788 |
| hybrid | **-0.1392** | 0.1096 | 0.5453 |

The hybrid model improved completely held-out OpenACE to Pearson 0.3990 and Spearman 0.4390.

It did not establish robust corpus-invariant prediction. P501, TEST_FOR, TCD, and TMHINT remained weak, and individual seeds were unstable.

## Promotion result

The full-development hybrid candidate exported successfully to ONNX and passed numerical parity.

It failed independent engineering sanity and is not promoted.

See [Phase 6.1 results](PHASE6_1_RESULTS.md).
