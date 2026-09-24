# OpenVQ

OpenVQ is a source-available, full-reference speech-quality engine for telecom and drive-test applications. It is designed as an independently derived perceptual quality system with an optional ViSQOL expert input, mobile-network-oriented diagnostics, a native C++ core, and Android bindings.

OpenVQ is not POLQA and does not claim to implement ITU-T P.863. Numerical equivalence or superiority must be established through independent listening-test validation.

## Implemented now

- 48 kHz internal fullband pipeline
- windowed-sinc sample-rate conversion
- mono WAV ingestion for PCM16 and float32 inputs
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
- pure-Python degradation generator
- monotonic human-MOS calibration tool
- Android JNI and Kotlin API
- native regression tests and GitHub Actions CI

## Native build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files:

    ./build/openvq_cli reference.wav degraded.wav

Optionally provide an independently computed ViSQOL MOS:

    ./build/openvq_cli reference.wav degraded.wav --visqol-score 4.21

## ViSQOL

Google ViSQOL is not vendored. tools/visqol_score.py uses a separately installed upstream ViSQOL package in 48 kHz audio mode and produces a score that OpenVQ can fuse as one expert input. Keeping it separate makes licensing and upgrades explicit.

## Android

The android/openvq-android library exposes:

    val json = OpenVqNative.analyzePcm16(reference, degraded, 48000)

The native library resamples other input rates internally.

## Validation

The checked-in score mapping is an engineering bootstrap model. Production MOS accuracy must be calibrated against human listening-test labels. See docs/VALIDATION.md and python/calibrate.py.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use requires a separate written commercial license from the licensor. See LICENSE and COMMERCIAL-LICENSE.md.
