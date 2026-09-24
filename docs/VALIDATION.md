# Validation plan

A production MOS claim requires subjective validation.

## Corpus

Use clean conversational speech from multiple speakers, languages and genders. Generate and collect degradations spanning AMR-NB, AMR-WB, EVS bandwidth modes, packet loss, burst loss, PLC, jitter-buffer artifacts, clock drift, time scaling, transcoding, noise, clipping, level changes, bandwidth restriction, codec switching and combinations of these conditions.

## Human labels

Collect ACR MOS using a P.800 or P.808 style protocol. Keep a locked test set that is never used for fitting weights or thresholds.

## Baselines

Compare against raw ViSQOL and any legally available published baseline scores. If a licensed POLQA installation is later available to the project, use it only as a benchmark. Human MOS remains the target variable.

## Acceptance metrics

Report Pearson correlation, Spearman rank correlation, RMSE, error by bandwidth class, error by codec, error by impairment class, calibration curve and worst-condition residuals. The project should not claim POLQA equivalence until the chosen acceptance thresholds are met on independent data.
