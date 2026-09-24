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

  // A coherent delayed copy should register as echo, unlike clean speech.
  auto echo = ref;
  const size_t echo_delay = 48000 * 120 / 1000;
  for (size_t i = echo_delay; i < echo.samples.size(); ++i) {
    echo.samples[i] = std::max(-0.99f, std::min(
        0.99f, echo.samples[i] + 0.32f * ref.samples[i - echo_delay]));
  }
  auto echo_result = analyzer.Analyze(ref, echo);
  assert(echo_result.advanced.echo_score > clean.advanced.echo_score + 0.02);
  assert(echo_result.mos < clean.mos);

  // Repeated short holes should register as choppiness.
  auto choppy = ref;
  for (size_t start = 48000 / 2; start + 960 < choppy.samples.size();
       start += 48000 / 5) {
    std::fill(choppy.samples.begin() + start,
              choppy.samples.begin() + start + 960, 0.0f);
  }
  auto choppy_result = analyzer.Analyze(ref, choppy);
  assert(choppy_result.advanced.choppiness_score >
         clean.advanced.choppiness_score + 0.01);
  assert(choppy_result.mos < clean.mos);

  // Repeat-last-frame PLC should also be treated as choppiness even when
  // there are no zero-valued holes.
  auto frozen = ref;
  const size_t frame20 = 48000 * 20 / 1000;
  for (size_t start = 48000; start + frame20 < frozen.samples.size();
       start += 48000 / 4) {
    std::copy(frozen.samples.begin() + start - frame20,
              frozen.samples.begin() + start,
              frozen.samples.begin() + start);
  }
  auto frozen_result = analyzer.Analyze(ref, frozen);
  assert(frozen_result.advanced.choppiness_score >
         clean.advanced.choppiness_score + 0.005);
  assert(frozen_result.mos < clean.mos);

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
  calibrated.calibration.advanced_echo_weight = 0.0;
  calibrated.calibration.advanced_choppiness_weight = 0.0;
  calibrated.calibration.advanced_residual_intrusion_weight = 0.0;
  auto bias_only = analyzer.Analyze(ref, ref, calibrated);
  assert(std::abs(bias_only.mos - 4.0) < 1e-6);

  std::cout << "Advanced OpenVQ tests passed\n";
}
