# OpenVQ

OpenVQ is a source-available, full-reference speech-quality engine for telecom and drive-test applications. It is designed as an independently derived perceptual quality system with an optional ViSQOL expert input, mobile-network-oriented diagnostics, a native C++ core, and Android bindings.

OpenVQ is not POLQA and does not claim to implement ITU-T P.863. Numerical equivalence or superiority must be established through independent listening-test validation.

## Implemented now

- 48 kHz internal fullband pipeline
- windowed-sinc sample-rate conversion
- PCM16 and float32 WAV ingestion
- NB, WB, SWB and FB spectral bandwidth classification
- global delay estimation
- multi-region sample-clock-drift estimation
- dropout-aware local frame alignment
- reference voice-activity detection
- FFT and logarithmic perceptual-band analysis
- missing and added spectral disturbance measures
- coloration analysis
- noisiness estimate
- discontinuity analysis and dropout event extraction
- loudness mismatch analysis
- clipping detection
- bad-section weighting
- monotonic MOS aggregation
- confidence estimate
- optional ViSQOL score fusion
- JSON CLI output
- per-frame quality trace in the C++ API
- deterministic degradation generator
- human-MOS feature extraction
- monotonic calibration training
- held-out benchmarking against human MOS, ViSQOL, and optional POLQA columns
- externally loadable calibration files
- Android JNI and Kotlin API
- native regression tests and GitHub Actions CI

## Native build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files:

    ./build/openvq_cli reference.wav degraded.wav

Use ViSQOL as an optional expert:

    ./build/openvq_cli reference.wav degraded.wav --visqol-score 4.21

Use fitted human-MOS calibration:

    ./build/openvq_cli reference.wav degraded.wav --calibration openvq.calibration

## Calibration loop

Start with a labeled manifest:

    reference,degraded,human_mos,visqol_mos,polqa_mos

Extract native OpenVQ degradation features:

    python3 python/build_training_table.py manifest.csv training.csv

Fit non-negative monotonic weights:

    python3 python/calibrate.py training.csv --out openvq.calibration

Evaluate on a separate held-out manifest:

    python3 python/benchmark.py heldout.csv --calibration openvq.calibration

The benchmark reports RMSE, Pearson correlation, Spearman correlation, and mean bias. When the manifest contains ViSQOL or licensed POLQA values, it reports the same metrics for those baselines.

## ViSQOL

Google ViSQOL is not vendored. tools/visqol_score.py uses a separately installed upstream ViSQOL package in 48 kHz audio mode and produces a score that OpenVQ can fuse as one expert input.

## Android

The android/openvq-android library exposes:

    val json = OpenVqNative.analyzePcm16(reference, degraded, 48000)

The native library resamples other input rates internally.

## Validation

The checked-in score mapping is an engineering bootstrap model. Production MOS accuracy must be calibrated against human listening-test labels. See docs/VALIDATION.md.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use requires a separate written commercial license from the licensor. See LICENSE and COMMERCIAL-LICENSE.md.
