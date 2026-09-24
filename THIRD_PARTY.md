# Third-party components

OpenVQ's native implementation is independently developed and does not contain POLQA or ITU-T P.863 reference implementation code.

## ViSQOL

Google ViSQOL is an optional external input to OpenVQ and is not vendored in this repository. Users who install or distribute ViSQOL must comply with the license and notices of the upstream ViSQOL project.

OpenVQ can run without ViSQOL. When a ViSQOL score is supplied, OpenVQ can use it as an additional calibrated perceptual feature.

## POLQA

POLQA is not included, reimplemented, or required by the OpenVQ codebase. If lawfully obtained POLQA scores are available, the benchmarking tool can accept them as comparison labels. No POLQA code is required for that comparison.
