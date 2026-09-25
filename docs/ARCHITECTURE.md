# OpenVQ architecture

## Short answer

OpenVQ is an independently implemented full-reference speech-quality engine.
It is not an implementation, clone, or wrapper of POLQA. It is also not simply
ViSQOL under another name.

## Native engine

The C++ engine compares a clean reference signal with a degraded recording and
computes its own perceptual and telecom diagnostics. Major components include:

- sample-rate normalization and bandwidth classification
- global delay and clock-drift estimation
- dropout-aware local alignment
- voice-activity handling
- FFT and 32-band ERB spectral analysis
- missing and added disturbance
- coloration and noisiness
- discontinuity and dropout events
- level mismatch and clipping
- multi-resolution 20/80/200 ms analysis
- temporal-envelope and modulation similarity
- asymmetric disturbance and spectral tilt
- bad-interval pooling
- delayed-copy echo detection
- local choppiness and PLC-like freeze detection
- residual intrusion analysis

Those components run without ViSQOL.

## Where ViSQOL enters

Google ViSQOL is a separate upstream program. It is not vendored into OpenVQ.

Phase 3 introduced a hybrid candidate that accepts two externally computed
ViSQOL v3.3.3 outputs:

- speech mode
- audio mode

The native engine turns those MOS values into two additional expert features
before final fusion. If those scores are not supplied, the native analyzer can
still run.

Therefore the relationship is:

reference + degraded audio
    -> native OpenVQ analysis
    -> optional ViSQOL expert scores
    -> fusion
    -> OpenVQ MOS + diagnostics

not:

audio -> ViSQOL -> renamed ViSQOL score.

## Why Phase 4 changes the fusion

The Phase-3 OpenACE benchmark showed a domain-generalization failure. ViSQOL
speech mode was much weaker on OpenACE than on NISQA P501/TCD, while the frozen
Phase-3 mapper had learned to trust it heavily.

Phase 4 therefore makes the native OpenVQ prediction the anchor and treats
ViSQOL modes as bounded advisers. The design goal is that one failing external
expert cannot collapse the overall metric.

## POLQA

POLQA is the ITU-T P.863 standardized model. OpenVQ does not contain POLQA
source code and does not claim P.863 conformance. POLQA scores, when lawfully
available, are benchmark values rather than inputs to OpenVQ.
