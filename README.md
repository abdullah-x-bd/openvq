# OpenVQ

OpenVQ is an open, full-reference speech-quality engine for telecom and drive-test applications.

It is designed to provide a reproducible alternative quality pipeline built around open algorithms, with optional ViSQOL integration for benchmarking and feature fusion. OpenVQ does **not** claim to implement or reproduce ITU-T P.863/POLQA. Its scores must be validated against human listening tests before any equivalence claim is made.

## Goals

- 48 kHz fullband processing
- NB, WB, SWB and FB bandwidth detection
- global and local delay alignment
- sample-clock drift estimation
- dropout-aware piecewise alignment
- perceptual spectral and temporal disturbance features
- coloration, noisiness, discontinuity and loudness dimensions
- clipping and dropout event detection
- optional ViSQOL score ingestion
- monotonic MOS mapping
- per-window quality traces
- native C++ core
- Android JNI/Kotlin API
- CLI tooling
- Python calibration and dataset tooling
- deterministic unit tests and CI

## Status

Initial engineering implementation is under active development.

## License

Apache License 2.0.
