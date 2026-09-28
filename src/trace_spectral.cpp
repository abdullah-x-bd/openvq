#include "trace_spectral.h"

#include <algorithm>
#include <cmath>
#include <complex>
#include <stdexcept>
#include <vector>

namespace openvq {
namespace trace_internal {
namespace {
constexpr double kPi = 3.14159265358979323846;

std::size_t NextPow2(std::size_t n) {
  std::size_t p = 1;
  while (p < n) p <<= 1;
  return p;
}
}  // namespace

void FftInPlace(std::vector<std::complex<double>>* values) {
  auto& x = *values;
  const std::size_t n = x.size();
  if (n == 0 || (n & (n - 1)) != 0) {
    throw std::invalid_argument("trace FFT length must be a non-zero power of two");
  }

  for (std::size_t i = 1, j = 0; i < n; ++i) {
    std::size_t bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) std::swap(x[i], x[j]);
  }

  for (std::size_t len = 2; len <= n; len <<= 1) {
    const double angle = -2.0 * kPi / static_cast<double>(len);
    const std::complex<double> wlen(std::cos(angle), std::sin(angle));
    for (std::size_t i = 0; i < n; i += len) {
      std::complex<double> w(1.0, 0.0);
      for (std::size_t j = 0; j < len / 2; ++j) {
        const auto u = x[i + j];
        const auto v = x[i + j + len / 2] * w;
        x[i + j] = u + v;
        x[i + j + len / 2] = u - v;
        w *= wlen;
      }
    }
  }
}

std::array<double, 64> Bands(const std::vector<float>& frame,
                             int sample_rate) {
  const std::size_t nfft = NextPow2(frame.size());
  std::vector<std::complex<double>> spectrum(nfft, {0.0, 0.0});

  for (std::size_t i = 0; i < frame.size(); ++i) {
    const double window =
        0.5 - 0.5 * std::cos(2.0 * kPi * i /
                             std::max<std::size_t>(1, frame.size() - 1));
    spectrum[i] = static_cast<double>(frame[i]) * window;
  }

  FftInPlace(&spectrum);

  std::vector<double> power(nfft / 2 + 1);
  for (std::size_t i = 0; i < power.size(); ++i) {
    power[i] = std::norm(spectrum[i]) + 1e-14;
  }

  std::array<double, 64> out{};
  const double lo = 50.0;
  const double hi = std::min(20000.0, sample_rate * 0.49);
  for (int band = 0; band < 64; ++band) {
    const double t0 = static_cast<double>(band) / 64.0;
    const double t1 = static_cast<double>(band + 1) / 64.0;
    const double f0 = lo * std::pow(hi / lo, t0);
    const double f1 = lo * std::pow(hi / lo, t1);

    const std::size_t k0 = std::min<std::size_t>(
        power.size() - 1, std::floor(f0 * nfft / sample_rate));
    const std::size_t k1 = std::min<std::size_t>(
        power.size(),
        std::max<std::size_t>(k0 + 1,
                              std::ceil(f1 * nfft / sample_rate)));

    double energy = 0.0;
    for (std::size_t k = k0; k < k1; ++k) energy += power[k];
    out[band] =
        10.0 * std::log10(energy / std::max<std::size_t>(1, k1 - k0) +
                          1e-14);
  }
  return out;
}

}  // namespace trace_internal
}  // namespace openvq
