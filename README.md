# OpenVQ

OpenVQ is a source-available, full-reference speech-quality engine for telecom
and drive-test applications. It combines an independently implemented native
C++ perceptual engine with optional external expert signals and produces a
quality score plus telecom-oriented diagnostics.

**OpenVQ is not POLQA and does not implement ITU-T P.863.**

For a plain-language overview, start with
[`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md). The architecture is described
in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and the complete validation
record, including negative results, is in
[`docs/VALIDATION_HISTORY.md`](docs/VALIDATION_HISTORY.md).

## Is OpenVQ based on ViSQOL?

The native OpenVQ engine is not based on ViSQOL and can run without it. It
independently computes alignment, spectral and temporal disturbance, missing
and added energy, coloration, noisiness, discontinuity, loudness, clipping,
echo, choppiness and other perceptual diagnostics.

Phase 3 and later experimental quality models can also consume separately
computed Google ViSQOL scores as expert features. ViSQOL is not vendored into
this repository.

POLQA is never used as an OpenVQ input.

## Implemented

- 48 kHz internal fullband pipeline
- PCM16 and float32 WAV ingestion
- fullband sample-rate conversion
- NB, WB, SWB and FB bandwidth classification
- global delay and multi-region clock-drift estimation
- dropout-aware local alignment and reference voice-activity detection
- FFT and 32-band ERB perceptual analysis
- 20 ms, 80 ms and 200 ms multi-resolution analysis
- missing and added disturbance measures
- coloration, noisiness, discontinuity and loudness analysis
- clipping and dropout-event analysis
- temporal-envelope and modulation-spectrum similarity
- asymmetric disturbance and spectral-tilt analysis
- active-level error and worst-interval pooling
- delayed-copy echo, choppiness and residual-intrusion diagnostics
- JSON CLI output and per-frame traces
- human-subjective calibration and validation tooling
- optional external ViSQOL expert inputs
- Android JNI and Kotlin API
- native regression tests and GitHub Actions validation

## Native build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files:

    ./build/openvq_cli reference.wav degraded.wav

The native engine works without ViSQOL.

Experimental hybrid scoring can supply separately computed expert scores:

    ./build/openvq_cli reference.wav degraded.wav \
      --visqol-speech-score 4.10 \
      --visqol-audio-score 4.25

## Scientific status

The engineering implementation is functional, but the quality model remains
under active validation.

Frozen Phase 3 performed strongly on TCD-VoIP and NISQA TEST P501:

| Dataset | Pearson | Spearman | RMSE |
| --- | ---: | ---: | ---: |
| TCD test | 0.9541 | 0.9375 | 0.4335 |
| NISQA TEST P501 | 0.8185 | 0.8209 | 0.6011 |

The same frozen model then failed to generalize to EARS-EMO-OpenACE:

| OpenACE comparison | Pearson |
| --- | ---: |
| OpenVQ Phase 3 | 0.1607 |
| published POLQA | 0.7939 |
| published ViSQOL | 0.7034 |

Therefore **OpenVQ currently does not claim POLQA parity**.

Phase 4 is a multi-domain redesign. TCD, P501 and OpenACE are now development
data. NISQA TEST FOR and TEST NSC are reserved as fresh holdouts under
[`validation/PHASE4_PROTOCOL.md`](validation/PHASE4_PROTOCOL.md).

## Validation reproducibility

See [`docs/REPRODUCING_VALIDATION.md`](docs/REPRODUCING_VALIDATION.md) for
workflow run IDs, artifact IDs, dataset revisions and freeze rules.

## Android

The `android/openvq-android` library exposes:

    val json = OpenVqNative.analyzePcm16(reference, degraded, 48000)

The JNI layer uses the same native analyzer as the CLI.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use
requires a separate written commercial license from the licensor. See
`LICENSE` and `COMMERCIAL-LICENSE.md`.

Google ViSQOL is a separate upstream dependency with its own license and is not
vendored into OpenVQ.
