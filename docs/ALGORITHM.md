# OpenVQ algorithm

OpenVQ is independently designed. It is not an implementation of POLQA and does not use the ITU-T P.863 reference code.

## Processing path

1. Decode PCM16 or IEEE float32 WAV and downmix to mono.
2. Resample both signals to 48 kHz using the native fullband front end.
3. Remove DC offset while retaining absolute gain information.
4. Build a 200 Hz amplitude envelope for coarse delay estimation.
5. Estimate global delay with normalized correlation.
6. Estimate sample-clock drift from local delay measurements across five temporal regions.
7. Track local alignment in a narrow window, while avoiding aggressive alignment of likely missing-speech regions so genuine dropouts are not hidden.
8. Run reference VAD from frame RMS relative to the active peak.
9. Compute a Hann-windowed FFT for active 20 ms frames and map it to perceptual spectral bands.
10. Calculate coloration, missing energy disturbance, added energy disturbance, frame similarity, level error and discontinuity.
11. Detect sustained dropout events and sample clipping.
12. Estimate noisiness from the degraded noise floor and added disturbance.
13. Produce coloration, noisiness, discontinuity and loudness dimensions on a 1 to 5 scale.
14. Build a second perceptual view using 32 ERB bands with compressive loudness.
15. Compare speech at 20 ms, 80 ms and 200 ms resolutions.
16. Measure temporal-envelope similarity, modulation-spectrum similarity, asymmetric added/missing disturbance, spectral-tilt error, active-level error and worst-interval severity.
17. Combine base and advanced degradation features using non-negative calibration weights.
18. Optionally use an independently computed ViSQOL MOS as a monotonic expert penalty.
19. Return MOS, dimensions, confidence, temporal events and advanced diagnostics.

## Why two perceptual stages

The base stage is deliberately simple and interpretable. It captures direct spectral, level and discontinuity degradations. The advanced stage observes the same call through an ERB auditory representation and multiple time resolutions. It is designed to capture short packet-loss artifacts without losing longer-term timbral and temporal changes.

The final mapper is monotonic. All degradation weights are constrained to be non-negative during calibration. A larger measured degradation therefore cannot improve MOS through the calibrated linear fusion.

## Bandwidth classes

The 48 kHz front end detects NB, WB, SWB and FB from spectral energy above approximately 3.4 kHz, 7 kHz and 14 kHz. Thresholds are explicit so they can be evaluated and recalibrated on a labeled telecom corpus.

## Calibration

The checked-in weights are engineering bootstrap values, not a claim of subjective validation.

Calibration is intentionally two-stage.

First, `python/calibrate.py` fits base degradation weights against human MOS. Then the feature table is rebuilt using the fitted base calibration. Finally, `python/calibrate_advanced.py` fits the final fusion of the calibrated base score and advanced ERB, temporal, modulation, asymmetry, tilt, level and worst-interval features.

Production releases should use a locked held-out set of P.800/P.808-style listening-test data and report Pearson correlation, Spearman correlation, RMSE, bias and per-condition residuals.

## Separation from root-cause analysis

RF, RTP, IMS, codec and mobility telemetry are intentionally excluded from the perceptual MOS input. They belong in a downstream root-cause model. This prevents a strong RF reading from artificially improving the score of audibly degraded speech and keeps the speech-quality metric independently testable.
