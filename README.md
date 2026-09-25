# OpenVQ

OpenVQ is a source-available, full-reference speech-quality engine for telecom and drive-test applications. It is an independently derived perceptual quality system with a native C++ core, telecom-oriented diagnostics, Android bindings, and optional external expert inputs such as Google ViSQOL.

OpenVQ is not POLQA and does not claim to implement ITU-T P.863. Numerical equivalence or superiority must be established through independent listening-test validation.

## Is OpenVQ based on ViSQOL?

No. The native OpenVQ analyzer does not call ViSQOL and does not reimplement ViSQOL.

OpenVQ independently computes its own reference/degraded alignment, bandwidth detection, clock drift, perceptual spectral disturbance, ERB-band similarity, temporal-envelope similarity, modulation similarity, missing and added disturbance, coloration, noisiness, discontinuity, loudness mismatch, clipping, bad-section severity, echo, choppiness, and residual-intrusion diagnostics.

ViSQOL entered the project later as an optional external expert:

- Phase 1 and Phase 2 developed the native OpenVQ signal analysis and telecom diagnostics.
- Phase 3 added two separately computed Google ViSQOL v3.3.3 outputs, speech mode and audio mode, as expert features in a learned monotonic fusion.
- The frozen Phase 3 model therefore depends partly on ViSQOL, but OpenVQ as a system is not a ViSQOL wrapper.
- OpenACE external validation showed that the Phase 3 fusion trusted the speech-mode expert too strongly outside its development distribution. Phase 4 is redesigning this expert fusion around reliability gating while retaining the native OpenVQ analyzer as the anchor.

See `docs/ARCHITECTURE.md`, `docs/VALIDATION_HISTORY.md`, and `docs/PHASE4_ROBUST_FUSION.md`.

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
- echo detection
- choppiness detection
- residual-intrusion analysis
- monotonic MOS aggregation
- trainable base and advanced fusion weights
- optional external ViSQOL expert inputs
- confidence estimate
- JSON CLI output
- per-frame quality traces
- deterministic degradation generator
- human-MOS feature extraction
- held-out benchmarking against human MOS, ViSQOL, and optional lawful POLQA scores
- Android JNI and Kotlin API
- native regression tests and GitHub Actions CI

## Native build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files with native OpenVQ:

    ./build/openvq_cli reference.wav degraded.wav

Run the native-first Phase 4 candidate with no external expert:

    ./build/openvq_cli reference.wav degraded.wav --phase4

Run Phase 4 with optional independently computed ViSQOL experts:

    ./build/openvq_cli reference.wav degraded.wav --phase4 \
        --visqol-speech-score 4.10 \
        --visqol-audio-score 4.25

Phase 4 remains native-first. When both experts are supplied they can influence only the capped robust consensus term.

For reproducibility, the frozen Phase 3 hybrid remains available when ViSQOL speech and audio scores are supplied without `--phase4`.

## Human-MOS calibration

Start with a training manifest:

    reference,degraded,human_mos,visqol_mos,polqa_mos

The ViSQOL and POLQA columns are optional. POLQA values are benchmark data only when lawfully available. Human MOS is the target.

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

## ViSQOL

Google ViSQOL is not vendored into this repository. Validation workflows build a pinned upstream Google ViSQOL release separately. Its scores are optional external evidence and are kept distinct from the native OpenVQ implementation.

The OpenACE result is an important warning against treating one ViSQOL mode as universally reliable. Phase 4 therefore treats external experts as fallible signals rather than as the definition of quality.

## Android

The `android/openvq-android` library exposes:

    val json = OpenVqNative.analyzePcm16(reference, degraded, 48000)

The JNI layer uses the same native analyzer as the CLI.

## Scientific status

The engineering implementation is mature enough for reproducible benchmarking, but the scientific validation is still in progress.

Frozen Phase 3 achieved strong results on its TCD and NISQA evaluations, then failed to generalize on the independent EARS-EMO-OpenACE codec benchmark. That failure is retained as part of the validation record rather than hidden or tuned away.

As of Phase 4 development:

- OpenVQ is not demonstrated to be at POLQA parity.
- The frozen Phase 3 model should not be described as a general replacement for POLQA.
- OpenACE is now development evidence and cannot serve as untouched validation for Phase 4.
- A new untouched subjective corpus is required before a Phase 4 generalization or POLQA-parity claim.

See `validation/LOCKED_POLQA_PROTOCOL.md` for the predeclared POLQA comparison criterion and `docs/VALIDATION_HISTORY.md` for the chronological evidence.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use requires a separate written commercial license from the licensor. See `LICENSE` and `COMMERCIAL-LICENSE.md`.
