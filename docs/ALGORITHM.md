# OpenVQ algorithm

OpenVQ is independently designed. It is not an implementation of POLQA and does not use the ITU-T P.863 reference code.

## Processing path

1. Decode PCM16 or IEEE float32 WAV and downmix to mono.
2. Resample both signals to 48 kHz using a windowed sinc resampler.
3. Remove DC offset while retaining absolute gain information.
4. Build a 200 Hz amplitude envelope for coarse delay estimation.
5. Estimate global delay with normalized correlation.
6. Estimate sample-clock drift from local delay measurements across five temporal regions.
7. Track local alignment in a narrow window, but disable aggressive local alignment for likely missing-speech frames so dropouts are not hidden.
8. Run reference VAD from frame RMS relative to the active peak.
9. Compute a Hann-windowed FFT for active 20 ms frames and map it to logarithmically spaced perceptual bands from 50 Hz to 20 kHz.
10. Calculate centered spectral coloration, missing energy disturbance, added energy disturbance, frame similarity, level error and discontinuity.
11. Detect sustained dropout events and sample clipping.
12. Estimate a noise penalty from low-percentile degraded-frame energy and added disturbance.
13. Produce coloration, noisiness, discontinuity and loudness diagnostic dimensions on a 1 to 5 scale.
14. Aggregate degradation penalties with non-negative weights. This monotonic construction prevents a larger measured degradation from improving the native score.
15. Optionally fuse an independently computed ViSQOL MOS as an additional expert feature.
16. Return overall MOS, dimensions, confidence, temporal events and per-frame traces.

## Bandwidth classes

The 48 kHz front end detects NB, WB, SWB and FB from spectral energy above approximately 3.4 kHz, 7 kHz and 14 kHz. Thresholds are intentionally explicit and should be recalibrated on a labeled telecom corpus.

## Calibration

The checked-in weights are engineering bootstrap values, not a claim of subjective validation. python/calibrate.py fits non-negative degradation weights against human MOS labels. Production releases should use held-out P.800/P.808-style listening-test data and report Pearson, Spearman and RMSE with confidence intervals.

## Separation from root-cause analysis

RF, RTP, IMS, codec and mobility telemetry are intentionally excluded from the perceptual MOS input. They belong in a downstream root-cause model. This avoids a strong RF reading artificially changing a score for audibly bad speech and keeps the speech score independently testable.
