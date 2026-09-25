# Public POLQA and human listening benchmark

Protocol recorded before computing OpenVQ results on this dataset, 2026-09-25.

## Data and frozen comparator

Use `mcernak/EARS-EMO-OpenACE` revision
`31acd607eb4fb1d136677fab2aa6ced0af0e1194`. Include all 144 coded
utterances (six speakers, six emotions, four codecs). Anchors are outside
the primary codec cohort. Report missing published POLQA values explicitly;
all paired comparisons use the identical complete-case cohort. Keep file
and metadata hashes. Never replace missing POLQA with another metric.

The frozen candidate remains `phase3-tcd-only-2026-09-24-f099129`.
Compute both ViSQOL experts with upstream v3.3.3 and the existing resampling
pipeline. Preserve the source audio, and convert only its container/sample
representation to float32 WAV when required by the native reader. No level
normalization, alignment correction, denoising, or coefficient changes.

Human labels here are MUSHRA ratings, not ACR MOS. Report Pearson and
Spearman against the original 0 to 100 ratings. As a separate scale-sensitive
analysis, fit an increasing affine mapping for each metric using five speakers
and predict the sixth speaker, repeating for all six speakers. Report these
out-of-fold RMSE/MAE values in MUSHRA points. The same mapping procedure
applies to OpenVQ, both ViSQOL experts, and published POLQA.

Use 10,000 paired cluster-bootstrap samples of the 36 source utterances
(speaker plus emotion), retaining the four codec versions together. Report
95 percent intervals for RMSE and correlation differences. These intervals
are conditional on the observed speakers and fitted cross-validation models;
six speakers do not support a broad population claim. Also report all six
speaker-level results. Do not retrofit the original +0.10 MOS margin to this
different scale. This benchmark cannot satisfy the separate locked two-corpus
TCD/NISQA parity protocol.

## Separate development experiment

Evaluate a signal-only ridge regression codec specialist using nested
leave-one-speaker-out validation. Inputs are the 21 native/ViSQOL degradation
features already defined by `hybrid_features.py`. No codec name, speaker ID,
emotion, filename, POLQA score, or published ViSQOL value is a model input.
The labels are human MUSHRA scores. Standardization and ridge fitting occur
inside each training fold. Choose alpha from [0.1, 1, 10, 100, 1000] using
inner leave-one-speaker-out mean squared error, then predict the outer held-out
speaker exactly once. Clip predictions to the MUSHRA range only.

This experiment develops a new codec-specific model; it is not a modification
of frozen Phase 3 or a deployable MOS replacement. Its nested out-of-fold
predictions estimate within-corpus speaker generalization. A final model fit
on all six speakers requires a new independent corpus before promotion.
Retain negative results, every fold, and every selected hyperparameter.

## Provenance

Published POLQA scores are supplied by the dataset authors. The dataset card
identifies P.863 but does not specify the complete executable version,
operating-mode command, or license record. Describe them as author-published
POLQA scores, not an independently executed or certified POLQA run.

Source: https://huggingface.co/datasets/mcernak/EARS-EMO-OpenACE
Paper: Coldenhoff, Granqvist, and Cernak, OpenACE, ICASSP 2025,
doi:10.1109/ICASSP49660.2025.10889159. Dataset license: MIT.
