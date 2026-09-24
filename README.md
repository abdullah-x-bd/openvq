# OpenVQ

OpenVQ is a source-available, full-reference speech-quality engine for telecom and drive-test applications. It is an independently derived perceptual quality system with optional Google ViSQOL input, telecom-oriented diagnostics, a native C++ core, and Android bindings.

OpenVQ is not POLQA and does not claim to implement ITU-T P.863. Numerical equivalence or superiority must be established through independent listening-test validation.

## Implemented

- 48 kHz internal fullband pipeline
- PCM16 and float32 WAV ingestion
- fullband sample-rate conversion
- NB, WB, SWB and FB bandwidth classification
- global delay estimation
- multi-region clock-drift estimation
- dropout-aware local alignment
- reference voice-activity detection
- FFT perceptual spectral analysis
- 32-band ERB auditory analysis
- 20 ms, 80 ms and 200 ms multi-resolution quality analysis
- missing and added disturbance measures
- asymmetric disturbance weighting
- coloration analysis
- noisiness analysis
- discontinuity and dropout-event analysis
- loudness mismatch analysis
- clipping detection
- temporal-envelope similarity
- modulation-spectrum similarity
- spectral-tilt error
- active-level error
- worst-interval pooling
- monotonic MOS aggregation
- trainable base and advanced fusion weights
- optional ViSQOL expert penalty
- confidence estimate
- JSON CLI output
- per-frame quality traces
- deterministic degradation generator
- human-MOS feature extraction
- two-stage human-MOS calibration
- held-out benchmarking against human MOS, ViSQOL, and optional licensed POLQA scores
- Android JNI and Kotlin API
- native regression tests and GitHub Actions CI

## Native build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files:

    ./build/openvq_cli reference.wav degraded.wav

Use an independently computed ViSQOL score as an optional expert input:

    ./build/openvq_cli reference.wav degraded.wav --visqol-score 4.21

Use fitted human-MOS calibration:

    ./build/openvq_cli reference.wav degraded.wav --calibration openvq-final.calibration

## Human-MOS calibration

Start with a training manifest:

    reference,degraded,human_mos,visqol_mos,polqa_mos

The ViSQOL and POLQA columns are optional. POLQA values are only benchmark data when lawfully available. Human MOS is the target.

Extract the initial feature table:

    python3 python/build_training_table.py train-manifest.csv train-base.csv

Fit the base monotonic degradation model:

    python3 python/calibrate.py train-base.csv --out openvq-base.calibration

Re-extract features using that fitted base model:

    python3 python/build_training_table.py train-manifest.csv train-advanced.csv \
        --calibration openvq-base.calibration

Fit the final advanced perceptual fusion while retaining the base weights:

    python3 python/calibrate_advanced.py train-advanced.csv \
        --base-calibration openvq-base.calibration \
        --out openvq-final.calibration

Evaluate only on a separate held-out manifest:

    python3 python/benchmark.py heldout.csv \
        --calibration openvq-final.calibration

The benchmark reports RMSE, Pearson correlation, Spearman correlation, and mean bias. If the held-out manifest contains ViSQOL or licensed POLQA scores, the same metrics are reported for those baselines.

## ViSQOL

Google ViSQOL is not vendored into this repository. `tools/visqol_score.py` uses a separately installed upstream ViSQOL package in 48 kHz audio mode. The resulting MOS can be supplied to OpenVQ as one optional expert feature. This keeps the upstream dependency, attribution and upgrades explicit.

## Android

The `android/openvq-android` library exposes:

    val json = OpenVqNative.analyzePcm16(reference, degraded, 48000)

The JNI layer uses the same advanced native analyzer as the CLI.

## Scientific status

The software implementation and calibration pipeline are complete engineering components. The checked-in default weights are bootstrap values. A claim that OpenVQ matches or exceeds POLQA requires a sufficiently large independent human listening-test corpus and a locked held-out evaluation set. The repository includes the machinery needed to perform that calibration and comparison.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use requires a separate written commercial license from the licensor. See `LICENSE` and `COMMERCIAL-LICENSE.md`.
