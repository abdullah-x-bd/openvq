#include "openvq/advanced.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
#include <vector>

static openvq::AudioBuffer Signal(double sec, int sr = 48000) {
  openvq::AudioBuffer a;
  a.sample_rate = sr;
  a.samples.resize(static_cast<size_t>(sec * sr));
  for (size_t i = 0; i < a.samples.size(); ++i) {
    const double t = double(i) / sr;
    const double local = std::fmod(t, 1.0);
    const double gate = local < 0.78 ? 1.0 : 0.0;
    const double env = gate * (0.45 + 0.55 * std::pow(
        std::max(0.0, std::sin(2 * 3.141592653589793 * 2.7 * t)), 0.6));
    a.samples[i] = float(env * (
        0.25 * std::sin(2 * 3.141592653589793 * 190 * t) +
        0.12 * std::sin(2 * 3.141592653589793 * 900 * t) +
        0.06 * std::sin(2 * 3.141592653589793 * 4200 * t)));
  }
  return a;
}

int main() {
  openvq::AdvancedAnalyzer analyzer;
  auto ref = Signal(5);
  auto clean = analyzer.Analyze(ref, ref);

  assert(clean.mos > 4.4);
  assert(clean.advanced.multi_resolution_similarity > 0.98);
  assert(clean.advanced.echo_likelihood < 0.10);
  assert(clean.advanced.residual_energy < 0.02);
  assert(clean.advanced.clipping_plateau < 0.05);

  auto dropped = ref;
  std::fill(
      dropped.samples.begin() + 48000,
      dropped.samples.begin() + 60000,
      0.0f);
  auto drop_result = analyzer.Analyze(ref, dropped);
  assert(drop_result.mos < clean.mos);
  assert(
      drop_result.advanced.bad_interval_severity >
      clean.advanced.bad_interval_severity);

  // A delayed copy should be specifically recognized as echo, not merely as
  // generic added energy.
  auto echoed = ref;
  const size_t echo_delay = static_cast<size_t>(0.120 * ref.sample_rate);
  for (size_t i = echo_delay; i < echoed.samples.size(); ++i) {
    echoed.samples[i] = std::clamp(
        echoed.samples[i] + 0.42f * ref.samples[i - echo_delay],
        -1.0f, 1.0f);
  }
  auto echo_result = analyzer.Analyze(ref, echoed);
  assert(echo_result.advanced.echo_likelihood >
         clean.advanced.echo_likelihood + 0.15);
  assert(echo_result.advanced.residual_energy >
         clean.advanced.residual_energy + 0.10);

  // Clipping detection must survive normalization to an arbitrary peak rather
  // than only looking for samples at +/-1.
  auto clipped = ref;
  for (float& v : clipped.samples) {
    v = std::clamp(v, -0.10f, 0.10f);
  }
  auto clip_result = analyzer.Analyze(ref, clipped);
  assert(clip_result.advanced.clipping_plateau >
         clean.advanced.clipping_plateau + 0.05);

  // Insert a 180 ms repeated segment and truncate the tail. This is the kind
  // of local time edit that a global-delay estimator must not align away.
  auto edited = ref;
  const size_t insert_at = static_cast<size_t>(1.6 * ref.sample_rate);
  const size_t edit_n = static_cast<size_t>(0.180 * ref.sample_rate);
  std::vector<float> temp;
  temp.reserve(edited.samples.size() + edit_n);
  temp.insert(temp.end(), edited.samples.begin(), edited.samples.begin() + insert_at);
  temp.insert(
      temp.end(),
      edited.samples.begin() + insert_at - edit_n,
      edited.samples.begin() + insert_at);
  temp.insert(temp.end(), edited.samples.begin() + insert_at, edited.samples.end());
  temp.resize(edited.samples.size());
  edited.samples = std::move(temp);
  auto edit_result = analyzer.Analyze(ref, edited);
  assert(edit_result.advanced.temporal_edit >
         clean.advanced.temporal_edit + 0.03);

  // Add deterministic background noise. Silence regions in the reference make
  // the inactive-noise feature observable.
  auto noisy = ref;
  std::mt19937 rng(7);
  std::normal_distribution<float> normal(0.0f, 0.025f);
  for (float& v : noisy.samples) {
    v = std::clamp(v + normal(rng), -1.0f, 1.0f);
  }
  auto noise_result = analyzer.Analyze(ref, noisy);
  assert(noise_result.advanced.inactive_noise >
         clean.advanced.inactive_noise + 0.10);
  assert(noise_result.advanced.residual_energy >
         clean.advanced.residual_energy + 0.05);

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
  calibrated.calibration.advanced_residual_weight = 0.0;
  calibrated.calibration.advanced_temporal_edit_weight = 0.0;
  calibrated.calibration.advanced_clip_plateau_weight = 0.0;
  calibrated.calibration.advanced_inactive_noise_weight = 0.0;
  auto bias_only = analyzer.Analyze(ref, ref, calibrated);
  assert(std::abs(bias_only.mos - 4.0) < 1e-6);

  std::cout << "Advanced OpenVQ tests passed\n";
}
