# OpenVQ architecture

## Purpose

OpenVQ is a full-reference speech-quality engine intended for telecom, network-testing, and drive-test applications. It compares a known reference utterance with a degraded recording and produces a quality estimate plus diagnostics.

It is an independently derived system. It does not implement POLQA or ITU-T P.863.

## Signal path

At a high level:

```
reference WAV --------------------------+
                                         |
                                         v
                                  native OpenVQ
                                         |
degraded WAV ---------------------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
               alignment and                         perceptual and
               timing analysis                       telecom diagnostics
                     |                                       |
                     +-------------------+-------------------+
                                         |
                                  native feature set
                                         |
                       optional external expert scores
                                         |
                                         v
                                   quality fusion
                                         |
                            MOS estimate + diagnostics
```

## Native OpenVQ analysis

The native analyzer is implemented in C++ and performs its own processing.

### Input and timing

- WAV loading
- sample-rate normalization
- global delay estimation
- local alignment
- multi-region clock-drift estimation
- reference voice-activity detection

### Spectral and perceptual analysis

- FFT spectral comparison
- ERB-band auditory representation
- multi-resolution analysis at 20, 80, and 200 ms
- missing disturbance
- added disturbance
- asymmetric disturbance
- spectral coloration
- spectral tilt
- loudness and active-level mismatch

### Temporal and telecom analysis

- temporal-envelope similarity
- modulation-spectrum similarity
- dropout and bad-section analysis
- clipping
- echo
- choppiness and short speech holes
- repeated-waveform or PLC-like freeze behavior
- unexplained residual intrusion

These signals exist independently of ViSQOL.

## ViSQOL relationship

ViSQOL is an optional external expert, not the OpenVQ core.

Phase 3 used two Google ViSQOL v3.3.3 scores:

- speech mode
- audio mode

Both are computed outside OpenVQ and then supplied as expert values to the frozen Phase 3 fusion.

The Phase 3 experiment demonstrated why this distinction matters. On TCD and NISQA, speech-mode ViSQOL was a useful expert. On EARS-EMO-OpenACE, speech-mode ViSQOL generalized poorly while audio-mode ViSQOL generalized much better. Because the frozen Phase 3 mapper gave speech mode a large influence, the combined OpenVQ score also generalized poorly.

Phase 4 therefore changes the fusion philosophy from fixed expert trust to reliability-gated expert use.

## POLQA relationship

POLQA is used only as a benchmark when lawful scores are available.

OpenVQ:

- does not contain POLQA source code
- does not implement P.863
- does not claim P.863 conformance
- does not require POLQA at runtime

A direct OpenVQ versus POLQA comparison should score the same audio pairs and compare both predictions against the same human subjective target.

## Runtime modes

### Native mode

Reference and degraded audio are analyzed without ViSQOL expert inputs.

### Frozen Phase 3 hybrid mode

When both ViSQOL speech and audio scores are supplied, the frozen Phase 3 mapper can combine them with native OpenVQ features.

This mode is preserved for reproducibility but is not considered generally validated after the OpenACE result.

### Phase 4

Phase 4 is under development. Its design goal is to make the native OpenVQ evidence the anchor and treat external experts as fallible, reliability-weighted evidence.
