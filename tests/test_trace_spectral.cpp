#include "trace_spectral.h"
#include "test_support.h"

#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <numeric>
#include <vector>

namespace {
constexpr double kPi = 3.14159265358979323846;

std::vector<std::complex<double>> DirectDft(
    const std::vector<std::complex<double>>& x) {
  const std::size_t n = x.size();
  std::vector<std::complex<double>> out(n, {0.0, 0.0});
  for (std::size_t k = 0; k < n; ++k) {
    for (std::size_t j = 0; j < n; ++j) {
      const double angle = -2.0 * kPi * static_cast<double>(k * j) /
                           static_cast<double>(n);
      out[k] += x[j] * std::complex<double>(std::cos(angle), std::sin(angle));
    }
  }
  return out;
}

double RelativeL2(const std::vector<std::complex<double>>& actual,
                  const std::vector<std::complex<double>>& expected) {
  double num = 0.0;
  double den = 0.0;
  for (std::size_t i = 0; i < actual.size(); ++i) {
    num += std::norm(actual[i] - expected[i]);
    den += std::norm(expected[i]);
  }
  return std::sqrt(num / std::max(den, 1e-30));
}

void CheckOracle(std::size_t n) {
  std::vector<std::complex<double>> x(n);
  for (std::size_t i = 0; i < n; ++i) {
    const double t = static_cast<double>(i) / static_cast<double>(n);
    x[i] = 0.3 + std::sin(2.0 * kPi * 3.0 * t) +
           0.2 * std::cos(2.0 * kPi * t);
  }
  const auto expected = DirectDft(x);
  auto actual = x;
  openvq::trace_internal::FftInPlace(&actual);
  OPENVQ_REQUIRE(RelativeL2(actual, expected) < 1e-10);
}

int ExpectedBand(double frequency, int sample_rate) {
  const double lo = 50.0;
  const double hi = std::min(20000.0, sample_rate * 0.49);
  return static_cast<int>(std::floor(
      64.0 * std::log(frequency / lo) / std::log(hi / lo)));
}

std::vector<float> Tone(double frequency, double amplitude, int sample_rate) {
  const std::size_t n = static_cast<std::size_t>(0.020 * sample_rate);
  std::vector<float> x(n);
  for (std::size_t i = 0; i < n; ++i) {
    x[i] = static_cast<float>(
        amplitude * std::sin(2.0 * kPi * frequency * i / sample_rate));
  }
  return x;
}

int PeakBand(const std::array<double,64>& bands) {
  return static_cast<int>(
      std::distance(bands.begin(), std::max_element(bands.begin(), bands.end())));
}

}  // namespace

int main() {
  // Exact FFT-versus-DFT oracle checks at the lengths used by the audit and
  // by the 20 ms / 48 kHz trace path (960 samples -> 1024-point FFT).
  CheckOracle(8);
  CheckOracle(16);
  CheckOracle(1024);

  // Impulse has a flat complex spectrum.
  std::vector<std::complex<double>> impulse(16, {0.0, 0.0});
  impulse[0] = 1.0;
  openvq::trace_internal::FftInPlace(&impulse);
  for (const auto& v : impulse) {
    OPENVQ_REQUIRE(std::abs(v - std::complex<double>(1.0, 0.0)) < 1e-12);
  }

  // Constant input has only a DC component.
  std::vector<std::complex<double>> constant(16, {1.0, 0.0});
  openvq::trace_internal::FftInPlace(&constant);
  OPENVQ_REQUIRE(std::abs(constant[0] - std::complex<double>(16.0, 0.0)) <
                 1e-12);
  for (std::size_t i = 1; i < constant.size(); ++i) {
    OPENVQ_REQUIRE(std::abs(constant[i]) < 1e-12);
  }

  // Parseval fixture on deterministic complex input.
  std::vector<std::complex<double>> p(1024);
  for (std::size_t i = 0; i < p.size(); ++i) {
    p[i] = std::complex<double>(
        0.3 * std::sin(0.017 * i) + 0.1 * std::cos(0.071 * i),
        0.2 * std::sin(0.031 * i));
  }
  double time_energy = 0.0;
  for (const auto& v : p) time_energy += std::norm(v);
  openvq::trace_internal::FftInPlace(&p);
  double freq_energy = 0.0;
  for (const auto& v : p) freq_energy += std::norm(v);
  freq_energy /= static_cast<double>(p.size());
  OPENVQ_REQUIRE(std::abs(freq_energy - time_energy) /
                     std::max(time_energy, 1e-30) <
                 1e-10);

  // Auditory-band frequency fixtures.
  constexpr int sr = 48000;
  for (double f : {250.0, 1000.0, 4000.0, 12000.0}) {
    const auto bands = openvq::trace_internal::Bands(Tone(f, 0.5, sr), sr);
    OPENVQ_REQUIRE(std::abs(PeakBand(bands) - ExpectedBand(f, sr)) <= 1);
  }

  // Halving tone amplitude should reduce the dominant band by about 6.02 dB.
  const auto hi = openvq::trace_internal::Bands(Tone(1000.0, 0.5, sr), sr);
  const auto lo = openvq::trace_internal::Bands(Tone(1000.0, 0.25, sr), sr);
  const int b = PeakBand(hi);
  const double delta = hi[b] - lo[b];
  OPENVQ_REQUIRE(delta > 5.9 && delta < 6.15);

  return 0;
}
