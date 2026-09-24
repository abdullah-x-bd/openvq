#include "openvq/advanced.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>

static openvq::AudioBuffer Signal(double sec, int sr = 48000) {
  openvq::AudioBuffer a;
  a.sample_rate = sr;
  a.samples.resize(static_cast<size_t>(sec * sr));
  for (size_t i = 0; i < a.samples.size(); ++i) {
    const double t = double(i) / sr;
    a.samples[i] = float(
        0.25 * std::sin(2 * 3.141592653589793 * 190 * t) +
        0.12 * std::sin(2 * 3.141592653589793 * 900 * t) +
        0.06 * std::sin(2 * 3.141592653589793 * 4200 * t));
  }
  return a;
}

int main() {
  openvq::AdvancedAnalyzer analyzer;
  auto ref = Signal(4);
  auto clean = analyzer.Analyze(ref, ref);
  assert(clean.mos > 4.4);
  assert(clean.advanced.multi_resolution_similarity > 0.98);

  auto bad = ref;
  std::fill(
      bad.samples.begin() + 48000,
      bad.samples.begin() + 60000,
      0.0f);
  auto result = analyzer.Analyze(ref, bad);
  assert(result.mos < clean.mos);
  assert(
      result.advanced.bad_interval_severity >
      clean.advanced.bad_interval_severity);

  openvq::AnalysisOptions calibrated;
  calibrated.calibration.final_bias = 1.0;
  calibrated.calibration.base_penalty_weight = 0.0;
  calibrated.calibration.advanced_multi_resolution_weight = 0.0;
  calibrated.calibration.advanced_temporal_weight = 0.0;
  calibrated.calibration.advanced_modulation_weight = 0.0;
  calibrated.calibration.advanced_asymmetry_weight = 0.0;
  calibrated.calibration.advanced_tilt_weight = 0.0;
  calibrated.calibration.advanced_level_weight = 0.0;
  calibrated.calibration.advanced_bad_interval_weight = 0.0;
  auto bias_only = analyzer.Analyze(ref, ref, calibrated);
  assert(std::abs(bias_only.mos - 4.0) < 1e-6);

  std::cout << "Advanced OpenVQ tests passed\n";
}
