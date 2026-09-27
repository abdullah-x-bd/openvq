#pragma once

#include <array>
#include <complex>
#include <vector>

namespace openvq {
namespace trace_internal {

// Trace-only spectral primitives. These are intentionally separate from the
// frozen Phase 6A frontend so trace corrections do not alter native analyzer
// semantics or its frozen source hashes.
void FftInPlace(std::vector<std::complex<double>>* values);
std::array<double, 64> Bands(const std::vector<float>& frame, int sample_rate);

}  // namespace trace_internal
}  // namespace openvq
