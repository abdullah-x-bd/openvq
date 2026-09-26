# Phase 6 sequence candidate design

The sequence model is a **conditional Phase 6 path**. It should be trained only if the fair 6B summary-model experiment shows that the small rich-feature ANN still has unacceptable unseen-domain failure.

## Fixed initial architecture

Parameter budget: fewer than 1,000,000 trainable parameters.

The learned auditory modes use:

1. shared reference/degraded 1-D encoders with 32, 64, and 128 channels;
2. pairwise concatenation of reference embedding, degraded embedding, absolute difference, and elementwise product;
3. local alignment/coverage evidence from the native trace;
4. residual temporal convolution blocks with dilations 1, 2, and 4;
5. masked pooling over the complete timeline;
6. explicit activity, unmatched-duration, local-disturbance, and confidence statistics;
7. an optional rich-v3 global feature branch;
8. a 64-unit regression head.

## Ablations

- `native_temporal`: timeline masks/local native evidence only
- `learned_bands`: shared learned auditory encoder plus native local evidence
- `hybrid`: learned local evidence plus rich-v3 global features

The model is trained directly against human subjective targets using robust Huber loss.

## Evaluation

All three modes are evaluated by leave-one-corpus-out transfer.

The held corpus is not used during fitting or early stopping.

Three fixed seeds are averaged.

Model selection maximizes the weakest held-corpus Pearson/Spearman value and then mean held-corpus correlation.

This remains development evidence. URGENT 2026 is not used for model selection.
